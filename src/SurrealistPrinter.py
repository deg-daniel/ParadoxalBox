from escpos.printer import Usb
from PIL import Image, ImageDraw
import random
import datetime
import json
import requests
import base64
from io import BytesIO
import logging
import sys
import unidecode
import qrcode
from dotenv import load_dotenv
import os

class SurrealistPrinter:
    def __init__(self):
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        load_dotenv(os.path.join(BASE_DIR, ".env"))
        self.OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
        self.VENDOR_ID = int(os.getenv("PRINTER_VENDOR_ID"),16)
        self.PRODUCT_ID = int(os.getenv("PRINTER_PRODUCT_ID"),16)
        self.PROMPT_DEFAULT = "Génère une phrase surréaliste assez courte qu'on pourrait interpréter logiquement dans la vraie vie."
        self.CHAR_BY_LINE = 48
        self.PIXEL_BY_LINE = 384

        self.printer = Usb(self.VENDOR_ID, self.PRODUCT_ID)
        #self.printer._raw(b'\x1b\x74\x02')  # force CP850
        #self.printer.charcode('CP850')

    def generate_sentence(self):
        try:
            with open("prompt.txt", "r", encoding="utf-8") as f:
                prompt = f.read().strip()
        except Exception as e:
            prompt = ""
        if not prompt:
            prompt = self.PROMPT_DEFAULT
        print(prompt)
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.OPENAI_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "gpt-4",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.8,
            "max_tokens": 60
        }

        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=20)
            #print(resp.headers.get("x-ratelimit-limit-requests"))
            #print(resp.headers.get("x-ratelimit-remaining-requests"))
            #print(resp.headers.get("Retry-After"))
            resp.raise_for_status()
            data = resp.json()
            logging.info( data['choices'][0]['message']['content'].strip() )
            text = data['choices'][0]['message']['content']
            if (text.startswith('"') and text.endswith('"')) or (text.startswith("'") and text.endswith("'")):
                text = text[1:-1]
            return "* " + text.strip()
        except Exception as e:
            logging.exception(f"Exception OpenAI sentence: {e}")
            print("Exception OpenAI:", e)
            return "L'imagination a pris une pause café."

    def generate_image(self, sentence="quelque chose de surréaliste"):
        try:
            with open("prompt_image.txt", "r", encoding="utf-8") as f:
                prompt_image = f.read().strip()
        except Exception as e:
            prompt_image = ""
        if prompt_image:
            prompt_image = prompt_image.replace("[SENTENCE]",sentence)
        else:
            prompt_image = sentence
            
        prompt = f"Génère un clipart minimaliste en noir et blanc 1-bit, style dessin au trait simple, sans nuances à partir de cette phrase : \"{prompt_image}\""

        url = "https://api.openai.com/v1/images/generations"
        headers = {
            "Authorization": f"Bearer {self.OPENAI_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "dall-e-3",
            "prompt": prompt,
            "n": 1,
            "size": "1024x1024",
            "response_format": "b64_json"
        }

        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=30)
            resp.raise_for_status()
            b64_data = resp.json()['data'][0]['b64_json']
            img_bytes = base64.b64decode(b64_data)
            img = Image.open(BytesIO(img_bytes)).convert("1")
            img = img.resize((self.PIXEL_BY_LINE, self.PIXEL_BY_LINE), Image.LANCZOS)
            return img
        except Exception as e:
            logging.exception(f"Exception OpenAI image: {e}")
            print("Exception OpenAI image:", e)
            return self.create_fallback_image()

    def create_fallback_image(self, width=None, height=200):
        width = width or self.PIXEL_BY_LINE
        img = Image.new('1', (width, height), 1)
        draw = ImageDraw.Draw(img)

        # Lune + oeil stylisé
        x1, y1 = random.randint(20, 100), random.randint(30, 100)
        size = random.randint(60, 100)
        draw.pieslice([(x1, y1), (x1 + size, y1 + size)], 30, 330, fill=0)
        draw.ellipse([(x1 + size // 3, y1), (x1 + size, y1 + size)], fill=1)

        eye_x, eye_y = random.randint(width // 2, width - 80), random.randint(40, height - 80)
        eye_w, eye_h = random.randint(70, 100), random.randint(40, 60)
        draw.ellipse([(eye_x, eye_y), (eye_x + eye_w, eye_y + eye_h)], outline=0, width=2)
        pupil_x = eye_x + eye_w // 3 + random.randint(-5, 5)
        pupil_y = eye_y + eye_h // 3 + random.randint(-5, 5)
        draw.ellipse([(pupil_x, pupil_y), (pupil_x + eye_w // 6, pupil_y + eye_h // 3)], fill=0)

        return img

    def wrap_text(self, text):
        words = text.split()
        lines, line = [], []
        for word in words:
            if sum(len(w) for w in line) + len(word) + len(line) <= self.CHAR_BY_LINE:
                line.append(word)
            else:
                lines.append(' '.join(line))
                line = [word]
        lines.append(' '.join(line))
        return '\n'.join(lines)

    def center_line(self, text):
        space = max(0, (self.CHAR_BY_LINE - len(text)) // 2)
        return ' ' * space + text

    def maintenant(self):
        now = datetime.datetime.now()
        jour = now.strftime("%A")
        date = now.strftime("%d %B")
        heure = now.strftime("%Hh%M")
        secondes = now.strftime("%S")
        centiemes = int(now.microsecond / 10000)
        return (
            self.center_line(f"{jour} {date} {heure} et {secondes} secondes") + "\n" +
            self.center_line(f"(et {centiemes} centiemes)") + "\n"
        )


    def surrealist(self):
        sentence = self.generate_sentence()
        img = self.generate_image(sentence=sentence)
        text = self.maintenant() + "\n" + self.wrap_text(sentence) + "\n"
        text = unidecode.unidecode(text) # pas d'accens !
        print(text)

        self.printer.text(text)
        #self.printer._raw(text.encode("cp850", errors="replace"))
        self.printer.image(img)
        #self.printer.text("\n")  # petite ligne vide
        self.printer.cut()

    def qrcode(self,data):
        self.printer.text("Conf pour le prompt:\n")
        self.printer.text(data)
        self.printer.text("\n")  # petite ligne vide
        
        qr = qrcode.QRCode(
            version=1,
            box_size=10,
            border=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L
        )
        qr.add_data(data)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white").convert("1")
        img = img.resize((self.PIXEL_BY_LINE, self.PIXEL_BY_LINE), Image.NEAREST)
        
        self.printer.image(img)
        self.printer.cut()
