import network
from utime import sleep
from pimoroni import RGBLED
from picographics import PicoGraphics, DISPLAY_PICO_DISPLAY, PEN_P4
import urequests
from wifi_config import SSID, KEY, IP, MASK, GATEWAY, DNS
from config import POS_LAT, POS_LONG, RADIUS, INTERVAL


def clear_display():
    display.set_pen(BLACK)
    display.clear()
    display.update()
    led.set_rgb(0, 0, 0)


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
        response = urequests.get(API)
        data = response.json()
        response.close()
    except Exception as e:
        print("An error occurred while connecting to the API:", e)

    planes = data['ac']
    planes.sort(key=lambda x: x['dst'])
    for plane in planes:
        type = plane.get('t', 'unk.')
        reg = plane.get('r', 'unk.')
        callsign = plane.get('flight', reg).rstrip()  # if no callsign, shows reg
        distance = plane.get('dst', '999')  # planes without "dst" will be at the end of the list after sorting
        direction = plane.get('dir', 'unk.')
        planes_around.append((type, callsign, reg, distance, direction))
    return planes_around

if __name__ == '__main__':
    display = PicoGraphics(display=DISPLAY_PICO_DISPLAY, pen_type=PEN_P4, rotate=0)
    display.set_backlight(0.5)
    display.set_font("bitmap8")

    led = RGBLED(6, 7, 8)

    WHITE = display.create_pen(255, 255, 255)
    BLACK = display.create_pen(0, 0, 0)
    GREEN = display.create_pen(0, 255, 0)
    CYAN = display.create_pen(0, 255, 255)
    MAGENTA = display.create_pen(255, 0, 255)
    YELLOW = display.create_pen(255, 255, 0)

    connect_wifi()

    API = f"https://api.adsb.lol/v2/point/{POS_LAT}/{POS_LONG}/{RADIUS}"

    while True:
        planes = get_planes()
        nm_to_km = RADIUS * 1.852
        text = f"Planes\nwithin a {round(nm_to_km)} km radius: {len(planes)}"
        clear_display()
        display.set_pen(GREEN)
        display.text(text, 0, 0, 240, 2)
        print(text)
        Y = 50
        display.set_pen(WHITE)
        if planes:
            for plane in planes:
                type, callsign, reg, distance, direction = plane
                distance_in_km = round(distance * 1.852)
                display.set_pen(CYAN)
                display.text(type, 0, Y, 80, 2)
                display.set_pen(MAGENTA)
                display.text(callsign, 60, Y, 80, 2)
                display.set_pen(YELLOW)
                display.text(f"{distance_in_km} km", 140, Y, 80, 2)
                display.set_pen(WHITE)
                display.text(f"{round(direction)}°", 205, Y, 80, 2)
                print(f"{type} | {callsign} | {reg} | {distance_in_km} km | {round(direction)}°")
                Y += 20
        display.update()
        print()
        sleep(INTERVAL)
