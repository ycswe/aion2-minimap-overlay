"""
아이온2 미니맵 오버레이
- 우측 상단 미니맵을 캡처해서 화면 중앙에 표시
- ESC로 종료
"""

import sys
import ctypes
import os
import time

try:
    import pygame.mixer as mixer
    mixer.init(frequency=22050, size=-16, channels=1, buffer=512)
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False
    print("pygame 미설치 - 효과음 비활성화 (pip install pygame)")

try:
    import numpy as np
except ImportError:
    print("numpy 설치 필요: pip install numpy")
    sys.exit(1)

try:
    import mss
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
        self.update_interval = 16  # 약 60 FPS

        # 적 감지 설정
        self.enemy_detect_enabled = True  # 적 감지 기능 on/off
        self.red_threshold = 3            # 빨간 픽셀 개수 임계값 (낮춤)
        self.border_width = 3             # 테두리 두께
        self.sound_enabled = True         # 효과음 on/off
        self.sound_file = "e.mp3"         # 효과음 파일
        self.sound_cooldown = 3.0         # 효과음 쿨다운 (초)

        # =========================================

        # 효과음 로드
        self.alert_sound = None
        if PYGAME_AVAILABLE and self.sound_enabled:
            sound_path = os.path.join(os.path.dirname(__file__), self.sound_file)
            if os.path.exists(sound_path):
                self.alert_sound = mixer.Sound(sound_path)
                print(f"효과음 로드: {self.sound_file}")
            else:
                print(f"효과음 파일 없음: {sound_path}")

        self.running = True
        self.sct = mss.mss()

        # 캡처 영역 미리 정의
        self.monitor = {
            "left": self.capture_x,
            "top": self.capture_y,
            "width": self.capture_width,
            "height": self.capture_height
        }

        # 축소된 크기 미리 계산
        self.display_width = int(self.capture_width * self.scale)
        self.display_height = int(self.capture_height * self.scale)
        self.display_size = (self.display_width, self.display_height)

        # 테두리 포함 최종 크기
        self.final_width = self.display_width + self.border_width * 2
        self.final_height = self.display_height + self.border_width * 2

        # 테두리 이미지 미리 생성 (검정/빨강)
        self.border_black = self._create_border_image((0, 0, 0))
        self.border_red = self._create_border_image((255, 50, 50))

        # 윈도우 생성
        self.root = tk.Tk()
        self.root.title("Minimap Overlay")
        self.root.overrideredirect(True)
        self.root.attributes('-topmost', True)
        self.root.attributes('-alpha', self.opacity)

        # 투명 배경 설정 (Windows)
        self.root.configure(bg='black')
        self.root.attributes('-transparentcolor', 'black')

        # 이미지 표시용 라벨
        self.label = tk.Label(self.root, bg='black', borderwidth=0)
        self.label.pack()

        # 초기 위치 설정
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        center_x = screen_width // 2 + self.overlay_offset_x
        center_y = screen_height // 2 + self.overlay_offset_y

        self.root.geometry(f"{self.final_width}x{self.final_height}+{center_x}+{center_y}")

        # 드래그 이동 지원
        self.label.bind('<Button-1>', self.start_drag)
        self.label.bind('<B1-Motion>', self.on_drag)

        # ESC로 종료
        self.root.bind('<Escape>', lambda e: self.quit())

        # 클릭 통과 설정 (Windows)
        self.set_click_through()

        # 이전 경고 상태 (깜빡임 방지)
        self.last_alert_state = False
        self.last_sound_time = 0  # 마지막 효과음 재생 시간

        # 리사이즈용 LUT 미리 계산 (cv2 없이 빠른 리사이즈)
        self._precalc_resize_indices()

        # 캡처 시작
        self.update_capture()

        print("=" * 40)
        print("미니맵 오버레이 실행 중 (60 FPS)")
        print("- ESC: 종료")
        print("- 창을 드래그해서 위치 조정 가능")
        print("=" * 40)

    def _precalc_resize_indices(self):
        """리사이즈용 인덱스 미리 계산"""
        self.row_indices = (np.arange(self.display_height) / self.scale).astype(np.int32)
        self.col_indices = (np.arange(self.display_width) / self.scale).astype(np.int32)
        # 범위 체크
        self.row_indices = np.clip(self.row_indices, 0, self.capture_height - 1)
        self.col_indices = np.clip(self.col_indices, 0, self.capture_width - 1)

    def _create_border_image(self, color):
        """테두리 배경 이미지 미리 생성"""
        arr = np.zeros((self.final_height, self.final_width, 3), dtype=np.uint8)
        arr[:, :] = color
        return arr

    def _fast_resize(self, arr):
        """numpy 인덱싱으로 빠른 리사이즈"""
        return arr[self.row_indices][:, self.col_indices]

    def _add_border_fast(self, img_arr, border_arr):
        """테두리 추가 (numpy로 빠르게)"""
        bw = self.border_width
        result = border_arr.copy()
        result[bw:bw+self.display_height, bw:bw+self.display_width] = img_arr
        return result

    def detect_enemy_fast(self, arr):
        """numpy로 빨간색 감지"""
        # 2픽셀마다 샘플링
        sampled = arr[::2, ::2]

        # BGRA 포맷 - int16으로 변환해서 overflow 방지
        r = sampled[:, :, 2].astype(np.int16)
        g = sampled[:, :, 1].astype(np.int16)
        b = sampled[:, :, 0].astype(np.int16)

        # 적 삼각형: 순수한 빨간색 (R~246, G~32, B~32)
        # R > 210, G < 80, B < 80 (분홍/갈색 제외)
        red_mask = (r > 210) & (g < 80) & (b < 80)

        return np.count_nonzero(red_mask) >= self.red_threshold

    def set_click_through(self):
        """마우스 클릭이 오버레이를 통과하도록 설정"""
        try:
            hwnd = ctypes.windll.user32.GetParent(self.root.winfo_id())
            GWL_EXSTYLE = -20
            WS_EX_LAYERED = 0x80000
            WS_EX_TRANSPARENT = 0x20
            style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
            ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style | WS_EX_LAYERED | WS_EX_TRANSPARENT)
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
            # 캡처 (mss는 이미 매우 빠름)
            screenshot = self.sct.grab(self.monitor)
            arr = np.asarray(screenshot)

            # 적 감지 (원본 배열로 직접)
            enemy_detected = False
            if self.enemy_detect_enabled:
                enemy_detected = self.detect_enemy_fast(arr)

            # BGRA -> RGB 변환 + 리사이즈 (한번에)
            rgb = arr[:, :, [2, 1, 0]]  # 채널 순서만 변경 (복사 최소화)
            resized = self._fast_resize(rgb)

            # 테두리 추가
            if enemy_detected:
                final = self._add_border_fast(resized, self.border_red)
            else:
                final = self._add_border_fast(resized, self.border_black)

            # PIL Image -> PhotoImage (이 부분이 가장 느림, 최적화 한계)
            img = Image.fromarray(final)
            self.photo = ImageTk.PhotoImage(img)
            self.label.configure(image=self.photo)

            # 효과음 재생 (쿨다운 적용)
            if enemy_detected and self.alert_sound:
                current_time = time.time()
                if current_time - self.last_sound_time >= self.sound_cooldown:
                    self.alert_sound.play()
                    self.last_sound_time = current_time
            self.last_alert_state = enemy_detected

        except Exception:
            pass

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
