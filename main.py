import network
from utime import sleep
from time import localtime
import uasyncio as asyncio
import urequests
from pimoroni import RGBLED
from machine import Pin
from picographics import PicoGraphics, DISPLAY_PICO_DISPLAY, PEN_P4
from wifi_config import SSID, KEY, IP, MASK, GATEWAY, DNS
from config import POS_LAT, POS_LONG, RADIUS, INTERVAL


def change_views(views):
    while True:
        for view in views:
            yield view


async def handle_button(views):
    button_pressed = False
    view_generator = change_views(views=views)
    next(view_generator)  # generator loads the second in order functions from `Views` (because 1 is already load while starting the program) to call it below after pressing the button

    while True:
        if not button_pressed:
            if button_a.value() == 0:  # if button pressed
                button_pressed = True
                current_view = next(view_generator)  # stores references to the function
                await current_view(planes_around=planes_around)  # calls one of the functions from the "Views" and inserts the argument in it
            elif button_b.value() == 0:  # if button pressed
                button_pressed = True
                pass
        if button_a.value() == 1 and button_b.value() == 1:  # if button not pressed
            button_pressed = False
        await asyncio.sleep(0.1)


def clear_display():
    display.set_pen(BLACK)
    display.clear()
    display.update()


def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(SSID, KEY)
    wlan.ifconfig((IP, MASK, GATEWAY, DNS))

    if wlan.isconnected():
        print('Successfully connected to the Wi-Fi')

    while not wlan.isconnected():
        print('Connecting to a Wi-Fi...')
        sleep(1)


async def show_all_planes(planes_around):
    while True:
        planes_around.clear()
        print("Downloading data from API...")
        new_planes = get_planes(api=API)
        print(f"Data downloaded from API, date: {localtime()}")
        if new_planes:
            for plane in new_planes:
                type = plane.get('t', 'unk.')
                reg = plane.get('r', 'unk.')
                callsign = plane.get('flight', reg).rstrip()  # if no callsign, shows reg
                distance = plane.get('dst', '999')  # planes without "dst" will be at the end of the list after sorting
                direction = plane.get('dir', 'unk.')
                altitude = plane.get('alt_baro', '-')
                planes_around.append((type, callsign, reg, altitude, direction, distance))
        show_planes(planes_to_show=planes_around)
        await asyncio.sleep(INTERVAL)


async def show_planes_details(planes_around):
    if planes_around:
        clear_display()
        plane = planes_around[0]
        type, callsign, reg, altitude, direction, distance = plane
        data_to_display = [
            (f"Type:   {type}", CYAN),
            (f"Callsign:   {callsign}", MAGENTA),
            (f"Reg:   {reg}", WHITE),
            (f"Altitude:   {altitude} ft", GREEN),
            (f"Direction:   {direction}°", CYAN),
            (f"Distance:   {round(distance * 1.852)} km", YELLOW)
        ]

        start_y = 20
        line_spacing = 20
        for index, (text, color) in enumerate(data_to_display):
            y = start_y + index * line_spacing
            display.set_pen(color)
            display.text(text, 0, y, 240, 2)
        display.update()
        print(plane)
    display.set_pen(MAGENTA)
    display.text("No planes!", 20, 100, 240, 2)


def get_planes(api):
    data = {}
    planes_all_data = []
    try:
        response = urequests.get(api)
        data = response.json()
        response.close()
    except Exception as e:
        print("An error occurred while connecting to the API:", e)

    try:
        planes_all_data = data.get('ac')
        planes_all_data.sort(key=lambda x: x['dst'])
    except Exception as e:
        print("An error occurred:", e)

    return planes_all_data


def show_planes(planes_to_show):
    nm_to_km = RADIUS * 1.852
    text = f"Planes\nwithin a {round(nm_to_km)} km radius: {len(planes_to_show)}"
    clear_display()
    display.set_pen(WHITE)
    display.text(text, 0, 0, 240, 2)
    print(text)
    Y = 50
    display.set_pen(WHITE)

    if planes_to_show:
        for plane in planes_to_show:
            type, callsign, reg, altitude, direction, distance = plane
            distance_in_km = round(distance * 1.852)
            altitude = round(altitude / 100)
            display.set_pen(CYAN)
            display.text(type, 0, Y, 80, 2)
            display.set_pen(MAGENTA)
            display.text(callsign, 53, Y, 80, 2)
            display.set_pen(BLUE)
            display.text(f"{altitude:03d}", 135, Y, 80, 2)
            display.set_pen(GREEN)
            display.text(f"{round(direction)}°", 177, Y, 80, 2)
            display.set_pen(YELLOW)
            display.text(f"{distance_in_km}", 222, Y, 80, 2)
            print(f"{type} | {callsign} | {reg} | {distance_in_km} km | {round(direction)}°")
            Y += 20
    display.update()
    print()


async def main():
    await asyncio.gather(show_all_planes(planes_around=planes_around), handle_button(views=views))


if __name__ == '__main__':
    display = PicoGraphics(display=DISPLAY_PICO_DISPLAY, pen_type=PEN_P4, rotate=0)
    display.set_backlight(0.5)
    display.set_font("bitmap8")

    led = RGBLED(6, 7, 8)
    led.set_rgb(0, 0, 0)

    button_a = Pin(12, Pin.IN, Pin.PULL_UP)
    button_b = Pin(13, Pin.IN, Pin.PULL_UP)

    WHITE = display.create_pen(255, 255, 255)
    BLACK = display.create_pen(0, 0, 0)
    GREEN = display.create_pen(0, 255, 0)
    CYAN = display.create_pen(0, 255, 255)
    BLUE = display.create_pen(0, 200, 255)
    MAGENTA = display.create_pen(255, 0, 255)
    YELLOW = display.create_pen(255, 255, 0)

    connect_wifi()

    API = f"https://api.adsb.lol/v2/point/{POS_LAT}/{POS_LONG}/{RADIUS}"
    planes_around = []
    views = (show_all_planes, show_planes_details)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Finished")
