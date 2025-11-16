#dtparam=hat_id=off
#sudo systemctl stop surrealist

from gpiozero import LED
from time import sleep

# tous les GPIO utilisables (hors alim et GND)
pins = [
    2, 3, 4, 5, 6, 7, 8, 9, 10,
    11, 12, 13, 14, 15, 16, 17,
    18, 19, 20, 21, 22, 23, 24,
    25, 26, 27, 1
]

pins = [7, 8, 12, 16, 20, 21, 25, 1]


leds = [LED(p) for p in pins]

print("=== Test interactif de toutes les GPIO ===")
print("Appuie sur Entrée pour tester la suivante (Ctrl+C pour quitter)\n")

for i, led in enumerate(leds):
    input(f"GPIO {pins[i]} -> Entrée pour allumer : ")
    led.on()
    print(f"GPIO {pins[i]} ON")
    input(f"GPIO {pins[i]} -> Entrée pour eteindre : ")
    led.off()
    print(f"GPIO {pins[i]} OFF\n")

print("Fin du test 🔥")
    