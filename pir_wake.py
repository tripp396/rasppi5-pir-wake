from gpiozero import MotionSensor
from signal import pause
import subprocess
import time
import threading
import paho.mqtt.client as mqtt

# === Configuration ===
PIR_GPIO = 17
MQTT_BROKER = "192.168.1.2" #Add your MQTT IP here
MQTT_PORT = 1883
MQTT_USERNAME = "mqtt" #Change to your MQTT username
MQTT_PASSWORD = "mqttpassword" #Change to your MQTT password

MQTT_TOPIC_STATE = "rpi5/motion"
MQTT_TOPIC_AVAIL = "rpi5/motion/availability"
MQTT_CLIENT_ID = "rpi5-motion-sensor"

MQTT_RESET_TIMEOUT = 30
SCREEN_OFF_TIMEOUT = 300

# === X11 Environment Variables ===
X11_ENV = {
    "DISPLAY": ":0",
    "XAUTHORITY": "/home/pi/.Xauthority" #If you have a different user then you will need to change from "pi" to whatever that username is
}

# === State Variables ===
last_motion_time = time.time()
mqtt_state_on = False

# === MQTT Setup ===
def on_connect(client, userdata, flags, rc):
    print(f"[MQTT] Connected with result code {rc}")
    client.publish(MQTT_TOPIC_AVAIL, "online", retain=True)

print("📡 Setting up MQTT client...")
client = mqtt.Client(MQTT_CLIENT_ID)
client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
client.will_set(MQTT_TOPIC_AVAIL, "offline", retain=True)
client.on_connect = on_connect
client.connect(MQTT_BROKER, MQTT_PORT, 60)
client.loop_start()

# === Helpers ===

def is_screen_on():
    try:
        result = subprocess.run(
            ["xset", "q"],
            env=X11_ENV,
            capture_output=True,
            text=True
        )
        return "Monitor is On" in result.stdout
    except Exception as e:
        print(f"⚠️ Could not determine screen state: {e}")
        return True  # assume on if unsure

def publish_motion(state):
    print(f"[MQTT] Publishing motion state: {state}")
    client.publish(MQTT_TOPIC_STATE, state, retain=True)

def turn_on_display():
    global last_motion_time, mqtt_state_on
    last_motion_time = time.time()

    print("💡 Motion detected. Entering turn_on_display()")
    print("🔍 Environment:")
    print(f"  DISPLAY = {X11_ENV.get('DISPLAY')}")
    print(f"  XAUTHORITY = {X11_ENV.get('XAUTHORITY')}")

    screen_now_on = is_screen_on()
    print(f"🖥️ Actual screen state: {'on' if screen_now_on else 'off'}")

    if not screen_now_on:
        print("🔧 Attempting to turn ON display...")
        try:
            result = subprocess.run(
                ["xset", "dpms", "force", "on"],
                env=X11_ENV,
                capture_output=True,
                text=True
            )
            print(f"✅ xset return code: {result.returncode}")
            print(f"stdout: {result.stdout.strip()}")
            print(f"stderr: {result.stderr.strip()}")
        except Exception as e:
            print(f"❌ Exception while running xset: {e}")
    else:
        print("🟡 Screen already on — skipping xset")

    if not mqtt_state_on:
        print("📡 Sending MQTT motion ON...")
        publish_motion("ON")
        mqtt_state_on = True
    else:
        print("🟢 MQTT already ON — skipping publish")

def turn_off_display():
    print("🌙 Checking if screen needs to be turned OFF...")
    if is_screen_on():
        print("🔧 Turning OFF display via xset...")
        try:
            result = subprocess.run(
                ["xset", "dpms", "force", "off"],
                env=X11_ENV,
                capture_output=True,
                text=True
            )
            print(f"✅ xset return code: {result.returncode}")
            print(f"stdout: {result.stdout.strip()}")
            print(f"stderr: {result.stderr.strip()}")
        except Exception as e:
            print(f"❌ Exception while running xset: {e}")
    else:
        print("🟡 Screen already off — skipping xset")

def monitor_inactivity():
    global mqtt_state_on
    while True:
        idle_time = time.time() - last_motion_time

        if mqtt_state_on and idle_time > MQTT_RESET_TIMEOUT:
            print(f"📉 No motion for {MQTT_RESET_TIMEOUT}s. Sending MQTT OFF...")
            publish_motion("OFF")
            mqtt_state_on = False

        if idle_time > SCREEN_OFF_TIMEOUT:
            print(f"⏲️ No activity for {SCREEN_OFF_TIMEOUT}s. Triggering screen off...")
            turn_off_display()

        time.sleep(2)

# === Main Execution ===

print("🚀 Starting PIR + MQTT screen controller script...")

try:
    pir = MotionSensor(PIR_GPIO)
    pir.when_motion = turn_on_display
    print("✅ PIR motion callback registered.")
except Exception as e:
    print(f"❌ Failed to initialize PIR sensor: {e}")

threading.Thread(target=monitor_inactivity, daemon=True).start()

pause()
