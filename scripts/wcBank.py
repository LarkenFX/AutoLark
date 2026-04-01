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
BANK_HEX = "#F25999"
BANK = bot.hex_to_rgb(BANK_HEX)
TREES_HEX = "#485DFF"
TREES = bot.hex_to_rgb(TREES_HEX)
IDLE_HEX = "#00FF00"
IDLE = bot.hex_to_rgb(IDLE_HEX)


# Define images
DEPOSIT_IMAGE = "deposit"
IRONWOOD_IMAGE = "ironwood"
images_dir = "/home/larken/AutoLark/images"

# Generate full paths once
deposit_path = os.path.join(images_dir, f"{DEPOSIT_IMAGE}.png")
ironwood_path = os.path.join(images_dir, f"{IRONWOOD_IMAGE}.png")

# Regions
gamebox = bot.gamebox
invent = bot.invent

while True:
    if PAUSED:
        time.sleep(2)
        continue
    # bank
    pos = bot.wait_for(lambda: bot.find_colors(*gamebox, BANK))
    if pos:
        bot.click_pos(*pos)
    bot.break_delay(chance=1.0, min_delay=1.2, max_delay=4, weight=0.6)
    # deposit
    pos = bot.wait_for(lambda: bot.locate_image(gamebox, deposit_path))
    if pos:
        bot.click_pos(*pos)
    bot.break_delay(chance=0.68, min_delay=0.8, max_delay=2, weight=1.2)
    while True:
        # click trees
        pos = bot.wait_for(lambda: bot.find_colors(*gamebox, TREES))
        if pos:
            bot.click_pos(*pos)
        bot.break_delay(chance=1, min_delay=5, max_delay=700, weight=.008)
        # check idle
        bot.wait_for(lambda: bot.find_colors(*gamebox, IDLE) is None)
        if bot.invent_check(ironwood_path):
            bot.break_delay(chance=1, min_delay=.8, max_delay=3700, weight=.008)
            break
