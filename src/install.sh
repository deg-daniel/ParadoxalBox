#!/bin/bash
set -e

if [ -z "$SUDO_USER" ]; then
    echo "Run this script with sudo, not directly as root"
    exit 1
fi

echo "[1] Install services"

REAL_USER="$SUDO_USER"
REAL_HOME=$(eval echo "~$REAL_USER")

for f in surrealist_*.service; do
    echo "Installing $f for $REAL_USER"
    # read the file, replace /home/admin with $REAL_HOME, write directly to systemd
    sed "s|/home/admin|$REAL_HOME|g" "$f" | sudo tee "/etc/systemd/system/$f" > /dev/null
    sudo systemctl enable "$f"
done

echo "[2] Python dependencies"
apt update
apt install -y python3-gpiozero python3-pip
pip3 install python-escpos unidecode pyusb python-dotenv --break-system-packages

echo "[3] GPIO tweaks"
grep -q "dtparam=hat_id=off" /boot/firmware/config.txt || echo "dtparam=hat_id=off" >> /boot/firmware/config.txt

echo "[4] Network config"
read -p "Do you want to configure Wi-Fi / Do you have an extra Wi-Fi dongle? (Y/N) " choice
choice=${choice^^}  # uppercase for comparison

if [[ "$choice" == "Y" ]]; then
    read -p "SSID: " SSID
    read -sp "Password: " PSK
    echo

    # patch preconfigured.nmconnection on the fly
    sed "s|SSID_PLACEHOLDER|$SSID|g; s|PSK_PLACEHOLDER|$PSK|g" preconfigured.nmconnection | sudo tee /etc/NetworkManager/system-connections/preconfigured.nmconnection > /dev/null
    sudo chmod 600 /etc/NetworkManager/system-connections/preconfigured.nmconnection
    sudo cp ParadoxalBox.nmconnection /etc/NetworkManager/system-connections/
    sudo chmod 600 /etc/NetworkManager/system-connections/*
    sudo nmcli connection reload

    echo "wlan0 AP: ParadoxalBox 12345678"
fi

echo "[Done]"

echo "The LEDs are connected in order to pins 7, 8, 12, 16, 20, 21, 25, 1"
echo "You can test the connection with test_gpio.py"
echo "The buttons are on pins 23 and 24"
echo "You can test them with test_bouton.py"
echo

VAL=$(grep "^OPENAI_API_KEY=" .env | cut -d '=' -f2-)

if [ -n "$VAL" ]; then
    echo "key openai fond.ok"
else
    echo "key openai empty, edit .env !!"
fi

