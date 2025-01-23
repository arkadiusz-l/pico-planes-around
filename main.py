import network
from time import sleep
from picographics import PicoGraphics, DISPLAY_PICO_DISPLAY, PEN_P4
import urequests
from wifi_config import SSID, KEY, IP, MASK, GATEWAY, DNS
from config import POS_LAT, POS_LONG, RADIUS, INTERVAL


def clear_display():
    display.set_pen(BLACK)
    display.clear()
    display.update()


def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(SSID, KEY)
    wlan.ifconfig((IP, MASK, GATEWAY, DNS))
    wlan.ifconfig()

    if wlan.isconnected():
        print('Successfully connected to the Wi-Fi')

    while not wlan.isconnected():
        print('Connecting to a Wi-Fi...')
        sleep(1)


def get_planes():
    planes = {}
    planes_around = []
    try:
        response = urequests.get(URL)
        planes = response.json()
        response.close()
    except Exception as e:
        print("An error occurred while connecting to the API:", e)

    for plane in planes['ac']:
        callsign = plane.get('flight')
        reg = plane.get('r', 'empty')
        planes_around.append((callsign, reg))
    return planes_around


if __name__ == '__main__':
    display = PicoGraphics(display=DISPLAY_PICO_DISPLAY, pen_type=PEN_P4, rotate=0)
    display.set_backlight(0.5)
    display.set_font("bitmap8")
    WHITE = display.create_pen(255, 255, 255)
    BLACK = display.create_pen(0, 0, 0)
    GREEN = display.create_pen(0, 255, 0)

    connect_wifi()

    URL = f"https://api.adsb.lol/v2/point/{POS_LAT}/{POS_LONG}/{RADIUS}"

    while True:
        clear_display()
        planes_around = get_planes()
        display.set_pen(GREEN)
        nm_to_km = RADIUS * 1.852
        text = f"Planes around you\n within a {round(nm_to_km)} km radius: {len(planes_around)}"
        print(text)
        display.text(text, 10, 10, 240, 2)
        print(planes_around)
        Y = 50
        display.set_pen(WHITE)
        if planes_around:
            for plane in planes_around:
                callsign, reg = plane
                text = f"{callsign} - {reg}"
                display.text(text, 10, Y, 240, 2)
                print(text)
                Y += 20
        display.update()
        sleep(INTERVAL)
