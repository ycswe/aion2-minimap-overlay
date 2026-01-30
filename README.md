# Aion2 Minimap Overlay

아이온2 미니맵을 화면 원하는 위치에 오버레이로 표시하는 프로그램입니다.

## 기능

- 우측 상단 미니맵을 캡처하여 원하는 위치에 표시
- 크기 축소 지원 (원본 미니맵 전체를 작게 표시)
- 클릭 통과 (게임 플레이에 방해 없음)
- 드래그로 위치 이동 가능

## 설치

```bash
pip install mss Pillow
```

## 실행

```bash
python minimap_overlay.py
```

또는 `run.bat` 더블클릭

## 설정

`minimap_overlay.py` 파일 상단에서 조정:

```python
# 캡처할 미니맵 영역
self.capture_x = 2200      # 좌측 시작점 X
self.capture_y = 133       # 상단 시작점 Y
self.capture_width = 331   # 미니맵 너비
self.capture_height = 221  # 미니맵 높이

# 오버레이 표시 위치 (화면 중앙 기준 오프셋)
self.overlay_offset_x = 250   # 중앙에서 오른쪽으로
self.overlay_offset_y = -50   # 중앙에서 위로

# 축소 비율 (0.5 = 50%, 1.0 = 원본)
self.scale = 0.6

# 투명도 (0.1 ~ 1.0)
self.opacity = 0.9
```

## 조작

- **ESC**: 종료
- **드래그**: 오버레이 위치 이동

## 요구사항

- Windows
- Python 3.7+
- mss
- Pillow
