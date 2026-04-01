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
kb = keyboard.Controller()

# Initialize bot
bot = Larky()
PAUSED = False

# Define target colors (hex) and convert to RGB
ALTAR_HEX = "#F25999"
ALTAR = bot.hex_to_rgb(ALTAR_HEX)
BANK_HEX = "#485DFF"
BANK = bot.hex_to_rgb(BANK_HEX)
LADDER_HEX = "#7D00FF"
LADDER = bot.hex_to_rgb(LADDER_HEX)
SHORTCUT_HEX = "#FF00FF"
SHORTCUT = bot.hex_to_rgb(SHORTCUT_HEX)
TILE_HEX = "#C74949"
TILE = bot.hex_to_rgb(TILE_HEX)
ESSENCE_HEX = "#00FFDD"
ESSENCE = bot.hex_to_rgb(ESSENCE_HEX)

# Define images
ESS_IMAGE = "essence"
POUCH_IMAGE = "pouch"
ACHCAPE_IMAGE = "achcape"
DEPOSIT_IMAGE = "deposit"

images_dir = "/home/larken/AutoLark/images"

# Generate full paths once
ess_path = os.path.join(images_dir, f"{ESS_IMAGE}.png")
pouch_path = os.path.join(images_dir, f"{POUCH_IMAGE}.png")
achcape_path = os.path.join(images_dir, f"{ACHCAPE_IMAGE}.png")
deposit_path = os.path.join(images_dir, f"{DEPOSIT_IMAGE}.png")

# Regions
gamebox = bot.gamebox
invent = bot.invent

while True:
    if PAUSED:
        time.sleep(2)
        continue

    pos = bot.wait_for(lambda: bot.find_colors(*gamebox, BANK))
    if pos:
        bot.click_pos(*pos)
    bot.break_delay(chance=1.0, min_delay=1.8, max_delay=4, weight=0.6)
    
    pos = bot.wait_for(lambda: bot.locate_image(gamebox, deposit_path))

    pos = bot.wait_for(lambda: bot.locate_image(gamebox, ess_path))
    if pos:
        bot.click_pos(*pos)
    bot.break_delay(chance=0.38, min_delay=0.8, max_delay=2, weight=1.2)

    # Fill pouch multiple times
    for _ in range(2):
        pos = bot.wait_for(lambda: bot.locate_image(invent, pouch_path))
        if pos:
            bot.click_pos(*pos)
        bot.break_delay(chance=0.63, min_delay=0.3, max_delay=2, weight=0.4)

        pos = bot.wait_for(lambda: bot.locate_image(gamebox, ess_path))
        if pos:
            bot.click_pos(*pos)
        bot.break_delay(chance=0.38, min_delay=0.8, max_delay=2, weight=1.2)

    kb.press(keyboard.Key.esc)
    kb.release(keyboard.Key.esc)
    bot.break_delay(chance=0.83, min_delay=0.6, max_delay=2, weight=0.4)

    pos = bot.wait_for(lambda: bot.locate_image(invent, achcape_path))
    if pos:
        bot.click_pos(*pos)

    pos = bot.wait_for(lambda: bot.find_colors(*gamebox, LADDER))
    if pos:
        bot.click_pos(*pos)
    bot.break_delay(chance=0.98, min_delay=0.8, max_delay=2, weight=1.2)

    pos = bot.wait_for(lambda: bot.find_colors(*gamebox, SHORTCUT))
    if pos:
        bot.click_pos(*pos)
    bot.break_delay(chance=1, min_delay=11, max_delay=12.8, weight=0.4)

    pos = bot.wait_for(lambda: bot.find_colors(*gamebox, TILE))
    if pos:
        bot.click_pos(*pos)

    for _ in range(2):
        pos = bot.wait_for(lambda: bot.find_colors(*gamebox, ALTAR))
        if pos:
            bot.click_pos(*pos)

        bot.wait_for(lambda: bot.find_colors(*invent, ESSENCE) is None)
        print("Essence used...")
        bot.break_delay(chance=0.68, min_delay=0.8, max_delay=2, weight=0.2)

        pos = bot.wait_for(lambda: bot.locate_image(invent, pouch_path))
        if pos:
            bot.click_pos(*pos)
        bot.break_delay(chance=0.88, min_delay=0.8, max_delay=2, weight=0.8)
    
    pos = bot.wait_for(lambda: bot.find_colors(*gamebox, ALTAR))
    if pos:
        bot.click_pos(*pos)

    kb.press(keyboard.Key.shift_l)
    pos = bot.wait_for(lambda: bot.locate_image(invent, achcape_path))
    if pos:
        bot.click_pos(*pos)
    kb.release(keyboard.Key.shift_l)
    bot.break_delay(chance=0.98, min_delay=0.8, max_delay=3, weight=1.2)