/* OpenRZ67 trigger, nRF52840 / coin cell. Zephyr (nRF Connect SDK).
 *
 * Same GATT and command protocol as the ESP32-C3 firmware in ../../src/main.cpp, so the
 * Android and iOS apps do not change:
 *   service  c9239c9e-6fc9-4168-b3aa-53105eb990b0
 *   command  458d4dc9-349f-401d-b092-a2b1c55f5319  write-without-response
 *            1 byte:  button * 10 + state        (1 trigger, 2 bulb, 3 countdown; 1 start, 0 stop)
 *            3 bytes: [3, seconds, state]        countdown with its duration
 *   battery  cda71ce6-4af9-4aa2-8d34-329c2acdae09  cell voltage, mV, uint16 LE, read + notify
 *   plus Device Information (0x180A) and Battery Service (0x180F).
 *
 * Power: boot (button press) -> advertise ADV_TIMEOUT -> no connection: System OFF, the
 * button wakes it. Connected: no timeout. Disconnect -> advertise ADV_TIMEOUT again.
 */
#include <zephyr/kernel.h>
#include <zephyr/sys/poweroff.h>
#include <zephyr/drivers/gpio.h>
#include <zephyr/drivers/adc.h>
#include <zephyr/drivers/watchdog.h>
#include <zephyr/sys/byteorder.h>
#include <zephyr/bluetooth/bluetooth.h>
#include <zephyr/bluetooth/conn.h>
#include <zephyr/bluetooth/gatt.h>
#include <zephyr/bluetooth/services/bas.h>
#include <zephyr/logging/log.h>

LOG_MODULE_REGISTER(openrz67, LOG_LEVEL_INF);

#define ADV_TIMEOUT      K_MINUTES(5)
#define VBAT_PERIOD      K_SECONDS(60)
#define VBAT_EMPTY_MV    2500   /* CR2032: 0 % */
#define VBAT_FULL_MV     3000   /* 100 % */
#define TRIGGER_HOLD_MS  100    /* S2 held for a plain release */
#define S1_LEAD_MS       10     /* S1 before S2, lets the camera wake its meter */
#define DEFAULT_COUNTDOWN_MS 10000
#define LED_HOLD_MS      2000   /* LED on after a trigger */
#define LONG_PRESS       K_SECONDS(3)   /* button held this long: power off */
#define WDT_TIMEOUT_MS   5000   /* the main loop wakes at least every 2 s */

/* --- Pins (devicetree, see boards/openrz67/openrz67_nrf/openrz67_nrf.dts) ---------- */
static const struct gpio_dt_spec led = GPIO_DT_SPEC_GET(DT_ALIAS(led0), gpios);
static const struct gpio_dt_spec s1 = GPIO_DT_SPEC_GET(DT_NODELABEL(s1_drv), gpios);
static const struct gpio_dt_spec s2 = GPIO_DT_SPEC_GET(DT_NODELABEL(s2_drv), gpios);
static const struct gpio_dt_spec button = GPIO_DT_SPEC_GET(DT_ALIAS(sw0), gpios);
static const struct adc_dt_spec vdd_adc = ADC_DT_SPEC_GET_BY_IDX(DT_PATH(zephyr_user), 0);
static const struct device *const wdt = DEVICE_DT_GET(DT_NODELABEL(wdt0));

/* --- GATT ------------------------------------------------------------------------- */
#define UUID_SERVICE BT_UUID_128_ENCODE(0xc9239c9e, 0x6fc9, 0x4168, 0xb3aa, 0x53105eb990b0)
#define UUID_COMMAND BT_UUID_128_ENCODE(0x458d4dc9, 0x349f, 0x401d, 0xb092, 0xa2b1c55f5319)
#define UUID_BATTERY BT_UUID_128_ENCODE(0xcda71ce6, 0x4af9, 0x4aa2, 0x8d34, 0x329c2acdae09)

static const struct bt_uuid_128 uuid_service = BT_UUID_INIT_128(UUID_SERVICE);
static const struct bt_uuid_128 uuid_command = BT_UUID_INIT_128(UUID_COMMAND);
static const struct bt_uuid_128 uuid_battery = BT_UUID_INIT_128(UUID_BATTERY);

struct command {
	uint8_t button;      /* 1 trigger, 2 bulb, 3 countdown */
	uint8_t value;       /* 1 start, 0 stop */
	uint32_t duration_ms;
};
K_MSGQ_DEFINE(commands, sizeof(struct command), 8, 4);

static uint16_t vbat_mv;
static bool vbat_notify;

static ssize_t write_command(struct bt_conn *conn, const struct bt_gatt_attr *attr,
			     const void *buf, uint16_t len, uint16_t offset, uint8_t flags)
{
	const uint8_t *d = buf;
	struct command c = {.duration_ms = DEFAULT_COUNTDOWN_MS};

	if (len == 1) {
		c.button = d[0] / 10;
		c.value = d[0] % 10;
	} else if (len == 3 && d[0] == 3) {
		c.button = 3;
		c.duration_ms = d[1] * 1000U;
		c.value = d[2];
	} else {
		return BT_GATT_ERR(BT_ATT_ERR_VALUE_NOT_ALLOWED);
	}
	k_msgq_put(&commands, &c, K_NO_WAIT);
	return len;
}

static ssize_t read_battery(struct bt_conn *conn, const struct bt_gatt_attr *attr,
			    void *buf, uint16_t len, uint16_t offset)
{
	uint16_t v = sys_cpu_to_le16(vbat_mv);
	return bt_gatt_attr_read(conn, attr, buf, len, offset, &v, sizeof(v));
}

static void battery_ccc_changed(const struct bt_gatt_attr *attr, uint16_t value)
{
	vbat_notify = value == BT_GATT_CCC_NOTIFY;
}

BT_GATT_SERVICE_DEFINE(trigger_svc,
	BT_GATT_PRIMARY_SERVICE(&uuid_service),
	BT_GATT_CHARACTERISTIC(&uuid_command.uuid, BT_GATT_CHRC_WRITE_WITHOUT_RESP | BT_GATT_CHRC_WRITE,
			       BT_GATT_PERM_WRITE, NULL, write_command, NULL),
	BT_GATT_CHARACTERISTIC(&uuid_battery.uuid, BT_GATT_CHRC_READ | BT_GATT_CHRC_NOTIFY,
			       BT_GATT_PERM_READ, read_battery, NULL, NULL),
	BT_GATT_CCC(battery_ccc_changed, BT_GATT_PERM_READ | BT_GATT_PERM_WRITE),
);

/* --- Advertising / connection ---------------------------------------------------- */
static const struct bt_data ad[] = {
	BT_DATA_BYTES(BT_DATA_FLAGS, BT_LE_AD_GENERAL | BT_LE_AD_NO_BREDR),
	BT_DATA_BYTES(BT_DATA_UUID128_ALL, UUID_SERVICE),
};
static const struct bt_data sd[] = {
	BT_DATA(BT_DATA_NAME_COMPLETE, CONFIG_BT_DEVICE_NAME, sizeof(CONFIG_BT_DEVICE_NAME) - 1),
};
/* 30-60 ms advertising, as on the ESP32 board; the phone sees us at once */
static const struct bt_le_adv_param adv_param =
	BT_LE_ADV_PARAM_INIT(BT_LE_ADV_OPT_CONN, 0x0030, 0x0060, NULL);

static struct bt_conn *current_conn;
static void adv_timeout_fn(struct k_work *work);
static K_WORK_DELAYABLE_DEFINE(adv_timeout, adv_timeout_fn);

static void start_advertising(void)
{
	int err = bt_le_adv_start(&adv_param, ad, ARRAY_SIZE(ad), sd, ARRAY_SIZE(sd));
	if (err && err != -EALREADY) {
		LOG_ERR("adv start %d", err);
	}
	k_work_reschedule(&adv_timeout, ADV_TIMEOUT);
}

static void power_off(void)
{
	bt_le_adv_stop();
	gpio_pin_set_dt(&led, 0);
	gpio_pin_set_dt(&s1, 0);
	gpio_pin_set_dt(&s2, 0);
	/* the button (active low, pulled up) wakes the chip from System OFF */
	gpio_pin_interrupt_configure_dt(&button, GPIO_INT_LEVEL_ACTIVE);
	sys_poweroff();
}

static void adv_timeout_fn(struct k_work *work)
{
	if (current_conn == NULL) {
		LOG_INF("nobody came, sleeping");
		power_off();
	}
}

static void connected(struct bt_conn *conn, uint8_t err)
{
	if (err) {
		return;   /* recycled() restarts advertising */
	}
	current_conn = bt_conn_ref(conn);
	k_work_cancel_delayable(&adv_timeout);
	/* 30-50 ms interval, no latency: a shutter command is acted on within one interval */
	bt_conn_le_param_update(conn, BT_LE_CONN_PARAM(0x18, 0x28, 0, 400));
}

static void disconnected(struct bt_conn *conn, uint8_t reason)
{
	/* the app can no longer send the stop: end a bulb here so the outputs do not stay on */
	struct command stop = {.button = 2, .value = 0};
	k_msgq_put(&commands, &stop, K_NO_WAIT);
	if (current_conn) {
		bt_conn_unref(current_conn);
		current_conn = NULL;
	}
}

/* With BT_MAX_CONN=1 the connection object is still held in disconnected(), so
 * bt_le_adv_start fails there with -ENOMEM. It is free once recycled() runs. */
static void recycled(void)
{
	start_advertising();   /* ADV_TIMEOUT to reconnect, then sleep */
}

BT_CONN_CB_DEFINE(conn_cb) = {
	.connected = connected,
	.disconnected = disconnected,
	.recycled = recycled,
};

/* --- Battery ----------------------------------------------------------------------- */
static void vbat_update(struct k_work *work);
static K_WORK_DELAYABLE_DEFINE(vbat_work, vbat_update);

static void vbat_update(struct k_work *work)
{
	int16_t raw;
	struct adc_sequence seq = {.buffer = &raw, .buffer_size = sizeof(raw)};

	adc_sequence_init_dt(&vdd_adc, &seq);
	if (adc_read_dt(&vdd_adc, &seq) == 0) {
		int32_t mv = raw;
		adc_raw_to_millivolts_dt(&vdd_adc, &mv);
		vbat_mv = CLAMP(mv, 0, 0xffff);
		int pct = (int)(vbat_mv - VBAT_EMPTY_MV) * 100 / (VBAT_FULL_MV - VBAT_EMPTY_MV);
		bt_bas_set_battery_level(CLAMP(pct, 0, 100));
		if (vbat_notify && current_conn) {
			uint16_t v = sys_cpu_to_le16(vbat_mv);
			bt_gatt_notify(current_conn, &trigger_svc.attrs[4], &v, sizeof(v));
		}
	}
	k_work_reschedule(&vbat_work, VBAT_PERIOD);
}

/* --- Shutter ----------------------------------------------------------------------- */
static bool bulb_active, countdown_active;
static int64_t countdown_end, led_hold_until;

static void open_shutter(void)
{
	gpio_pin_set_dt(&s1, 1);
	k_msleep(S1_LEAD_MS);
	gpio_pin_set_dt(&s2, 1);
}

static void close_shutter(void)
{
	gpio_pin_set_dt(&s2, 0);
	gpio_pin_set_dt(&s1, 0);
}

static void trigger_shutter(void)
{
	bulb_active = false;
	open_shutter();
	k_msleep(TRIGGER_HOLD_MS);
	close_shutter();
}

/* Same semantics as handleCommand() in the ESP32 firmware: only 1 starts, a start
 * cancels a pending countdown, a stop leaves it running. */
static void handle(const struct command *c)
{
	bool start = c->value == 1;

	switch (c->button) {
	case 1:
		if (start) {
			countdown_active = false;
			trigger_shutter();
			led_hold_until = k_uptime_get() + LED_HOLD_MS;
		} else {
			led_hold_until = 0;
		}
		break;
	case 2:
		if (start) {
			countdown_active = false;
			bulb_active = true;
			open_shutter();
		} else {
			bulb_active = false;
			close_shutter();
		}
		break;
	case 3:
		if (start) {
			bulb_active = false;
			close_shutter();
			countdown_end = k_uptime_get() + c->duration_ms;
		}
		countdown_active = start;
		break;
	default:
		LOG_WRN("unknown button %u", c->button);
	}
}

/* LED: solid while the shutter is held or just fired, fast blink in a countdown,
 * short blink every 2 s while advertising, off when connected and idle. */
static void led_tick(int64_t now)
{
	bool on;

	if (bulb_active || now < led_hold_until) {
		on = true;
	} else if (countdown_active) {
		on = (now % 250) < 125;
	} else if (current_conn == NULL) {
		on = (now % 2000) < 40;
	} else {
		on = false;
	}
	gpio_pin_set_dt(&led, on);
}

/* --- Button: a press wakes from System OFF and restarts advertising; held 3 s, power off --- */
static void adv_work_fn(struct k_work *work)
{
	if (current_conn == NULL) {
		start_advertising();
	}
}
static K_WORK_DEFINE(adv_work, adv_work_fn);

static void long_press_fn(struct k_work *work)
{
	if (!gpio_pin_get_dt(&button)) {
		return;
	}
	/* a button still held, or bouncing on release, would wake System OFF at once */
	for (int released = 0; released < 3;) {
		k_msleep(20);
		released = gpio_pin_get_dt(&button) ? 0 : released + 1;
	}
	if (current_conn) {
		bt_conn_disconnect(current_conn, BT_HCI_ERR_REMOTE_POWER_OFF);
		k_msleep(100);   /* let the disconnect go out so the app sees it at once */
	}
	power_off();
}
static K_WORK_DELAYABLE_DEFINE(long_press, long_press_fn);

static struct gpio_callback button_cb;
static void button_pressed(const struct device *dev, struct gpio_callback *cb, uint32_t pins)
{
	k_work_submit(&adv_work);   /* bt_le_adv_start is not ISR-safe */
	k_work_reschedule(&long_press, LONG_PRESS);
}

/* How long the main loop may sleep before the LED or the countdown needs it */
static k_timeout_t next_wait(int64_t now)
{
	if (countdown_active || bulb_active || now < led_hold_until) {
		return K_MSEC(20);
	}
	if (current_conn == NULL) {
		int64_t phase = now % 2000;
		return K_MSEC(phase < 40 ? 40 - phase : 2000 - phase);
	}
	return K_SECONDS(1);
}

int main(void)
{
	gpio_pin_configure_dt(&led, GPIO_OUTPUT_INACTIVE);
	gpio_pin_configure_dt(&s1, GPIO_OUTPUT_INACTIVE);
	gpio_pin_configure_dt(&s2, GPIO_OUTPUT_INACTIVE);
	gpio_pin_configure_dt(&button, GPIO_INPUT);
	gpio_pin_interrupt_configure_dt(&button, GPIO_INT_EDGE_TO_ACTIVE);
	gpio_init_callback(&button_cb, button_pressed, BIT(button.pin));
	gpio_add_callback(button.port, &button_cb);
	adc_channel_setup_dt(&vdd_adc);

	/* a hung loop resets the chip, and reset releases S1/S2 */
	struct wdt_timeout_cfg wdt_cfg = {
		.window.max = WDT_TIMEOUT_MS,
		.flags = WDT_FLAG_RESET_SOC,
	};
	int wdt_ch = wdt_install_timeout(wdt, &wdt_cfg);
	wdt_setup(wdt, WDT_OPT_PAUSE_HALTED_BY_DBG);

	int err = bt_enable(NULL);
	if (err) {
		LOG_ERR("bt_enable %d", err);
		return 0;
	}
	start_advertising();
	k_work_schedule(&vbat_work, K_SECONDS(1));

	struct command c;
	while (1) {
		if (k_msgq_get(&commands, &c, next_wait(k_uptime_get())) == 0) {
			handle(&c);
		}
		int64_t now = k_uptime_get();
		if (countdown_active && now >= countdown_end) {
			countdown_active = false;
			trigger_shutter();
		}
		led_tick(now);
		wdt_feed(wdt, wdt_ch);
	}
	return 0;
}
