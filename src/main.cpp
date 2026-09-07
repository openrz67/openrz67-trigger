#include <Arduino.h>
#include <BLEDevice.h>
#include <BLEServer.h>
#include <esp_pm.h>

#define SERVICE_UUID        "c9239c9e-6fc9-4168-b3aa-53105eb990b0"
#define CHARACTERISTIC_UUID "458d4dc9-349f-401d-b092-a2b1c55f5319"

#define DELAY 2000
#define BLINK_SPEED 500
#define COUNTDOWN_DURATION 10000  // 10 seconds in milliseconds

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
#define Serial nullSerial
#endif

constexpr int ledPin = 20; // GPIO20 (U0RXD)
// D4's anode is on VCC and its cathode reaches GPIO20 through R20, so the LED is
// active-low: driving the pin LOW lights it. Flip these two if a board is wired the
// other way round.
constexpr int LED_ON = LOW;
constexpr int LED_OFF = HIGH;
constexpr int shutterPinS2 = 3; // GPIO3, drives U6 (camera S2)
constexpr int shutterPinS1 = 4; // GPIO4, drives U5 (camera S1); rev 1 used GPIO21 (U0TXD)

int incoming;
unsigned long now;
unsigned long timestampButton;
unsigned long countdownStartTime;
unsigned long countdownDuration = COUNTDOWN_DURATION; // Default to 10 seconds
bool countdownActive = false;
bool bulbModeActive = false;
unsigned long lastCountdownPrint = 0;

BLEServer *pServer = nullptr;
bool deviceConnected = false;
bool oldDeviceConnected = false;

void endBulbMode();
void startCountdown(unsigned long durationMs);
void cancelCountdown();

void openShutter() {
    Serial.println("Setting shutterPins HIGH...");
    digitalWrite(shutterPinS1, HIGH);
    delay(10); // Allow S1's PhotoMOS to turn on before requesting release.
    digitalWrite(shutterPinS2, HIGH);
}

void closeShutter() {
    Serial.println("Setting shutterPins LOW...");
    digitalWrite(shutterPinS2, LOW);
    digitalWrite(shutterPinS1, LOW);
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

void endBulbMode() {
    Serial.println("Ending bulb mode - shutter closing");
    bulbModeActive = false;
    closeShutter();
}


void startCountdown(unsigned long durationMs) {
    endBulbMode();
    // Clear stale button-1 state so the trigger timeout in loop()
    // doesn't fight the countdown blink over the LED pin
    incoming = 0;
    countdownActive = false;
    countdownDuration = durationMs;
    countdownStartTime = millis();
    lastCountdownPrint = 0;
    countdownActive = true;
    digitalWrite(ledPin, LED_ON);
    Serial.print("Starting ");
    Serial.print(durationMs / 1000);
    Serial.println("-second countdown...");
}

void cancelCountdown() {
    countdownActive = false;
    countdownStartTime = 0;
    digitalWrite(ledPin, LED_OFF);
    Serial.println("Countdown cancelled");
}

class BleServerCallback : public BLEServerCallbacks {
    void onConnect(BLEServer *pServer) override {
        Serial.println("*** BLE CLIENT CONNECTED ***");
        deviceConnected = true;
    };

    void onDisconnect(BLEServer *pServer) override {
        Serial.println("*** BLE CLIENT DISCONNECTED ***");
        deviceConnected = false;

        // Immediately restart advertising for new connections
        delay(100); // Minimal delay for cleanup
        pServer->startAdvertising();
        Serial.println("*** RESTARTED ADVERTISING ***");
    };

};

class BLECharacteristicCallback : public BLECharacteristicCallbacks {
    void onWrite(BLECharacteristic *pCharacteristic) override {
        now = millis();
        std::string data = pCharacteristic->getValue();
        
        if (data.length() == 1) {
            // Legacy single-byte protocol
            incoming = data[0];
            Serial.print("BLE command received (legacy): ");
            Serial.println(incoming);

            int button = incoming / 10;
            int value = incoming % 10;

            switch (button) {
                case 1:
                    Serial.print("Button 1, value = ");
                    Serial.println(value);
                    if (value == 1) {
                        // Button 1 PRESS - trigger shutter
                        // A pending countdown would keep blinking the LED and
                        // fire the shutter a second time, so cancel it first
                        cancelCountdown();
                        digitalWrite(ledPin, LED_ON);
                        timestampButton = now;
                        triggerShutter();
                    } else {
                        // Button 1 RELEASE - just turn off LED, don't trigger again
                        digitalWrite(ledPin, LED_OFF);
                    }
                    break;
                case 2:
                    Serial.print("Button 2 (Bulb Mode), value = ");
                    Serial.println(value);
                    if (value == 1) {
                        // Start bulb mode
                        // A pending countdown would end the bulb exposure when
                        // it expires, so cancel it first
                        cancelCountdown();
                        digitalWrite(ledPin, LED_ON);
                        startBulbMode();
                    } else {
                        // End bulb mode
                        digitalWrite(ledPin, LED_OFF);
                        endBulbMode();
                    }
                    break;
                case 3:
                    Serial.print("Button 3 (Legacy Countdown), value = ");
                    Serial.println(value);
                    if (value == 1) {
                        // Start countdown with default duration
                        startCountdown(COUNTDOWN_DURATION);
                    } else {
                        // Cancel countdown
                        cancelCountdown();
                    }
                    break;
                default:
                    Serial.println("Unknown button triggered");
            }
        } else if (data.length() == 3) {
            // New multi-byte protocol
            uint8_t command = data[0];
            uint8_t duration = data[1];
            uint8_t action = data[2];
            
            Serial.print("BLE command received (multi-byte): [");
            Serial.print(command);
            Serial.print(", ");
            Serial.print(duration);
            Serial.print(", ");
            Serial.print(action);
            Serial.println("]");
            
            if (command == 3) { // Countdown command
                if (action == 1) {
                    // Start countdown with specified duration
                    startCountdown(duration * 1000UL); // Convert seconds to milliseconds
                } else {
                    // Cancel countdown
                    cancelCountdown();
                }
            } else {
                Serial.println("Unknown multi-byte command");
            }
        } else {
            Serial.print("Invalid command length: ");
            Serial.println(data.length());
        }
    }
};

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
    pCharacteristic->setValue("Hello from OpenRZ67!");

    pService->start();
    Serial.println("BLE service and characteristic configured");

    BLEAdvertising *pAdvertising = BLEDevice::getAdvertising();
    pAdvertising->addServiceUUID(SERVICE_UUID);
    pAdvertising->setScanResponse(true);
    pAdvertising->setMinPreferred(0);
    pAdvertising->setMaxPreferred(0);

    // Additional advertising configuration for better discoverability
    BLEAdvertisementData adData;
    adData.setName("OpenRZ67");
    adData.setCompleteServices(BLEUUID(SERVICE_UUID));
    pAdvertising->setAdvertisementData(adData);

    BLEAdvertisementData scanResponseData;
    scanResponseData.setName("OpenRZ67");
    scanResponseData.setCompleteServices(BLEUUID(SERVICE_UUID));
    pAdvertising->setScanResponseData(scanResponseData);

    Serial.println("BLE advertising configured");

    // Set advertising power (most important for battery life)
    esp_err_t adv_power = esp_ble_tx_power_set(ESP_BLE_PWR_TYPE_ADV, ESP_PWR_LVL_N0);  // 0dBm
    Serial.print("Set advertising power to 0dBm: ");
    Serial.println(adv_power == ESP_OK ? "SUCCESS" : "FAILED");

    // Set default power for other operations
    esp_err_t default_power = esp_ble_tx_power_set(ESP_BLE_PWR_TYPE_DEFAULT, ESP_PWR_LVL_N0);  // 0dBm
    Serial.print("Set default power to 0dBm: ");
    Serial.println(default_power == ESP_OK ? "SUCCESS" : "FAILED");

    // Start advertising
    pAdvertising->start();
    Serial.println("*** BLE ADVERTISING STARTED - Device visible as 'OpenRZ67' ***");
}

void checkToReconnect() //added
{
    if (deviceConnected && !oldDeviceConnected) {
        Serial.println("Reconnected");
        oldDeviceConnected = deviceConnected;
    }
    if (!deviceConnected && oldDeviceConnected) {
        Serial.println("Connection state updated: disconnected");
        oldDeviceConnected = deviceConnected;
    }
}

void configurePowerManagement() {
    esp_pm_config_esp32c3_t pm_config = {
        .max_freq_mhz = 80,
        .min_freq_mhz = 10,
        // USB Serial/JTAG drops off the bus when the C3 enters light sleep, so the
        // debug build (CDC on) keeps the chip awake; production may sleep.
        .light_sleep_enable = !ARDUINO_USB_CDC_ON_BOOT
    };
    // The Arduino 2.0.17 framework ships its ESP-IDF libraries with CONFIG_PM_ENABLE
    // unset, so this returns ESP_ERR_NOT_SUPPORTED and neither DFS nor automatic light
    // sleep is active: the chip runs at the 80 MHz set by the framework and idles in
    // the BLE stack's own sleep. Kept so a framework with PM enabled picks it up.
    esp_err_t err = esp_pm_configure(&pm_config);
    if (err == ESP_OK) {
        Serial.println("Power management: DFS 10-80 MHz, light sleep "
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

    setupBLE();

    Serial.println("=== OPENRZ67 TRIGGER STARTING ===");
    Serial.print("ESP32 Chip Model: ");
    Serial.println(ESP.getChipModel());
    Serial.print("ESP32 Chip Revision: ");
    Serial.println(ESP.getChipRevision());
    Serial.print("Flash Size: ");
    Serial.print(ESP.getFlashChipSize() / (1024 * 1024));
    Serial.println(" MB");
    Serial.print("Free Heap: ");
    Serial.print(ESP.getFreeHeap());
    Serial.println(" bytes");

    Serial.println("Configuring GPIO pins...");
    pinMode(ledPin, OUTPUT);
    digitalWrite(ledPin, LED_OFF);
    pinMode(shutterPinS1, OUTPUT);
    pinMode(shutterPinS2, OUTPUT);
    Serial.print("LED pin configured: GPIO");
    Serial.println(ledPin);
    Serial.print("Shutter pin configured: GPIO");
    Serial.println(shutterPinS2);
    Serial.print("Shutter pin configured: GPIO");
    Serial.println(shutterPinS1);

    // Configure power management for frequency scaling
    configurePowerManagement();

    Serial.println("=== SETUP COMPLETE - SYSTEM READY ===");
    Serial.println("Hello from Open RZ67 Trigger!");
}


void loop() {

    checkToReconnect();

    if (deviceConnected) {
        now = millis(); // Store current time

        if (incoming == 11 and digitalRead(ledPin) == LED_ON and now > timestampButton + DELAY) {
            // Shutter has fired, disable LED
            digitalWrite(ledPin, LED_OFF);
            Serial.println("Button 1 timeout reached");
        }
    }

    // Handle Arduino countdown - runs regardless of connection status
    if (countdownActive && countdownStartTime > 0) {
        unsigned long currentTime = millis();
        unsigned long elapsed = currentTime - countdownStartTime;

        // Print countdown status only once per second to avoid spam
        if (currentTime - lastCountdownPrint >= 1000) {
            unsigned long secondsRemaining = (countdownDuration - elapsed) / 1000;
            Serial.print("Countdown: ");
            Serial.print(secondsRemaining);
            Serial.println(" seconds remaining");
            lastCountdownPrint = currentTime;
        }

        if (elapsed >= countdownDuration) {
            // Countdown complete - trigger shutter
            countdownActive = false;
            countdownStartTime = 0;
            triggerShutter();
            digitalWrite(ledPin, LED_OFF);
            Serial.println("Countdown complete - shutter triggered!");
        } else {
            // Blink LED during countdown (faster blink than button 2)
            if (elapsed % 250 < 125) {  // 250ms cycle, on for first 125ms
                digitalWrite(ledPin, LED_ON);
            } else {
                digitalWrite(ledPin, LED_OFF);
            }
        }
    }

    // Handle bulb mode LED indication - steady light when active
    if (bulbModeActive) {
        digitalWrite(ledPin, LED_ON);
    }

    delay(10);

}
