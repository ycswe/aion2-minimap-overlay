"""
아이온2 미니맵 오버레이
- 우측 상단 미니맵을 캡처해서 화면 중앙에 표시
- ESC로 종료
"""

import sys
import ctypes
from ctypes import wintypes
import threading
import time

try:
    import mss
    import mss.tools
except ImportError:
    print("mss 설치 필요: pip install mss")
    sys.exit(1)

try:
    from PIL import Image, ImageTk
except ImportError:
    print("Pillow 설치 필요: pip install Pillow")
    sys.exit(1)

try:
    import tkinter as tk
except ImportError:
    print("tkinter가 없습니다")
    sys.exit(1)


class MinimapOverlay:
    def __init__(self):
        # ===== 설정 영역 (여기서 조정하세요) =====

        # 캡처할 미니맵 영역
        self.capture_x = 2200      # 좌측 시작점 X
        self.capture_y = 133       # 상단 시작점 Y
        self.capture_width = 331   # 미니맵 너비 (2531-2200)
        self.capture_height = 221  # 미니맵 높이 (354-133)

        # 오버레이 표시 위치 (화면 중앙 기준 오프셋)
        self.overlay_offset_x = 250   # 중앙에서 오른쪽으로 (캐릭터 옆)
        self.overlay_offset_y = -50   # 중앙에서 위로

        # 축소 비율 (0.5 = 50% 크기, 0.7 = 70% 크기)
        self.scale = 0.6

        # 오버레이 투명도 (0.1 ~ 1.0)
        self.opacity = 0.9

        # 업데이트 간격 (밀리초) - 낮을수록 부드럽지만 CPU 사용 증가
        self.update_interval = 33  # 약 30 FPS

        # =========================================

        self.running = True
        self.sct = mss.mss()

        # 윈도우 생성
        self.root = tk.Tk()
        self.root.title("Minimap Overlay")
        self.root.overrideredirect(True)  # 테두리 제거
        self.root.attributes('-topmost', True)  # 항상 위
        self.root.attributes('-alpha', self.opacity)

        # 투명 배경 설정 (Windows)
        self.root.configure(bg='black')
        self.root.attributes('-transparentcolor', 'black')

        # 이미지 표시용 라벨
        self.label = tk.Label(self.root, bg='black', borderwidth=0)
        self.label.pack()

        # 축소된 크기 계산
        self.display_width = int(self.capture_width * self.scale)
        self.display_height = int(self.capture_height * self.scale)

        # 초기 위치 설정
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        center_x = screen_width // 2 + self.overlay_offset_x
        center_y = screen_height // 2 + self.overlay_offset_y

        self.root.geometry(f"{self.display_width}x{self.display_height}+{center_x}+{center_y}")

        # 드래그 이동 지원
        self.label.bind('<Button-1>', self.start_drag)
        self.label.bind('<B1-Motion>', self.on_drag)

        # ESC로 종료
        self.root.bind('<Escape>', lambda e: self.quit())

        # 클릭 통과 설정 (Windows)
        self.set_click_through()

        # 캡처 시작
        self.update_capture()

        print("=" * 40)
        print("미니맵 오버레이 실행 중")
        print("- ESC: 종료")
        print("- 창을 드래그해서 위치 조정 가능")
        print("=" * 40)

    def set_click_through(self):
        """마우스 클릭이 오버레이를 통과하도록 설정"""
        try:
            hwnd = ctypes.windll.user32.GetParent(self.root.winfo_id())

            GWL_EXSTYLE = -20
            WS_EX_LAYERED = 0x80000
            WS_EX_TRANSPARENT = 0x20

            style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
            style = style | WS_EX_LAYERED | WS_EX_TRANSPARENT
            ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style)
        except Exception as e:
            print(f"클릭 통과 설정 실패: {e}")

    def start_drag(self, event):
        self.drag_x = event.x
        self.drag_y = event.y

    def on_drag(self, event):
        x = self.root.winfo_x() + event.x - self.drag_x
        y = self.root.winfo_y() + event.y - self.drag_y
        self.root.geometry(f"+{x}+{y}")

    def update_capture(self):
        if not self.running:
            return

        try:
            # 미니맵 영역 캡처
            monitor = {
                "left": self.capture_x,
                "top": self.capture_y,
                "width": self.capture_width,
                "height": self.capture_height
            }

            screenshot = self.sct.grab(monitor)

            # PIL Image로 변환
            img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")

            # 축소 (LANCZOS로 고품질 리사이즈)
            img = img.resize((self.display_width, self.display_height), Image.LANCZOS)

            # Tkinter용으로 변환
            self.photo = ImageTk.PhotoImage(img)
            self.label.configure(image=self.photo)

        except Exception as e:
            print(f"캡처 오류: {e}")

        # 다음 업데이트 예약
        if self.running:
            self.root.after(self.update_interval, self.update_capture)

    def quit(self):
        self.running = False
        self.root.destroy()

    def run(self):
        self.root.mainloop()


def main():
    print("\n아이온2 미니맵 오버레이")
    print("-" * 40)
    print("시작하기 전에 게임을 실행하세요")
    print("미니맵 위치가 맞지 않으면 스크립트 상단의")
    print("capture_x, capture_y 값을 조정하세요")
    print("-" * 40)

    overlay = MinimapOverlay()
    overlay.run()


if __name__ == "__main__":
    main()
