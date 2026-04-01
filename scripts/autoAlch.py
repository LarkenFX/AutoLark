import sys
import time
import os
from pynput import keyboard
sys.path.append("/home/larken/AutoLark/utils")  # <-- path to core.py
from core import Larky

def on_press(key):
    global PAUSED
    try:
        if key == keyboard.Key.end:
            PAUSED = not PAUSED
            print("Paused" if PAUSED else "Resumed")
    except AttributeError:
        pass

listener = keyboard.Listener(on_press=on_press)
listener.start()

time.sleep(2)  # Give user time to switch

# Initialize bot
bot = Larky()
PAUSED = False

# Define target colors (hex) and convert to RGB
BANK_HEX = "#F25999"
BANK = bot.hex_to_rgb(BANK_HEX)
STATION_HEX = "#485DFF"
STATION = bot.hex_to_rgb(STATION_HEX)

# Define images
ALCH_IMAGE = "alch"
NOTED_IMAGE = "noted"
RUNEARROW_IMAGE = "runearrow"
RUNEBALL_IMAGE = "runeball"
images_dir = "/home/larken/AutoLark/images"

# Generate full paths once
alch_path = os.path.join(images_dir, f"{ALCH_IMAGE}.png")
noted_path = os.path.join(images_dir, f"{NOTED_IMAGE}.png")
runearrow_path = os.path.join(images_dir, f"{RUNEARROW_IMAGE}.png")
runeball_path = os.path.join(images_dir, f"{RUNEBALL_IMAGE}.png")

# Regions
gamebox = bot.gamebox
invent = bot.invent

items = {
    "notes": noted_path,
    "balls": runeball_path,
    "arrows": runearrow_path
}

while True:
    if PAUSED:
        time.sleep(2)
        continue

    pos = bot.wait_for(lambda: bot.locate_image(invent, alch_path))
    if pos:
        bot.click_pos(*pos)
    bot.break_delay(chance=1.0, min_delay=3.0, max_delay=5.1, weight=0.2)
    
    for name in list(items.keys()):
        if items[name] is None:
            continue

        pos = bot.wait_for(lambda: bot.locate_image(invent, items[name]), timeout=2)
        if pos:
            bot.click_pos(*pos)
            bot.break_delay(chance=0.12, min_delay=1.2, max_delay=4, weight=0.4)
            break
        else:
            items[name] = None  # Mark as unavailable

    # Exit if all items are done
    if all(value is None for value in items.values()):
        break