import RPi.GPIO as GPIO
import time
import threading

PIN_TOP = 23
PIN_BOTTOM = 24
STABLE_TIME = 0.2

GPIO.setmode(GPIO.BCM)
GPIO.setup(PIN_TOP, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(PIN_BOTTOM, GPIO.IN, pull_up_down=GPIO.PUD_UP)

last_stable_state = None
lock = threading.Lock()
timer = None

stop_event = threading.Event()

def read_button():
    return GPIO.input(PIN_TOP) == GPIO.LOW or GPIO.input(PIN_BOTTOM) == GPIO.LOW

def validate_state():
    global last_stable_state, timer
    timer = None
    state = read_button()
    with lock:
        if state != last_stable_state:
            last_stable_state = state
            if state:
                print("→ bouton HAUT")
            else:
                print("→ bouton BAS")

def on_change(channel):
    global timer
    if timer:
        timer.cancel()
    timer = threading.Timer(STABLE_TIME, validate_state)
    timer.start()

GPIO.add_event_detect(PIN_TOP, GPIO.BOTH, callback=on_change, bouncetime=50)
GPIO.add_event_detect(PIN_BOTTOM, GPIO.BOTH, callback=on_change, bouncetime=50)

last_stable_state = read_button()
print(f"État initial : {'BAS' if last_stable_state else 'HAUT'}")

try:
    # attend indéfiniment, mais proprement
    stop_event.wait()
except KeyboardInterrupt:
    GPIO.cleanup()
