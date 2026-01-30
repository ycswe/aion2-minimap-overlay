"""
미니맵 색상 테스트 도구
- 미니맵 영역의 빨간색 픽셀을 분석합니다
"""

import mss
import numpy as np
from collections import Counter

# 미니맵 영역 (minimap_overlay.py와 동일하게 설정)
capture_x = 2200
capture_y = 133
capture_width = 331
capture_height = 221

monitor = {
    "left": capture_x,
    "top": capture_y,
    "width": capture_width,
    "height": capture_height
}

print("미니맵 색상 분석 도구")
print("=" * 50)
print("Enter를 눌러 현재 미니맵을 분석하세요...")
input()

with mss.mss() as sct:
    screenshot = sct.grab(monitor)
    arr = np.asarray(screenshot)

    # BGRA -> RGB
    b = arr[:, :, 0].flatten()
    g = arr[:, :, 1].flatten()
    r = arr[:, :, 2].flatten()

    # 현재 감지 조건: R > 200, R-G > 80, R-B > 80
    print("\n=== 현재 감지 조건 (R>200, R-G>80, R-B>80) ===")
    current_detected = []
    for i in range(len(r)):
        ri, gi, bi = int(r[i]), int(g[i]), int(b[i])
        if ri > 200 and (ri - gi) > 80 and (ri - bi) > 80:
            current_detected.append((ri, gi, bi))

    if current_detected:
        print(f"감지된 픽셀 수: {len(current_detected)}개")
        counter = Counter(current_detected)
        print("감지된 색상:")
        for color, count in counter.most_common(10):
            print(f"  RGB{color}: {count}개 (R-G={color[0]-color[1]}, R-B={color[0]-color[2]})")
    else:
        print("감지된 픽셀 없음")

    # 더 엄격한 조건: R > 220, R-G > 150, R-B > 150
    print("\n=== 더 엄격한 조건 (R>220, R-G>150, R-B>150) ===")
    strict_detected = []
    for i in range(len(r)):
        ri, gi, bi = int(r[i]), int(g[i]), int(b[i])
        if ri > 220 and (ri - gi) > 150 and (ri - bi) > 150:
            strict_detected.append((ri, gi, bi))

    if strict_detected:
        print(f"감지된 픽셀 수: {len(strict_detected)}개")
        counter2 = Counter(strict_detected)
        for color, count in counter2.most_common(10):
            print(f"  RGB{color}: {count}개")
    else:
        print("감지된 픽셀 없음")

print()
print("=" * 50)
input("Enter를 눌러 종료...")
