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
    def smooth_move(x1, y1, x2, y2, steps=None, duration=None):
        dx, dy = x2 - x1, y2 - y1
        dist = math.hypot(dx, dy)

        # --- Step count based on distance
        if steps is None:
            steps = 14 if dist < 40 else 20 if dist < 120 else 30 if dist < 250 else 40

        # --- Duration scaling (fixes fast long moves)
        if duration is None:
            speed_mult = 0.35
            base = steps * random.uniform(0.009, 0.013)
            dist_factor = (dist / 220) ** 0.65
            duration = base * (1 + dist_factor) * speed_mult

        # --- Curve strength (less aggressive on long moves)
        k = 10 + min(dist / 180, 1.5) * 3

        # --- Small perpendicular curve (human arc)
        perp_x = -dy / (dist + 1e-6)
        perp_y = dx / (dist + 1e-6)
        curve_strength = random.uniform(-3, 3) * min(1, dist / 150)

        # --- Optional slight overshoot (only for longer moves)
        overshoot = 0
        if dist > 80 and random.random() < 0.7:
            overshoot = random.uniform(3, 8)

        target_x = x2 + (dx / (dist + 1e-6)) * overshoot
        target_y = y2 + (dy / (dist + 1e-6)) * overshoot

        # --- Main movement
        for i in range(1, steps + 1):
            t = i / steps

            # Sigmoid easing (smooth accel/decel)
            s = 1 / (1 + math.exp(-k * (t - 0.5)))

            # Base path
            mx = x1 + (target_x - x1) * s
            my = y1 + (target_y - y1) * s

            # Add slight curve
            curve = math.sin(t * math.pi) * curve_strength
            mx += perp_x * curve
            my += perp_y * curve

            # Tiny jitter (reduced near end)
            jitter_scale = (1 - t)
            mx += random.uniform(-1.2, 1.2) * jitter_scale
            my += random.uniform(-1.2, 1.2) * jitter_scale

            Larky.move_mouse_abs(mx, my)
            time.sleep(duration / steps)

        # --- Final correction phase (ENSURES EXACT TARGET)
        x_curr, y_curr = Larky.get_mouse_pos()
        dx, dy = x2 - x_curr, y2 - y_curr
        dist = math.hypot(dx, dy)

        if dist > 0:
            micro_steps = 6 if dist < 10 else 10
            micro_duration = 0.04 if dist < 10 else 0.06

            for i in range(1, micro_steps + 1):
                t = i / micro_steps
                s = 1 / (1 + math.exp(-10 * (t - 0.5)))

                mx = x_curr + dx * s
                my = y_curr + dy * s

                Larky.move_mouse_abs(mx, my)
                time.sleep(micro_duration / micro_steps)

    @staticmethod
    def click_pos(x, y, ox=1, oy=2, button='1'):
        x1, y1 = Larky.get_mouse_pos()

        # Move to true target first
        Larky.smooth_move(x1, y1, x, y)

        # Apply small human-like final adjustment
        final_x = x + random.randint(-ox, ox)
        final_y = y + random.randint(-oy, oy)

        Larky.move_mouse_abs(final_x, final_y)

        # Tiny hesitation (very human)
        time.sleep(random.uniform(0.01, 0.03))

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
    def find_colors(left, top, width, height, target_color, tolerance=5):
        with mss.mss() as sct:
            monitor = {"left": left, "top": top, "width": width, "height": height}
            try:
                img = np.array(sct.grab(monitor))
            except mss.exception.ScreenShotError:
                return None
            img = cv2.cvtColor(img, cv2.COLOR_BGRA2RGB)
            # Build mask
            diff = np.abs(img - target_color)
            mask = np.all(diff <= tolerance, axis=2).astype(np.uint8)
            if not np.any(mask):
                return None
            # --- Step 1: isolate largest blob (important for multiple objects)
            num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(mask, connectivity=8)
            if num_labels <= 1:
                return None
            largest = 1 + np.argmax(stats[1:, cv2.CC_STAT_AREA])
            blob = (labels == largest).astype(np.uint8)
            # --- Step 2: distance transform (distance from edge)
            dist = cv2.distanceTransform(blob, cv2.DIST_L2, 5)
            max_dist = dist.max()
            # --- Step 3: handle thin / bad shapes safely
            if max_dist < 2:
                ys, xs = np.where(blob)
                idx = np.random.randint(len(xs))
                return (left + xs[idx], top + ys[idx])
            # --- Step 4: pick from top interior pixels (not just 1 point)
            flat = dist.flatten()
            # Top N deepest pixels (adaptive)
            top_n = min(40, len(flat))
            indices = np.argpartition(flat, -top_n)[-top_n:]
            # Weighted randomness (favor deeper pixels)
            weights = flat[indices]
            weights = weights / (weights.sum() + 1e-6)
            choice = np.random.choice(indices, p=weights)
            y, x = np.unravel_index(choice, dist.shape)
            # --- Step 5: tiny human-like jitter
            x += int(np.random.normal(0, 1.5))
            y += int(np.random.normal(0, 1.5))
            x = np.clip(x, 0, width - 1)
            y = np.clip(y, 0, height - 1)
            return (left + x, top + y)

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

    def find_image(self, region, image_path, threshold=0.8, click=False):
        pos = self.locate_image(region, image_path, threshold)
        if pos and click:
            self.click_pos(*pos)
        return pos
    
    def check_inventory(self, region, image_path, threshold=0.9, dedupe_dist=12):
        with mss.mss() as sct:
            left, top, width, height = region
            monitor = {"left": left, "top": top, "width": width, "height": height}

            screen = np.array(sct.grab(monitor))
            screen_gray = cv2.cvtColor(screen, cv2.COLOR_BGRA2GRAY)

            template = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
            if template is None:
                raise FileNotFoundError(f"Image not found: {image_path}")

            res = cv2.matchTemplate(screen_gray, template, cv2.TM_CCOEFF_NORMED)

            ys, xs = np.where(res >= threshold)
            points = list(zip(xs, ys))

            # --- Deduplicate matches (prevents overcount spam)
            filtered = []
            for (x, y) in points:
                for (fx, fy) in filtered:
                    if abs(x - fx) < dedupe_dist and abs(y - fy) < dedupe_dist:
                        break
                else:
                    filtered.append((x, y))

            return len(filtered)

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

    def invent_check(self, image_path):
        count = self.check_inventory(self.invent, image_path)

        # --- Conservative logic ---
        if count >= 28:
            return True

        # --- Safety net: slightly lower confidence but still likely full
        if count >= 27:
            # double-check quickly to avoid rare false positives
            time.sleep(0.05)
            count2 = self.check_inventory(self.invent, image_path)
            if count2 >= 26:
                return True

        return False
