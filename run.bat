@echo off
echo 의존성 설치 중...
pip install mss Pillow -q

echo 오버레이 실행 중...
python minimap_overlay.py
pause
