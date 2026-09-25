#include <Arduino.h>
#include <BLEDevice.h>
#include <BLEServer.h>
#include <esp_pm.h>
#include <driver/ledc.h>

#define SERVICE_UUID        "c9239c9e-6fc9-4168-b3aa-53105eb990b0"
#define CHARACTERISTIC_UUID "458d4dc9-349f-401d-b092-a2b1c55f5319"
// Rev 3: SW_SYS (battery on battery power, BQ25185 SYS voltage on USB) in mV, uint16 LE, read + notify.
#define BATTERY_UUID        "cda71ce6-4af9-4aa2-8d34-329c2acdae09"
#define VBAT_PERIOD 10000
// Battery Level (0x2A19) percent from the cell voltage, linear between these two points.
#define VBAT_EMPTY_MV 3500
#define VBAT_FULL_MV  4200

#ifndef FW_VERSION
#define FW_VERSION "dev"
#endif

#define DELAY 2000
#define COUNTDOWN_DURATION 10000  // 10 seconds in milliseconds
// Idle status LED: dim steady while a phone is connected, a slow soft pulse while
// advertising. PWM via LEDC so the pulse can dim.
#define PULSE_PERIOD 4000
#define PULSE_MAX 120   // of 255; the LED is current-starved already, keep it soft
#define CONNECTED_LEVEL 25  // dim steady when connected, so trigger/bulb (255) still show

// Radio timing, the main battery-life lever with light sleep on. Advertising interval
// in 0.625 ms units: kept fast, since a slower one (100-200 ms was tried) makes the phone
// take seconds longer to find the device; connection interval in 1.25 ms units with a
// slave latency, so the chip may skip that many connection events when idle. A
// command from the phone is seen at the next event the chip listens to, so the worst
// added trigger delay is (CONN_LATENCY + 1) * CONN_MAX_INTERVAL * 1.25 ms. Latency
// is 0 until a bench measurement shows what skipping events saves against that delay.
#define ADV_MIN_INTERVAL 0x0030  // 30 ms
#define ADV_MAX_INTERVAL 0x0060  // 60 ms
#define CONN_MIN_INTERVAL 0x18   // 30 ms
#define CONN_MAX_INTERVAL 0x28   // 50 ms
#define CONN_LATENCY 0
#define CONN_TIMEOUT 400         // 4 s, in 10 ms units

// VERBOSE comes from platformio.ini: 0 in the production env (every Serial call
// compiles to a no-op), 1 in the debug env, where Serial is USB CDC.
#ifndef VERBOSE
#define VERBOSE 0
#endif
#if !VERBOSE
  struct NullStream {
      template<typename T> NullStream& operator<<(T const&) { return *this; }
      void print(...) {}
      void println(...) {}
      void setTxTimeoutMs(...) {}
      void begin(...) {}
  };
static NullStream nullSerial;
#undef Serial // the core defines it as a macro when CDC is off
#define Serial nullSerial
#endif

constexpr int ledPin = 20; // GPIO20 (U0RXD)
uint8_t ledLevel = 0; // 0 = off, 255 = full

// LEDC straight from ESP-IDF, since Arduino's ledcAttach() cannot ask for KEEP_ALIVE and
// the PWM would stop whenever the chip light-sleeps. RC_FAST is the only LEDC clock on the
// C3 that runs through light sleep (APB stops).
void setupLed() {
    ledc_timer_config_t timer = {
        .speed_mode = LEDC_LOW_SPEED_MODE,
        .duty_resolution = LEDC_TIMER_8_BIT,
        .timer_num = LEDC_TIMER_0,
        .freq_hz = 5000,
        .clk_cfg = LEDC_USE_RC_FAST_CLK,
    };
    ESP_ERROR_CHECK(ledc_timer_config(&timer));
    ledc_channel_config_t channel = {
        .gpio_num = ledPin,
        .speed_mode = LEDC_LOW_SPEED_MODE,
        .channel = LEDC_CHANNEL_0,
        .timer_sel = LEDC_TIMER_0,
        .duty = 0,
        .sleep_mode = LEDC_SLEEP_MODE_KEEP_ALIVE,
        // D4's anode is on VCC and its cathode reaches GPIO20 through R20, so the LED is
        // active-low. Clear this if a board is wired the other way round.
        .flags = {.output_invert = 1},
    };
    ESP_ERROR_CHECK(ledc_channel_config(&channel));
}

void ledWrite(uint8_t level) {
    ledLevel = level;
    ledc_set_duty(LEDC_LOW_SPEED_MODE, LEDC_CHANNEL_0, level);
    ledc_update_duty(LEDC_LOW_SPEED_MODE, LEDC_CHANNEL_0);
}
// S2_PIN comes from platformio.ini: GPIO3 on rev 1/2 (default), GPIO6 in the rev3 envs.
#ifndef S2_PIN
#define S2_PIN 3
#endif
constexpr int shutterPinS2 = S2_PIN; // drives U6 (camera S2)
// S1_PIN comes from platformio.ini: GPIO4 on rev 2 (default), GPIO21 (U0TXD) in the rev1 env.
#ifndef S1_PIN
#define S1_PIN 4
#endif
constexpr int shutterPinS1 = S1_PIN; // drives U5 (camera S1)

// Commands arrive on the BLE task (onWrite) and are executed in loop(), so the BLE
// stack is never blocked by the shutter delays. The queue is the only shared state
// between the two tasks besides the connection flags below.
struct Command {
    uint8_t button;   // 1 trigger, 2 bulb, 3 countdown
    uint8_t value;    // 1 press/start, 0 release/cancel
    uint32_t durationMs;
};
QueueHandle_t commandQueue;

int incoming;
unsigned long timestampButton;
unsigned long countdownStartTime;
unsigned long countdownDuration = COUNTDOWN_DURATION;
bool countdownActive = false;
bool bulbModeActive = false;
unsigned long lastCountdownPrint = 0;

BLEServer *pServer = nullptr;
volatile bool deviceConnected = false;
volatile bool advertiseRequested = false;

// Tickless idle forces PM_SLP_DISABLE_GPIO on, which releases every pin in light sleep.
// A released S1/S2 pin reads as off through R21/R22, fine while closed but it would end
// a bulb exposure, so the chip stays out of light sleep while the shutter is open.
esp_pm_lock_handle_t shutterAwake;
bool shutterOpen = false;

void openShutter() {
    if (!shutterOpen) esp_pm_lock_acquire(shutterAwake);
    shutterOpen = true;
    Serial.println("Setting shutterPins HIGH...");
    digitalWrite(shutterPinS1, HIGH);
    delay(10); // Allow S1's PhotoMOS to turn on before requesting release.
    digitalWrite(shutterPinS2, HIGH);
}

void closeShutter() {
    Serial.println("Setting shutterPins LOW...");
    digitalWrite(shutterPinS2, LOW);
    digitalWrite(shutterPinS1, LOW);
    if (shutterOpen) esp_pm_lock_release(shutterAwake);
    shutterOpen = false;
}

void endBulbMode() {
    Serial.println("Ending bulb mode - shutter closing");
    bulbModeActive = false;
    closeShutter();
}

void triggerShutter() {
    Serial.println("Trigger shutter");
    endBulbMode();
    openShutter();
    delay(100);
    closeShutter();
}

void startBulbMode() {
    Serial.println("Starting bulb mode - shutter opening");
    bulbModeActive = true;
    openShutter();
}

void startCountdown(unsigned long durationMs) {
    endBulbMode();
    // Clear stale button-1 state so the trigger timeout in loop()
    // doesn't fight the countdown blink over the LED pin
    incoming = 0;
    countdownDuration = durationMs;
    countdownStartTime = millis();
    lastCountdownPrint = 0;
    countdownActive = true;
    ledWrite(255);
    Serial.print("Starting ");
    Serial.print(durationMs / 1000);
    Serial.println("-second countdown...");
}

void cancelCountdown() {
    countdownActive = false;
    countdownStartTime = 0;
    ledWrite(0);
    Serial.println("Countdown cancelled");
}

void handleCommand(const Command &c, unsigned long now) {
    switch (c.button) {
        case 1:
            if (c.value == 1) {
                // A pending countdown would keep blinking the LED and
                // fire the shutter a second time, so cancel it first
                cancelCountdown();
                incoming = 11;
                ledWrite(255);
                timestampButton = now;
                triggerShutter();
            } else {
                incoming = 10;
                ledWrite(0);
            }
            break;
        case 2:
            if (c.value == 1) {
                // A pending countdown would end the bulb exposure when
                // it expires, so cancel it first
                cancelCountdown();
                ledWrite(255);
                startBulbMode();
            } else {
                ledWrite(0);
                endBulbMode();
            }
            break;
        case 3:
            if (c.value == 1) startCountdown(c.durationMs);
            else cancelCountdown();
            break;
        default:
            Serial.println("Unknown button triggered");
    }
}

class BleServerCallback : public BLEServerCallbacks {
    void onConnect(BLEServer *pServer, ble_gap_conn_desc *desc) override {
        Serial.println("*** BLE CLIENT CONNECTED ***");
        deviceConnected = true;
        pServer->requestConnParams(desc->conn_handle, CONN_MIN_INTERVAL,
                                  CONN_MAX_INTERVAL, CONN_LATENCY, CONN_TIMEOUT);
    }

    void onDisconnect(BLEServer *pServer, ble_gap_conn_desc *desc) override {
        Serial.println("*** BLE CLIENT DISCONNECTED ***");
        deviceConnected = false;
        advertiseRequested = true; // restarted from loop(), off the BLE task
    }
};

class BLECharacteristicCallback : public BLECharacteristicCallbacks {
    void onWrite(BLECharacteristic *pCharacteristic) override {
        String data = pCharacteristic->getValue();
        Command c = {};

        if (data.length() == 1) {
            // Legacy single-byte protocol: button * 10 + state
            uint8_t v = data[0];
            c.button = v / 10;
            c.value = v % 10;
            c.durationMs = COUNTDOWN_DURATION;
            Serial.print("BLE command received (legacy): ");
            Serial.println(v);
        } else if (data.length() == 3) {
            // Multi-byte protocol: [command, duration s, action]
            c.button = data[0];
            c.durationMs = (uint8_t)data[1] * 1000U;
            c.value = data[2];
            Serial.print("BLE command received (multi-byte): [");
            Serial.print(c.button);
            Serial.print(", ");
            Serial.print(c.durationMs / 1000);
            Serial.print(", ");
            Serial.print(c.value);
            Serial.println("]");
            if (c.button != 3) {
                Serial.println("Unknown multi-byte command");
                return;
            }
        } else {
            Serial.print("Invalid command length: ");
            Serial.println(data.length());
            return;
        }
        xQueueSend(commandQueue, &c, 0);
    }
};

#ifdef VBAT_ADC_PIN
BLECharacteristic *pBattery = nullptr;
BLECharacteristic *pBatteryLevel = nullptr;
unsigned long lastVbat = 0;

// 1 MΩ / 1 MΩ divider on SW_SYS into an ADC1 pin; the 100 nF at the pin makes the 500 kΩ source fine.
uint16_t readVbatMillivolts() {
    uint32_t sum = 0;
    for (int i = 0; i < 8; i++) sum += analogReadMilliVolts(VBAT_ADC_PIN);
    return sum / 8 * 2;
}

void updateVbat(unsigned long t) {
    if (lastVbat && t - lastVbat < VBAT_PERIOD) return;
    lastVbat = t;
    uint16_t mv = readVbatMillivolts();
    uint8_t percent = constrain((int)(mv - VBAT_EMPTY_MV) * 100 / (VBAT_FULL_MV - VBAT_EMPTY_MV), 0, 100);
    pBattery->setValue((uint8_t *)&mv, 2);
    pBatteryLevel->setValue(&percent, 1);
    if (deviceConnected) {
        pBattery->notify();
        pBatteryLevel->notify();
    }
    Serial.print("SW_SYS mV: ");
    Serial.println(mv);
}
#endif

void setupBLE() {
    Serial.println("Initializing BLE...");

    BLEDevice::init("OpenRZ67");
    pServer = BLEDevice::createServer();
    pServer->setCallbacks(new BleServerCallback());

    BLEService *pService = pServer->createService(SERVICE_UUID);

    BLECharacteristic *pCharacteristic = pService->createCharacteristic(
            CHARACTERISTIC_UUID,
            BLECharacteristic::PROPERTY_READ |
            BLECharacteristic::PROPERTY_WRITE_NR
    );
    pCharacteristic->setCallbacks(new BLECharacteristicCallback());
#ifdef VBAT_ADC_PIN
    pBattery = pService->createCharacteristic(
            BATTERY_UUID,
            BLECharacteristic::PROPERTY_READ |
            BLECharacteristic::PROPERTY_NOTIFY
    );
#endif
    pService->start();

    // Device Information Service (0x180A), so any BLE tool can read the firmware version.
    BLEService *pDis = pServer->createService(BLEUUID((uint16_t)0x180A));
    pDis->createCharacteristic(BLEUUID((uint16_t)0x2A29), BLECharacteristic::PROPERTY_READ)->setValue("OpenRZ67");
    pDis->createCharacteristic(BLEUUID((uint16_t)0x2A24), BLECharacteristic::PROPERTY_READ)->setValue("Trigger");
    pDis->createCharacteristic(BLEUUID((uint16_t)0x2A26), BLECharacteristic::PROPERTY_READ)->setValue(FW_VERSION);
    pDis->start();

#ifdef VBAT_ADC_PIN
    // Battery Service (0x180F): Battery Level in percent, the standard form phones show.
    BLEService *pBas = pServer->createService(BLEUUID((uint16_t)0x180F));
    pBatteryLevel = pBas->createCharacteristic(
            BLEUUID((uint16_t)0x2A19),
            BLECharacteristic::PROPERTY_READ |
            BLECharacteristic::PROPERTY_NOTIFY
    );
    pBas->start();
#endif
    Serial.println("BLE services configured");

    BLEAdvertising *pAdvertising = BLEDevice::getAdvertising();
    pAdvertising->addServiceUUID(SERVICE_UUID);
    pAdvertising->setScanResponse(true);
    pAdvertising->setMinPreferred(CONN_MIN_INTERVAL);
    pAdvertising->setMaxPreferred(CONN_MAX_INTERVAL);
    pAdvertising->setMinInterval(ADV_MIN_INTERVAL);
    pAdvertising->setMaxInterval(ADV_MAX_INTERVAL);

    BLEAdvertisementData adData;
    adData.setName("OpenRZ67");
    adData.setCompleteServices(BLEUUID(SERVICE_UUID));
    pAdvertising->setAdvertisementData(adData);

    BLEAdvertisementData scanResponseData;
    scanResponseData.setName("OpenRZ67");
    scanResponseData.setCompleteServices(BLEUUID(SERVICE_UUID));
    pAdvertising->setScanResponseData(scanResponseData);

    // 0 dBm on advertising and connections (the default is +3 dBm)
    BLEDevice::setPower(ESP_PWR_LVL_N0, ESP_BLE_PWR_TYPE_ADV);
    BLEDevice::setPower(ESP_PWR_LVL_N0, ESP_BLE_PWR_TYPE_DEFAULT);

    pAdvertising->start();
    Serial.println("*** BLE ADVERTISING STARTED - Device visible as 'OpenRZ67' ***");
}

// Runs only when nothing else owns the LED (trigger hold, bulb, countdown).
void idleLed(unsigned long t) {
    if (deviceConnected) {
        ledWrite(CONNECTED_LEVEL);
        return;
    }
    // triangle 0..1..0 over PULSE_PERIOD, squared so the fade looks even
    float x = (t % PULSE_PERIOD) / (float)PULSE_PERIOD * 2;
    if (x > 1) x = 2 - x;
    ledWrite((uint8_t)(PULSE_MAX * x * x));
}

void configurePowerManagement() {
    esp_pm_config_t pm_config = {
        // USB Serial/JTAG drops off the bus in light sleep and is untested under DFS, so
        // the debug build (CDC on) stays awake at a fixed 80 MHz; production sleeps.
        .max_freq_mhz = 80,
        .min_freq_mhz = ARDUINO_USB_CDC_ON_BOOT ? 80 : 10,
        .light_sleep_enable = !ARDUINO_USB_CDC_ON_BOOT
    };
    // Needs CONFIG_PM_ENABLE (custom_sdkconfig in platformio.ini); without it this returns
    // ESP_ERR_NOT_SUPPORTED and the clock stays at F_CPU.
    esp_err_t err = esp_pm_configure(&pm_config);
    if (err == ESP_OK) {
        Serial.println("Power management: " + String(pm_config.min_freq_mhz) + "-80 MHz, light sleep "
                       + String(pm_config.light_sleep_enable ? "on" : "off"));
    } else {
        Serial.println("Power management not available in this framework build ("
                       + String(esp_err_to_name(err)) + ")");
    }
}

void setup() {
#if ARDUINO_USB_CDC_ON_BOOT
    Serial.setTxTimeoutMs(0); // Don't block when no serial monitor connected
#endif
    Serial.begin(115200);
    delay(500);  // Brief delay for serial stability

    commandQueue = xQueueCreate(4, sizeof(Command));
    ESP_ERROR_CHECK(esp_pm_lock_create(ESP_PM_NO_LIGHT_SLEEP, 0, "shutter", &shutterAwake));
    setupBLE();

    Serial.println("=== OPENRZ67 TRIGGER " FW_VERSION " ===");
    Serial.print("Free Heap: ");
    Serial.println(ESP.getFreeHeap());

    setupLed();
    pinMode(shutterPinS1, OUTPUT);
    pinMode(shutterPinS2, OUTPUT);

    configurePowerManagement();
    Serial.println("=== SETUP COMPLETE - SYSTEM READY ===");
}

void loop() {
    unsigned long now = millis();

    if (advertiseRequested) {
        advertiseRequested = false;
        pServer->startAdvertising();
        Serial.println("*** RESTARTED ADVERTISING ***");
    }

    Command c;
    while (xQueueReceive(commandQueue, &c, 0) == pdTRUE) handleCommand(c, now);

    if (incoming == 11 && ledLevel > 0 && now - timestampButton >= DELAY) {
        // Shutter has fired, disable LED
        ledWrite(0);
        Serial.println("Button 1 timeout reached");
    }

    // Countdown runs regardless of connection status
    if (countdownActive) {
        unsigned long elapsed = now - countdownStartTime;

        if (now - lastCountdownPrint >= 1000) {
            Serial.print("Countdown: ");
            Serial.print((countdownDuration - elapsed) / 1000);
            Serial.println(" seconds remaining");
            lastCountdownPrint = now;
        }

        if (elapsed >= countdownDuration) {
            countdownActive = false;
            countdownStartTime = 0;
            triggerShutter();
            ledWrite(0);
            Serial.println("Countdown complete - shutter triggered!");
        } else {
            ledWrite(elapsed % 250 < 125 ? 255 : 0); // fast blink
        }
    }

    if (bulbModeActive) {
        ledWrite(255);
    }

    // Idle: steady = phone connected, soft pulse = on and waiting
    bool triggerHold = incoming == 11 && now - timestampButton < DELAY;
    if (!countdownActive && !bulbModeActive && !triggerHold) {
        idleLed(now);
    }
#ifdef VBAT_ADC_PIN
    updateVbat(now);
#endif

    delay(10);
}
