# k2000.py
from gpiozero import PWMLED
from time import sleep
import threading
import random

class K2000:
    def __init__(self, pins=None, speed=0.1):
        if pins is None:
            pins = [7, 8, 12, 16, 20, 21, 25, 1]  # valeurs par défaut
        self.leds = [PWMLED(p) for p in pins]
        self.virtual_len = len(self.leds) + 4
        self.speed = speed
        self._stop_event = threading.Event()
        self._thread = None

    def leds_on(self):
        for led in self.leds:
            led.value = 0.01

    def intensity(self, offset):
        if offset == 0:
            return 1.0
        elif abs(offset) == 1:
            return 0.3
        else:
            return 0.01

    def _animate_k2000(self):
        while not self._stop_event.is_set():
            # gauche -> droite
            for pos in range(self.virtual_len):
                if self._stop_event.is_set():
                    break
                for i, led in enumerate(self.leds):
                    led.value = self.intensity(i - (pos - 2))
                sleep(self.speed)
            # droite -> gauche
            for pos in range(self.virtual_len - 1, -1, -1):
                if self._stop_event.is_set():
                    break
                for i, led in enumerate(self.leds):
                    led.value = self.intensity(i - (pos - 2))
                sleep(self.speed)

    def _animate_blink(self):
        # clignotement doux 3 fois
        for _ in range(3):
            # monte la luminosité
            for val in [x / 20.0 for x in range(0, 21)]:
                for led in self.leds:
                    led.value = val
                sleep(0.05)
            # redescend
            for val in [x / 20.0 for x in range(20, -1, -1)]:
                for led in self.leds:
                    led.value = val
                sleep(0.05)
        self.stop()

    def _animate_wait(self):
        while not self._stop_event.is_set():
            led = random.choice(self.leds)
            led.value = 1.0
            sleep(0.5)
            led.value = 0.05
            if self._stop_event.is_set():
                break
                
    def start(self, mode=None):
        self._stop_event.clear()
        if mode == "blink":
            self._thread = threading.Thread(target=self._animate_blink)
        elif mode == "wait":
            self._thread = threading.Thread(target=self._animate_wait)
        else:
            self._thread = threading.Thread(target=self._animate_k2000)
        self._thread.start()

    def stop(self):
        self._stop_event.set()
        if self._thread and threading.current_thread() != self._thread:
            self._thread.join()
        self.leds_on()