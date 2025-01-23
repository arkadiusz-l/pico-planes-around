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
    data = {}
    planes_around = []
    try:
        response = urequests.get(URL)
        data = response.json()
        response.close()
    except Exception as e:
        print("An error occurred while connecting to the API:", e)

    planes = data['ac']
    planes.sort(key=lambda x: x['dst'])
    for plane in planes:
        callsign = plane.get('flight', 'empty').rstrip()
        reg = plane.get('r', 'empty')
        distance = plane.get('dst', '999')  # planes without "dst" will be at the end of the list after sorting
        planes_around.append((callsign, reg, distance))
    return planes_around

if __name__ == '__main__':
    display = PicoGraphics(display=DISPLAY_PICO_DISPLAY, pen_type=PEN_P4, rotate=0)
    display.set_backlight(0.5)
    display.set_font("bitmap8")
    WHITE = display.create_pen(255, 255, 255)
    BLACK = display.create_pen(0, 0, 0)
    GREEN = display.create_pen(0, 255, 0)
    CYAN = display.create_pen(0, 255, 255)
    MAGENTA = display.create_pen(255, 0, 255)
    YELLOW = display.create_pen(255, 255, 0)

    connect_wifi()

    URL = f"https://api.adsb.lol/v2/point/{POS_LAT}/{POS_LONG}/{RADIUS}"

    while True:
        clear_display()
        planes = get_planes()
        display.set_pen(GREEN)
        nm_to_km = RADIUS * 1.852
        text = f"Planes around you\n within a {round(nm_to_km)} km radius: {len(planes)}"
        print(text)
        display.text(text, 0, 0, 240, 2)
        print(planes)
        Y = 50
        display.set_pen(WHITE)
        if planes:
            for plane in planes:
                callsign, reg, distance = plane
                display.set_pen(CYAN)
                display.text(callsign, 0, Y, 80, 2)
                display.set_pen(MAGENTA)
                display.text(reg, 90, Y, 80, 2)
                display.set_pen(YELLOW)
                display.text(f"{round(distance * 1.852)} km", 175, Y, 80, 2)
                print(text)
                Y += 20
        display.update()
        sleep(INTERVAL)
