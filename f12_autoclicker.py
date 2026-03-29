import tkinter as tk
from tkinter import ttk
import threading
import time
import keyboard
import pyautogui


class F12AutoClicker:
    def __init__(self):
        self.running = False
        self.thread = None

        self.root = tk.Tk()
        self.root.title("F12 Auto Clicker")
        self.root.resizable(False, False)

        frame = ttk.Frame(self.root, padding=20)
        frame.grid()

        # 시간 설정
        ttk.Label(frame, text="분 (Minutes):").grid(row=0, column=0, sticky="w", pady=5)
        self.minutes_var = tk.IntVar(value=5)
        self.minutes_spin = ttk.Spinbox(frame, from_=0, to=999, width=10, textvariable=self.minutes_var)
        self.minutes_spin.grid(row=0, column=1, pady=5)

        ttk.Label(frame, text="초 (Seconds):").grid(row=1, column=0, sticky="w", pady=5)
        self.seconds_var = tk.IntVar(value=2)
        self.seconds_spin = ttk.Spinbox(frame, from_=0, to=59, width=10, textvariable=self.seconds_var)
        self.seconds_spin.grid(row=1, column=1, pady=5)

        # 키 설정
        ttk.Label(frame, text="누를 키 (Key):").grid(row=2, column=0, sticky="w", pady=5)
        self.key_var = tk.StringVar(value="f12")
        self.key_entry = ttk.Entry(frame, textvariable=self.key_var, width=12)
        self.key_entry.grid(row=2, column=1, pady=5)

        # 상태 표시
        self.status_var = tk.StringVar(value="정지됨 (Stopped)")
        self.status_label = ttk.Label(frame, textvariable=self.status_var, foreground="red", font=("", 12, "bold"))
        self.status_label.grid(row=3, column=0, columnspan=2, pady=10)

        # 남은 시간 표시
        self.countdown_var = tk.StringVar(value="")
        ttk.Label(frame, textvariable=self.countdown_var, font=("", 10)).grid(row=4, column=0, columnspan=2)

        # 시작/정지 버튼
        self.toggle_btn = ttk.Button(frame, text="시작 (Start)", command=self.toggle)
        self.toggle_btn.grid(row=5, column=0, columnspan=2, pady=10, sticky="ew")

        ttk.Label(frame, text="F11 키로 시작/정지 토글", foreground="gray").grid(row=6, column=0, columnspan=2)

        # F11 핫키 등록
        keyboard.add_hotkey("f11", self._on_f11)

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.root.mainloop()

    def _on_f11(self):
        self.root.after(0, self.toggle)

    def toggle(self):
        if self.running:
            self.stop()
        else:
            self.start()

    def start(self):
        self.running = True
        self.status_var.set("실행 중 (Running)")
        self.status_label.config(foreground="green")
        self.toggle_btn.config(text="정지 (Stop)")
        self.minutes_spin.config(state="disabled")
        self.seconds_spin.config(state="disabled")
        self.key_entry.config(state="disabled")
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False
        self.status_var.set("정지됨 (Stopped)")
        self.status_label.config(foreground="red")
        self.toggle_btn.config(text="시작 (Start)")
        self.countdown_var.set("")
        self.minutes_spin.config(state="normal")
        self.seconds_spin.config(state="normal")
        self.key_entry.config(state="normal")

    def _loop(self):
        while self.running:
            total = self.minutes_var.get() * 60 + self.seconds_var.get()
            remaining = total
            while remaining > 0 and self.running:
                m, s = divmod(remaining, 60)
                self.countdown_var.set(f"다음 클릭까지: {m:02d}:{s:02d}")
                time.sleep(1)
                remaining -= 1
            if self.running:
                key = self.key_var.get().strip()
                pyautogui.press(key)
                self.countdown_var.set(f"'{key}' 키 눌림!")

    def on_close(self):
        self.running = False
        keyboard.unhook_all()
        self.root.destroy()


if __name__ == "__main__":
    F12AutoClicker()
