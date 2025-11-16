from gpiozero import Button
from signal import pause
import threading
import time
from k2000 import K2000
from SurrealistPrinter import SurrealistPrinter
import subprocess

k = K2000()
printer = SurrealistPrinter()
lock = threading.Lock()

button_down = Button(24, pull_up=True, bounce_time=0.2)
button_up = Button(23, pull_up=True, bounce_time=0.2)

state = "idle"  # idle, down, up
last_change = 0
MIN_DURATION = 2  # secondes
busy = False
wlan_up = True

# petite anim si connexion ou pas
def watch_wlan():
    global wlan_up
    while True:
        try:
            status = subprocess.check_output(
                ['nmcli', '-t', '-f', 'DEVICE,STATE', 'device'], text=True
            )
            wlan_status = None
            for line in status.strip().split("\n"):
                device, state = line.split(":")
                if device == "wlan1":
                    wlan_status = state
                    break

            if wlan_status != "connected" and wlan_up:
                # perte de connexion détectée
                print("wlan1 → DOWN")
                k.stop()
                k.start(mode="wait")
                wlan_up = False
            elif wlan_status == "connected" and not wlan_up:
                # reconnexion détectée
                print("wlan1 → UP")
                k.stop()
                k.start(mode="blink")
                wlan_up = True

        except Exception as e:
            print("watch_wlan error:", e)

        time.sleep(2)
        
def trigger(action):
    global busy, last_change
    now = time.time()
    if busy or now - last_change < MIN_DURATION:
        return  # ignore si déjà en action ou trop tôt
    busy = True
    last_change = now
    threading.Thread(target=lambda: run(action), daemon=True).start()

def run(action):
    global busy
    if action == "down":
        k.start()
        print("button DOWN")
        printer.surrealist()
        time.sleep(3)
        k.stop()
    elif action == "up":
        k.start(mode="wait")
        print("button UP")
        time.sleep(3)
        k.stop()
    print("End")
    busy = False  # fini → autorise le prochain état

def down():    
    global state
    if state != "down":
        state = "down"
        trigger("down")

def up():
    global state
    if state != "up":
        state = "up"
        trigger("up")

button_down.when_pressed = down
button_up.when_pressed = up

k.leds_on()

# au demarrage, affiche l'IP et le QrCode pour modifier le prompt
output = subprocess.check_output(
    ["nmcli", "-t", "-f", "IP4.ADDRESS", "device", "show", "wlan1"],
    text=True
)
for line in output.splitlines():
    if line.startswith("IP4.ADDRESS"):
        ip = line.split(":")[1].split("/")[0]
ip = None
if ip:
    #print("définir le wifi:")
    #print("wifi: ParadoxalBox")
    #print("pass: 12345678")
    #print("http://10.42.0.1/")
    #print("-")
    print("conf pour le prompt")
    data = f"http://{ip}/"
    print(data)
    printer.qrcode(data)

#threading.Thread(target=watch_wlan, daemon=True).start()

pause()
