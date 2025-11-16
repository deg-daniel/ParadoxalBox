from http.server import BaseHTTPRequestHandler, HTTPServer
import urllib.parse, os, html
import subprocess
import threading
import configparser
import ipaddress

PORT = 80

def ip_on_wlan0(client_ip):
    res = subprocess.run(["ip", "-4", "addr", "show", "wlan0"], capture_output=True, text=True)
    for line in res.stdout.splitlines():
        line = line.strip()
        if line.startswith("inet "):
            net = ipaddress.ip_network(line.split()[1], strict=False)
            return ipaddress.ip_address(client_ip) in net
    return False
    
def create_wifi_profile(ssid, password):
    connection_name = "preconfigured"
    file_path = f"/etc/NetworkManager/system-connections/{connection_name}.nmconnection"
    config = configparser.ConfigParser()
    config.read(file_path)

    if 'wifi' not in config:
        config['wifi'] = {}
    config['wifi']['ssid'] = ssid

    if 'wifi-security' not in config:
        config['wifi-security'] = {}
    config['wifi-security']['key-mgmt'] = 'wpa-psk'
    config['wifi-security']['psk'] = password

    with open(file_path, 'w') as f:
        config.write(f)

    subprocess.run(['nmcli', 'connection', 'reload'])
    subprocess.run(['nmcli', 'connection', 'up', connection_name])
    
    # loop jusqu'à ce qu'on ait une IP ou timeout
    start = time.time()
    ip = None
    while time.time() - start < 10:
        try:
            # récupère l'IP IPv4 de l'interface du profil
            result = subprocess.run(
                ['nmcli', '-t', '-f', 'IP4.ADDRESS', 'connection', 'show', connection_name],
                capture_output=True, text=True
            )
            ip_line = result.stdout.strip()
            if ip_line:
                ip = ip_line.split('/')[0]  # prends juste l'adresse
                break
        except Exception:
            pass
        time.sleep(0.5)

    return ip

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        p = html.escape(open("prompt.txt", "r", encoding="utf-8").read()) if os.path.exists("prompt.txt") else ""
        pi = html.escape(open("prompt_image.txt", "r", encoding="utf-8").read()) if os.path.exists("prompt_image.txt") else ""
        client_ip = self.client_address[0]
        wlan0 = ip_on_wlan0(client_ip)

        page = f"""
        <html><head><meta charset="utf-8">
        <title>Modifier les prompts de la Paradoxal Box</title>
        <style>
            body {{ font-family:sans-serif; background:#fff; color:#000; margin:40px; }}
            textarea {{ width:100%; border: solid 1px #000; height:150px; background:#fff; color:#000; padding:10px; font-family:monospace; border-radius:8px; margin-bottom:10px; }}
            button {{ padding:10px 20px; background:#FFF; border:solid 1px #000; border-radius:6px; cursor:pointer; font-weight:bold; }}
            button:hover {{ background:#9f9; }}
            h1, h2 {{ color:#000; }}
            p {{ font-size:0.7em; font-style:italic }}
        </style>
        </head><body>
        <h1>Modifier les prompts de la Paradoxal Box.</h1>

        <form method="POST" action="/prompts">
            <h2>Prompt texte</h2>
            <p>Defaut prompt: Génère une phrase surréaliste assez courte qu'on pourrait interpréter logiquement dans la vraie vie.</p>
            <textarea name="prompt">{p}</textarea>

            <h2>Prompt image (si vide, utilise le prompt texte)</h2> 
            <textarea name="prompt_image">{pi}</textarea><br>

            <button type="submit">💾 Enregistrer Prompt</button>
        </form>
        <br/><br/>
        """
        if wlan0:
            page = page + """
            <form method="POST" action="/wifi">
                <h2>Wi-Fi</h2>
                Pour admin, changer le Wifi: <input name="ssid" placeholder="SSID">&nbsp;<input name="password" placeholder="password"><br>
                <br/>
                <button type="submit">💾 Enregistrer WiFi</button>
            </form>
            """
        page = page + """    
        </body></html>
        """
        self.send_response(200)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(page.encode("utf-8"))

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        data = urllib.parse.parse_qs(self.rfile.read(length).decode("utf-8"))
        
        if self.path == "/prompts":
            with open("prompt.txt", "w", encoding="utf-8") as f:
                f.write(data.get("prompt", [""])[0])
            with open("prompt_image.txt", "w", encoding="utf-8") as f:
                f.write(data.get("prompt_image", [""])[0])
            self.send_response(303)
            self.send_header("Location", "/")
            self.end_headers()

        elif self.path == "/wifi":
            ssid = data.get("ssid", [""])[0]
            password = data.get("password", [""])[0]
            ip = create_wifi_profile(ssid, password)
            self.send_response(200)
            self.end_headers()
            msg = f"OK, je change le wifi. New IP: {ip}"
            self.wfile.write(msg.encode("utf-8"))
        
print("serve..")
HTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
