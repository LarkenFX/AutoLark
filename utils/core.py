import subprocess
import sys
import mss
import numpy as np
import cv2
import random
import time
import math
import os

# ==============================
# Config
# ==============================
WINDOW_NAME = "RuneLite"

GAMEBOX = (0, 0, 1025, 822)
INFOBOX = (0, 0, 322, 170)
INVENT  = (1065, 562, 178, 253)

CLICK_DELAY_RANGE = (0.09, 0.13)
COLOR_TOLERANCE = 5

# ==============================
# Larky Class
# ==============================
class Larky:
    def __init__(self, window_name=WINDOW_NAME):
        self.window_name = window_name
        self.win_id = self.get_window_id()
        self.geom = self.get_window_geometry(self.win_id)
        self.gamebox = self.get_abs_region(GAMEBOX)
        self.infobox = self.get_abs_region(INFOBOX)
        self.invent = self.get_abs_region(INVENT)

    # ==============================
    # Helpers
    # ==============================
    @staticmethod
    def run_cmd(cmd):
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        if result.returncode != 0:
            raise RuntimeError(f"{cmd[0]} failed:\n{result.stderr}")
        return result.stdout

    @staticmethod
    def log(msg):
        print(f"[{time.strftime('%H:%M:%S')}] {msg}")

    # ==============================
    # Window Handling
    # ==============================
    def get_window_geometry(self, win_id):
        output = self.run_cmd(["xwininfo", "-id", win_id])
        geom = {}
        for line in output.splitlines():
            line = line.strip()
            if "Absolute upper-left X" in line:
                geom["x"] = int(line.split(":")[1].strip())
            elif "Absolute upper-left Y" in line:
                geom["y"] = int(line.split(":")[1].strip())
            elif line.startswith("Width:"):
                geom["width"] = int(line.split(":")[1].strip())
            elif line.startswith("Height:"):
                geom["height"] = int(line.split(":")[1].strip())
            elif "Map State" in line:
                geom["map_state"] = line.split(":")[1].strip()
        required = ["x", "y", "width", "height"]
        for key in required:
            if key not in geom:
                raise RuntimeError(f"Failed to parse window geometry ({key} missing)")
        return geom

    def get_window_id(self):
        output = self.run_cmd(["xdotool", "search", "--name", self.window_name])
        ids = output.splitlines()
        if not ids:
            sys.exit(f"No window found matching '{self.window_name}'")
        max_area = 0
        chosen_id = None
        for win_id in ids:
            try:
                geom = self.get_window_geometry(win_id)
            except Exception:
                continue
            if geom.get("map_state") != "IsViewable":
                continue
            area = geom["width"] * geom["height"]
            if area > max_area:
                max_area = area
                chosen_id = win_id
        if chosen_id is None:
            sys.exit(f"No visible '{self.window_name}' window found.")
        return chosen_id

    # ==============================
    # Region Conversion
    # ==============================
    def get_abs_region(self, region):
        rx, ry, rw, rh = region
        rx = max(0, rx)
        ry = max(0, ry)
        max_w = self.geom["width"] - rx
        max_h = self.geom["height"] - ry
        rw = max(0, min(rw, max_w))
        rh = max(0, min(rh, max_h))
        x = self.geom["x"] + rx
        y = self.geom["y"] + ry
        return (x, y, rw, rh)

    # ==============================
    # Mouse Utilities
    # ==============================
    @staticmethod
    def get_mouse_pos():
        output = Larky.run_cmd(["xdotool", "getmouselocation", "--shell"])
        loc = {}
        for line in output.splitlines():
            if "=" in line:
                k, v = line.strip().split("=")
                loc[k] = int(v)
        return loc["X"], loc["Y"]

    @staticmethod
    def move_mouse_abs(x, y):
        Larky.run_cmd(["xdotool", "mousemove", str(int(x)), str(int(y))])

    @staticmethod
    def smooth_move(x1, y1, x2, y2, steps=None, duration=None, k=12, jitter=3):
        dx, dy = x2 - x1, y2 - y1
        dist = math.hypot(dx, dy)
        if steps is None:
            steps = 10 if dist < 30 else 18 if dist < 100 else 28 if dist < 200 else 35
        if duration is None:
            duration = steps * random.uniform(0.009, 0.014)
        ox, oy = random.uniform(-jitter, jitter), random.uniform(-jitter, jitter)
        for i in range(1, steps+1):
            t = i / steps
            s = 1 / (1 + math.exp(-k * (t - 0.5)))
            Larky.move_mouse_abs(x1 + dx * s + ox * (1-s), y1 + dy * s + oy * (1-s))
            time.sleep(duration / steps)
        # Micro-correction
        x1c, y1c = Larky.get_mouse_pos()
        dx, dy = x2 - x1c, y2 - y1c
        dist = math.hypot(dx, dy)
        if dist > 1:
            micro_steps = 6 if dist < 10 else 10
            micro_duration = 0.03 if dist < 10 else 0.045
            for i in range(1, micro_steps+1):
                t = i / micro_steps
                s = 1 / (1 + math.exp(-k*(t-0.5)))
                Larky.move_mouse_abs(x1c + dx*s, y1c + dy*s)
                time.sleep(micro_duration/micro_steps)

    @staticmethod
    def click_pos(x, y, ox=3, oy=5, button='1'):
        x1, y1 = Larky.get_mouse_pos()
        x2, y2 = x + ox, y + oy
        Larky.smooth_move(x1, y1, x2, y2, steps=random.randint(16,30), k=random.randint(10,16))
        Larky.run_cmd(["xdotool", "click", button])

    @staticmethod
    def break_delay(chance=0.1, min_delay=0.1, max_delay=15, weight=10):
        if random.random() < chance:
            # Use beta distribution to bias toward 0 (min_sec)
            t = random.betavariate(weight, 1)
            delay = min_delay + t * (max_delay - min_delay)
            time.sleep(delay)

    # ==============================
    # Color / Vision Utilities
    # ==============================
    @staticmethod
    def hex_to_rgb(hex_color):
        hex_color = hex_color.lstrip('#')
        if len(hex_color) != 6:
            raise ValueError(f"Invalid hex color: {hex_color}")
        return int(hex_color[0:2],16), int(hex_color[2:4],16), int(hex_color[4:6],16)

    @staticmethod
    def shuffle_rows(n_rows):
        order = list(range(n_rows))
        swaps = random.randint(1,3)
        for _ in range(swaps):
            i = random.randint(0, n_rows-2)
            j = i+1
            order[i], order[j] = order[j], order[i]
        return order

    @staticmethod
    def find_colors(
        left, top, width, height,
        target_color,
        tolerance=2
    ):
        with mss.mss() as sct:
            monitor = {"left": left, "top": top, "width": width, "height": height}
            try:
                img = np.array(sct.grab(monitor))
            except mss.exception.ScreenShotError:
                return None

            img = cv2.cvtColor(img, cv2.COLOR_BGRA2RGB)

            diff = np.abs(img - target_color)
            mask = np.all(diff <= tolerance, axis=2)

            ys, xs = np.where(mask)

            if len(xs) == 0:
                return None

            # centroid
            cx = np.mean(xs)
            cy = np.mean(ys)

            sigma = min(width, height) * 0.2

            # gaussian sampling
            for _ in range(50):
                x = int(np.random.normal(cx, sigma))
                y = int(np.random.normal(cy, sigma))

                if 0 <= x < width and 0 <= y < height:
                    if mask[y, x]:
                        return (left + x, top + y)

            # fallback (rare)
            idx = np.random.randint(len(xs))
            return (left + xs[idx], top + ys[idx])

    @staticmethod
    def color_exists(region, color, tolerance=COLOR_TOLERANCE):
        return Larky.find_colors(*region, color, tolerance) is not None

    @staticmethod
    def wait_for(condition_fn, timeout=None, interval=0.1):
        start = time.time()
        while True:
            result = condition_fn()
            if result:            # if something truthy returned
                return result     # <-- return the actual value (e.g., coordinates)
            if timeout and (time.time() - start > timeout):
                return None
            time.sleep(interval)

    # ==============================
    # Image Utilities
    # ==============================
    @staticmethod
    def locate_image(region, image_path, threshold=0.8):
        with mss.mss() as sct:
            left, top, width, height = region
            monitor = {"left": left, "top": top, "width": width, "height": height}
            screen = np.array(sct.grab(monitor))
            screen_gray = cv2.cvtColor(screen, cv2.COLOR_BGRA2GRAY)
            template = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
            if template is None:
                raise FileNotFoundError(f"Image not found: {image_path}")
            res = cv2.matchTemplate(screen_gray, template, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, max_loc = cv2.minMaxLoc(res)
            if max_val >= threshold:
                tx, ty = max_loc
                tw, th = template.shape[::-1]
                return (left + tx + tw//2, top + ty + th//2)
            return None

    def find_image(self, region, image_name, threshold=0.8, click=False):
        image_path = os.path.join(".images", f"{image_name}.png")
        pos = self.locate_image(region, image_path, threshold)
        if pos and click:
            self.click_pos(*pos)
        return pos

    # ==============================
    # Inventory Utilities
    # ==============================
    def drop_all(self, region, color, cols, rows, slot_w, slot_h, slot_margin=6):
        start_x, start_y, width, height = region
        row_order = self.shuffle_rows(rows)
        for row in row_order:
            for col in range(cols):
                cx = start_x + col * slot_w + slot_w // 2
                cy = start_y + row * slot_h + slot_h // 2
                left = max(cx - slot_margin, start_x)
                top = max(cy - slot_margin, start_y)
                right = min(cx + slot_margin, start_x + width)
                bottom = min(cy + slot_margin, start_y + height)
                pos = self.find_colors(left, top, right-left, bottom-top, color)
                if pos:
                    self.click_pos(pos[0] + random.randint(-2, 2),
                                   pos[1] + random.randint(-2, 2))
                    time.sleep(random.uniform(*CLICK_DELAY_RANGE))