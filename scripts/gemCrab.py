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

time.sleep(2)  # Give user time to switch to game window

# Initialize bot
bot = Larky()
PAUSED = False

# Define target colors (hex) and convert to RGB
CRAB_HEX = "#FF00FF"
CRAB = bot.hex_to_rgb(CRAB_HEX)
CAVE_HEX = "#00FFDD"
CAVE = bot.hex_to_rgb(CAVE_HEX)

# Define images
ALCH_IMAGE = "alch"
images_dir = "/home/larken/AutoLark/images"

# Generate full paths once
alch_path = os.path.join(images_dir, f"{ALCH_IMAGE}.png")

# Regions
gamebox = bot.gamebox
invent = bot.invent


while True:
    if PAUSED:
        time.sleep(2)
        continue

    pos = bot.wait_for(lambda: bot.find_colors(*gamebox, CRAB))
    if pos:
        bot.click_pos(*pos)
    
    bot.wait_for(lambda: bot.find_colors(*gamebox, CRAB) is None)
    bot.break_delay(chance=1, min_delay=40, max_delay=100, weight=1)

    pos = bot.find_colors(*gamebox, CAVE)
    if pos:
        bot.click_pos(*pos)
    bot.break_delay(chance=0.1, min_delay=4, max_delay=10, weight=2)
