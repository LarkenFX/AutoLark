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
STATION_HEX = "#485DFF"
STATION = bot.hex_to_rgb(STATION_HEX)

# Define images
SALVAGE_IMAGE = "martial"
DEPOSIT_IMAGE = "deposit"
images_dir = "/home/larken/AutoLark/images"

# Generate full paths once
salvage_path = os.path.join(images_dir, f"{SALVAGE_IMAGE}.png")
deposit_path = os.path.join(images_dir, f"{DEPOSIT_IMAGE}.png")

# Regions
gamebox = bot.gamebox
invent = bot.invent

while True:
    if PAUSED:
        time.sleep(2)
        continue
    # --- Step 1: Click the BANK color in gamebox ---
    pos = bot.wait_for(lambda: bot.find_colors(*gamebox, BANK))
    if pos:
        bot.click_pos(*pos)
    bot.break_delay(chance=1.0, min_delay=1.2, max_delay=4, weight=0.6)  # <-- break delay after clicking BANK

    # --- Step 2: Click the DEPOSIT image in gamebox ---
    pos = bot.wait_for(lambda: bot.locate_image(gamebox, deposit_path))
    if pos:
        bot.click_pos(*pos)
    bot.break_delay(chance=0.38, min_delay=0.8, max_delay=2, weight=1.2)

    # --- Step 3: Click the SALVAGE image in gamebox ---
    pos = bot.wait_for(lambda: bot.locate_image(gamebox, salvage_path))
    if pos:
        bot.click_pos(*pos)
    bot.break_delay(chance=0.13, min_delay=0.3, max_delay=2, weight=0.4)
    # --- Step 4: Click the STATION color in gamebox ---
    pos = bot.wait_for(lambda: bot.find_colors(*gamebox, STATION))
    if pos:
        bot.click_pos(*pos)

    # --- Step 5: Wait until SALVAGE image disappears from inventory ---
    bot.wait_for(lambda: bot.locate_image(invent, salvage_path) is None)
    bot.break_delay(chance=0.24, min_delay=0.5, max_delay=15, weight=4)
