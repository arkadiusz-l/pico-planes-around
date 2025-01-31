import network
from utime import sleep
from time import localtime
import uasyncio as asyncio
import urequests
from pimoroni import RGBLED
from machine import Pin, reset
from picographics import PicoGraphics, DISPLAY_PICO_DISPLAY, PEN_P4
from wifi_config import SSID, KEY, IP, SUBNET, GATEWAY, DNS, MAX_ATTEMPTS, RETRY_DELAY
from config import POS_LAT, POS_LONG, RADIUS, INTERVAL


def change_views(views):
    while True:
        for view in views:
            yield view


async def handle_button(views):
    button_pressed = False
    view_generator = change_views(views=views)
    current_view = next(view_generator)  # generator loads the first in order functions from `Views`
    active_view_task = asyncio.create_task(current_view(planes_around=planes_around))  # runs first view

    while True:
        if not button_pressed:
            if button_a.value() == 0:  # if button pressed
                button_pressed = True

                if active_view_task:
                    active_view_task.cancel()
                    try:
                        await active_view_task
                    except asyncio.CancelledError:
                        pass
                current_view = next(view_generator)  # generator loads the second in order functions from `Views`
                active_view_task = asyncio.create_task(current_view(planes_around=planes_around))  # runs next view from `Views`
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


def connect_wifi(ssid, key, ip=None, subnet=None, gateway=None, dns=None, max_attempts=10, retry_delay=5):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    attempt = 0
    while not wlan.isconnected() and attempt < max_attempts:
        if attempt == MAX_ATTEMPTS // 2:
            print("WLAN interface restart")
            wlan.disconnect()
            wlan.active(False)
            sleep(2)
            wlan.active(True)
        print(f"Connecting to the Wi-Fi... Attempt {attempt + 1}/{max_attempts}")
        try:
            wlan.connect(ssid, key)
        except OSError as e:
            print("Wi-Fi configuration error:", e)
            return
        sleep(retry_delay)
        attempt += 1

    if wlan.isconnected():
        if ip:
            wlan.ifconfig((ip, subnet, gateway, dns))
            print('Successfully connected to the Wi-Fi')
        return
    else:
        print(f"All attempts failed")
        reset_device()


def reset_device():
    print("Resetting Pico...")
    sleep(2)
    reset()


async def show_all_planes(planes_around):
    try:
        while True:
            planes_around.clear()
            new_planes = get_planes(api=API)
            if new_planes:
                for plane in new_planes:
                    type = plane.get('t', 'unk')
                    reg = plane.get('r', 'unk')
                    callsign = plane.get('flight', reg).rstrip()  # if no callsign, shows reg
                    distance = plane.get('unk')  # planes without `dst` receive infinity (float('inf')) in the get_planes () function
                    direction = plane.get('dir', 'unk')
                    altitude = plane.get('alt_baro', None)
                    planes_around.append((type, callsign, reg, altitude, direction, distance))
            show_planes(planes_to_show=planes_around)
            await asyncio.sleep(INTERVAL)
    except asyncio.CancelledError:
        raise  # propagation of the exception to `handle_button()`

async def show_planes_details(planes_around):
    clear_display()
    font_size = 2
    if planes_around:

        def generate_details(plane):
            type, callsign, reg, altitude, direction, distance = plane
            yield f"Type:   {type}", CYAN
            yield f"Callsign:   {callsign}", MAGENTA
            yield f"Reg:   {reg}", WHITE
            yield f"Altitude:   {altitude} ft", GREEN
            yield f"Direction:   {direction}°", CYAN
            yield f"Distance:   {round(distance * 1.852, 1)} km", YELLOW

        plane = planes_around[0]
        start_y = 20
        line_spacing = 20
        for line_index, (text, pen_color) in enumerate(generate_details(plane)):
            y = start_y + line_index * line_spacing
            display.set_pen(pen_color)
            display.text(text, 0, y, 240, font_size)
        display.update()
        print(plane)
    else:
        display.set_pen(MAGENTA)
        display.text("No planes!", 0, 0, 240, font_size)
        display.update()


def get_planes(api):
    data = {}
    planes_all_data = []
    response = None
    try:
        print("Downloading data from API...")
        response = urequests.get(api, timeout=5)
        data = response.json()
        print(f"Data downloaded from API, date: {localtime()}")
    except Exception as e:
        print("An error occurred while connecting to the API:", e)
        connect_wifi(
            ssid=SSID, key=KEY, ip=IP, subnet=SUBNET, gateway=GATEWAY, dns=DNS, max_attempts=MAX_ATTEMPTS,
                     retry_delay=RETRY_DELAY
        )

    finally:
        if response:
            response.close()
            try:
                planes_all_data = data.get('ac', [])
                planes_all_data.sort(key=lambda x: x.get('dst', float('inf')))  # planes without "dst" will be at the end of the list after sorting
            except Exception as e:
                print("An error occurred while processing data from the API:", e)

    return planes_all_data


def show_planes(planes_to_show):
    nm_to_km = RADIUS * 1.852
    header_text = f"Planes\nwithin a {round(nm_to_km)} km radius: {len(planes_to_show)}"
    clear_display()
    display.set_pen(WHITE)
    display.text(header_text, 0, 0, 240, 2)
    print(header_text)

    def generate_display_lines():
        y = 50
        for plane in planes_to_show:
            type, callsign, reg, altitude, direction, distance = plane
            if altitude:
                altitude = round(altitude / 100)
                altitude = f"{altitude:03d}"
            else:
                altitude = 'unk'
            direction_rounded = round(direction)
            distance_in_km = round(distance * 1.852)

            yield type, CYAN, 0, y
            yield callsign, MAGENTA, 56, y
            yield f"{altitude}", BLUE, 136, y
            yield f"{direction_rounded}°", GREEN, 177, y
            yield f"{distance_in_km}", YELLOW, 222, y
            y += 20
            print(f"{type} | {callsign} | {reg} | {altitude} | {direction_rounded}° | {distance_in_km} km")

    for text, pen_color, x, y in generate_display_lines():
        display.set_pen(pen_color)
        display.text(text, x, y, 80, 2)

    display.update()
    print()


async def main():
    await asyncio.gather(handle_button(views=views))


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

    connect_wifi(ssid=SSID, key=KEY, ip=IP, subnet=SUBNET, gateway=GATEWAY, dns=DNS, max_attempts=MAX_ATTEMPTS, retry_delay=RETRY_DELAY)

    API = f"https://api.adsb.lol/v2/point/{POS_LAT}/{POS_LONG}/{RADIUS}"
    planes_around = []
    views = (show_all_planes, show_planes_details)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Finished")
        clear_display()  # only works on IDE-triggered program termination
