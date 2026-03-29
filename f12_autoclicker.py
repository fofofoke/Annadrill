import tkinter as tk
from tkinter import ttk
import threading
import time
import serial
import serial.tools.list_ports


class F12AutoClicker:
    def __init__(self):
        self.running = False
        self.thread = None
        self.ser = None

        self.root = tk.Tk()
        self.root.title("F12 Auto Clicker (Arduino)")
        self.root.resizable(False, False)

        frame = ttk.Frame(self.root, padding=20)
        frame.grid()

        # 아두이노 시리얼 포트 선택
        ttk.Label(frame, text="포트 (Port):").grid(row=0, column=0, sticky="w", pady=5)
        self.port_var = tk.StringVar()
        self.port_combo = ttk.Combobox(frame, textvariable=self.port_var, width=18, state="readonly")
        self.port_combo.grid(row=0, column=1, pady=5)
        self.refresh_ports()

        refresh_btn = ttk.Button(frame, text="새로고침", width=8, command=self.refresh_ports)
        refresh_btn.grid(row=0, column=2, padx=(5, 0), pady=5)

        # 연결 버튼
        self.connect_btn = ttk.Button(frame, text="연결 (Connect)", command=self.toggle_connection)
        self.connect_btn.grid(row=1, column=0, columnspan=3, pady=5, sticky="ew")

        self.conn_status_var = tk.StringVar(value="연결 안됨 (Disconnected)")
        ttk.Label(frame, textvariable=self.conn_status_var, foreground="gray").grid(row=2, column=0, columnspan=3)

        ttk.Separator(frame, orient="horizontal").grid(row=3, column=0, columnspan=3, sticky="ew", pady=10)

        # 시간 설정
        ttk.Label(frame, text="분 (Minutes):").grid(row=4, column=0, sticky="w", pady=5)
        self.minutes_var = tk.IntVar(value=5)
        self.minutes_spin = ttk.Spinbox(frame, from_=0, to=999, width=10, textvariable=self.minutes_var)
        self.minutes_spin.grid(row=4, column=1, pady=5)

        ttk.Label(frame, text="초 (Seconds):").grid(row=5, column=0, sticky="w", pady=5)
        self.seconds_var = tk.IntVar(value=2)
        self.seconds_spin = ttk.Spinbox(frame, from_=0, to=59, width=10, textvariable=self.seconds_var)
        self.seconds_spin.grid(row=5, column=1, pady=5)

        # 키 설정
        ttk.Label(frame, text="누를 키 (Key):").grid(row=6, column=0, sticky="w", pady=5)
        self.key_var = tk.StringVar(value="f12")
        self.key_entry = ttk.Entry(frame, textvariable=self.key_var, width=12)
        self.key_entry.grid(row=6, column=1, pady=5)

        # 상태 표시
        self.status_var = tk.StringVar(value="정지됨 (Stopped)")
        self.status_label = ttk.Label(frame, textvariable=self.status_var, foreground="red", font=("", 12, "bold"))
        self.status_label.grid(row=7, column=0, columnspan=3, pady=10)

        # 남은 시간 표시
        self.countdown_var = tk.StringVar(value="")
        ttk.Label(frame, textvariable=self.countdown_var, font=("", 10)).grid(row=8, column=0, columnspan=3)

        # 시작/정지 버튼
        self.toggle_btn = ttk.Button(frame, text="시작 (Start)", command=self.toggle)
        self.toggle_btn.grid(row=9, column=0, columnspan=3, pady=10, sticky="ew")

        ttk.Label(frame, text="F11 키로 시작/정지 토글", foreground="gray").grid(row=10, column=0, columnspan=3)

        # F11 핫키 등록 (tkinter 바인딩 - 창 포커스 필요 없음)
        self.root.bind_all("<F11>", lambda e: self.toggle())

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.root.mainloop()

    def refresh_ports(self):
        ports = [p.device for p in serial.tools.list_ports.comports()]
        self.port_combo["values"] = ports
        if ports:
            self.port_combo.current(0)

    def toggle_connection(self):
        if self.ser and self.ser.is_open:
            self.disconnect()
        else:
            self.connect()

    def connect(self):
        port = self.port_var.get()
        if not port:
            self.conn_status_var.set("포트를 선택하세요!")
            return
        try:
            self.ser = serial.Serial(port, 9600, timeout=2)
            time.sleep(2)  # 아두이노 리셋 대기
            # READY 응답 읽기
            while self.ser.in_waiting:
                self.ser.readline()
            self.conn_status_var.set(f"연결됨: {port}")
            self.connect_btn.config(text="해제 (Disconnect)")
            self.port_combo.config(state="disabled")
        except serial.SerialException as e:
            self.conn_status_var.set(f"연결 실패: {e}")
            self.ser = None

    def disconnect(self):
        if self.running:
            self.stop()
        if self.ser and self.ser.is_open:
            self.ser.close()
        self.ser = None
        self.conn_status_var.set("연결 안됨 (Disconnected)")
        self.connect_btn.config(text="연결 (Connect)")
        self.port_combo.config(state="readonly")

    def send_key(self, key_name):
        """아두이노에 KEY 명령을 시리얼로 전송"""
        if not self.ser or not self.ser.is_open:
            return False
        try:
            cmd = f"KEY {key_name}\n"
            self.ser.write(cmd.encode())
            response = self.ser.readline().decode().strip()
            return response == "OK"
        except serial.SerialException:
            return False

    def toggle(self):
        if self.running:
            self.stop()
        else:
            self.start()

    def start(self):
        if not self.ser or not self.ser.is_open:
            self.status_var.set("먼저 아두이노를 연결하세요!")
            return
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
                success = self.send_key(key)
                if success:
                    self.countdown_var.set(f"'{key}' 키 전송 완료!")
                else:
                    self.countdown_var.set(f"'{key}' 전송 실패!")

    def on_close(self):
        self.running = False
        if self.ser and self.ser.is_open:
            self.ser.close()
        self.root.destroy()


if __name__ == "__main__":
    F12AutoClicker()
