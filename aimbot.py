import ctypes
import cv2
import json
import math
import mss
import os
import sys
import time
import numpy as np
import win32api
from termcolor import colored
from ultralytics import YOLO
import torch

# ==================== DÉTECTION GPU (DirectML pour RX 6600) ====================
def get_torch_device():
    if torch.cuda.is_available():
        name = torch.cuda.get_device_name(0)
        print(colored(f"AMD GPU DETECTED → {name} [ROCm/HIP]", "green"))
        return torch.device("cuda")

    try:
        import torch_directml
        if torch_directml.is_available():
            d = torch_directml.device()
            name = torch_directml.device_name(0)
            print(colored(f"AMD GPU via DirectML → {name}", "cyan"))
            return d
    except:
        pass

    print(colored("AUCUNE ACCÉLÉRATION GPU → Mode CPU seulement", "red"))
    return torch.device("cpu")

device = get_torch_device()

# ==================== RÉSOLUTION ====================
screen_x = ctypes.windll.user32.GetSystemMetrics(0) // 2
screen_y = ctypes.windll.user32.GetSystemMetrics(1) // 2

# ==================== PARAMÈTRES ====================
aim_height = 10
fov = 350
confidence = 0.45
use_trigger_bot = True
mouse_method = "ddxoft"  # "win32" si tu n’as pas la DLL

# ==================== MOUSE WIN32 ====================
PUL = ctypes.POINTER(ctypes.c_ulong)
class MouseInput(ctypes.Structure):
    _fields_ = [("dx", ctypes.c_long), ("dy", ctypes.c_long), ("mouseData", ctypes.c_ulong),
                ("dwFlags", ctypes.c_ulong), ("time", ctypes.c_ulong), ("dwExtraInfo", PUL)]
class Input_I(ctypes.Union):
    _fields_ = [("mi", MouseInput)]
class Input(ctypes.Structure):
    _fields_ = [("type", ctypes.c_ulong), ("ii", Input_I)]

extra = ctypes.c_ulong(0)
ii_ = Input_I()

# ==================== AIMBOT ====================
class Aimbot:
    screen = mss.mss()
    mouse_dll = None
    aimbot_status = colored("ENABLED", "green")

    with open("lib/config/config.json", encoding="utf-8") as f:
        sens_config = json.load(f)

    def __init__(self, box_constant=fov, mouse_delay=0.0005):
        self.box_constant = box_constant
        self.mouse_delay = mouse_delay

        print("[INFO] Chargement modèle YOLOv8...")
        self.model = YOLO("lib/best.pt")
        self.model.to(device)

        if str(device) == "privateuseone:0":
            print(colored("ACCÉLÉRATION GPU AMD VIA DIRECTML ACTIVÉE", "cyan"))
        elif device.type == "cuda":
            print(colored("ACCÉLÉRATION GPU AMD VIA ROCm ACTIVÉE", "green"))
        else:
            print(colored("MODE CPU → très lent", "red"))

        # ddxoft
        if mouse_method == "ddxoft":
            dll = os.path.join(os.path.dirname(__file__), "mouse", "dd40605x64.dll")
            if os.path.exists(dll):
                try:
                    Aimbot.mouse_dll = ctypes.WinDLL(dll)
                    if Aimbot.mouse_dll.DD_btn(0) == 1:
                        print(colored("ddxoft chargé → mouvements parfaits", "green"))
                    else:
                        raise
                except:
                    print(colored("ddxoft échoué → win32", "yellow"))
            else:
                print(colored("DLL ddxoft manquante → win32", "yellow"))

        print("\nF1 = Toggle | F2 = Quit\n")

    @staticmethod
    def toggle():
        Aimbot.aimbot_status = colored("DISABLED", "red") if "ENABLED" in Aimbot.aimbot_status else colored("ENABLED", "green")
        print(f"AIMBOT → [{Aimbot.aimbot_status}]")

    def move(self, dx, dy):
        if Aimbot.mouse_dll:
            Aimbot.mouse_dll.DD_movR(int(dx), int(dy))
        else:
            ii_.mi = MouseInput(int(dx), int(dy), 0, 0x0001, 0, ctypes.pointer(extra))
            ctypes.windll.user32.SendInput(1, ctypes.byref(Input(ctypes.c_ulong(0), ii_)), ctypes.sizeof(Input))
        time.sleep(self.mouse_delay)

    def click(self):
        if Aimbot.mouse_dll:
            Aimbot.mouse_dll.DD_btn(1)
            time.sleep(0.001)
            Aimbot.mouse_dll.DD_btn(2)
        else:
            ctypes.windll.user32.mouse_event(0x02, 0, 0, 0, 0)
            time.sleep(0.001)
            ctypes.windll.user32.mouse_event(0x04, 0, 0, 0, 0)

    def start(self):
        box = {'left': screen_x - self.box_constant//2, 'top': screen_y - self.box_constant//2,
               'width': self.box_constant, 'height': self.box_constant}

        print("[INFO] Capture lancée – Bonne chance")
        while True:
            t = time.perf_counter()

            frame = cv2.cvtColor(np.array(self.screen.grab(box)), cv2.COLOR_BGRA2BGR)
            results = self.model(frame, conf=confidence, iou=0.45, device=device, verbose=False)[0]

            best = None
            best_dist = 99999

            for b in results.boxes:
                x1,y1,x2,y2 = map(int, b.xyxy[0])
                h = y2-y1
                hx = (x1+x2)//2
                hy = y1 + h//aim_height
                if x1 < 20 or (x1 < self.box_constant//4 and y2 > self.box_constant*0.8):
                    continue
                dist = math.hypot(hx - self.box_constant//2, hy - self.box_constant//2)
                if dist < best_dist:
                    best_dist = dist
                    best = (hx, hy, x1, y1)

            if best:
                hx, hy, x1, y1 = best
                abs_x = hx + box['left']
                abs_y = hy + box['top']

                cv2.circle(frame, (hx, hy), 8, (0,255,0), -1)
                cv2.line(frame, (hx, hy), (self.box_constant//2, self.box_constant//2), (0,255,255), 2)

                locked = abs(abs_x - screen_x) < 12 and abs(abs_y - screen_y) < 12
                cv2.putText(frame, "LOCKED" if locked else "TARGETING", (x1+10, y1+30), 0.8,
                            (0,255,0) if locked else (0,140,255), 2)

                if locked and use_trigger_bot and win32api.GetKeyState(0x01) not in (-127,-128):
                    self.click()

                if "ENABLED" in Aimbot.aimbot_status and win32api.GetKeyState(0x02) in (-127,-128):
                    self.move(abs_x - screen_x, abs_y - screen_y)

            cv2.putText(frame, f"FPS: {int(1/(time.perf_counter()-t))}", (10,35), cv2.FONT_HERSHEY_DUPLEX, 1, (255,255,255), 2)
            cv2.imshow("Lunar V2 - RX 6600 DirectML", frame)
            if cv2.waitKey(1) & 0xFF == ord('0'):
                break

        cv2.destroyAllWindows()
        self.screen.close()

if __name__ == "__main__":
    print("Lance lunar.py, pas ce fichier !")