# Planes Around with Raspberry Pi Pico
This application was previously created in August 2024 in order to improve my programming skills and shows planes in terminal.\
Now I have rewritten the code to run in [MicroPython](https://micropython.org/) on [Raspberry Pi Pico W](https://www.raspberrypi.com/products/raspberry-pi-pico/?variant=raspberry-pi-pico-w) with [Pimoroni Pico Display Pack](https://shop.pimoroni.com/products/pico-display-pack?variant=32368664215635).

It uses [adsb.lol API](https://api.adsb.lol/docs).

## Description
This application displays the planes around you.\
To do this, it connects to the API and, at specified intervals, retrieves information about aircrafts located within a specified radius from the point whose coordinates were entered in the configuration file.\
The default time interval is 30 seconds and the default radius is 5 nautical miles.

## Usage
If you don't have MicroPython on your Pico, the easiest way is to use the [Pimoroni custom version](https://github.com/pimoroni/pimoroni-pico), it already includes the libraries necessary to support displays and other improvements.\
However, make sure which version to use!\
For Pico (1) use [RP2040](https://github.com/pimoroni/pimoroni-pico/releases), for Pico 2 you should use [RP2350](https://github.com/pimoroni/pimoroni-pico-rp2350/releases).

For me, it works with MicroPython [v1.23.0 bugfix 1](https://github.com/pimoroni/pimoroni-pico/releases/tag/v1.23.0-1).

### Configuration
In `wifi_config.py` enter the connection parameters to your Wi-Fi network, such as SSID, key (password) etc.\
In `config.py`:
* enter the latitude and longitude of the point from which the radius will be calculated.
* enter the radius
* enter time interval after which the aircrafts data will be retrieves again

Copy the `main.py`, `wifi_config.py` and `config.py` files to your Raspberry Pi Pico device with a connected display (e.g. using [Thonny](https://thonny.org), [rshell](https://pypi.org/project/rshell) or [mpremote](https://pypi.org/project/mpremote/)).\
After restarting the Pico the program will automatically start from the `main.py` file.

### Disclaimer
I think the code should work with [Pico 2](https://www.raspberrypi.com/products/raspberry-pi-pico-2) as well.\
If you want to use a different display you will have to adapt the code to its resolution etc.

## History
I like watching planes through binoculars/telescope and taking pictures of them, so I wanted to know what was flying around.
