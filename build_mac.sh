#!/bin/bash

# Mac용 KeiaiLAB 블로그 글생성기 패키징 스크립트

echo "🍎 Mac용 KeiaiLAB 블로그 글생성기 패키징 시작..."

# 필요한 패키지 설치
echo "📦 필요한 패키지 설치 중..."
pip install pyinstaller customtkinter openai

# 이전 빌드 파일 정리
echo "🧹 이전 빌드 파일 정리 중..."
rm -rf build/
rm -rf dist/
rm -f *.spec

# PyInstaller로 Mac용 앱 생성
echo "🔨 Mac용 앱 빌드 중..."
pyinstaller \
    --onefile \
    --windowed \
    --name "KeiaiLAB_블로그_글생성기_by_혁" \
    --add-data ".env:." \
    --add-data "prompts.py:." \
    --hidden-import customtkinter \
    --hidden-import openai \
    --icon=app_icon.icns \
    desktop_gui.py

# 빌드 결과 확인
if [ -f "dist/KeiaiLAB_블로그_글생성기_by_혁" ]; then
    echo "✅ Mac용 앱이 성공적으로 생성되었습니다!"
    echo "📁 위치: dist/KeiaiLAB_블로그_글생성기_by_혁"
    
    # 실행 권한 부여
    chmod +x "dist/KeiaiLAB_블로그_글생성기_by_혁"
    echo "🔐 실행 권한이 설정되었습니다."
    
    # 파일 크기 확인
    echo "📊 파일 정보:"
    ls -lh "dist/KeiaiLAB_블로그_글생성기_by_혁"
    
else
    echo "❌ 빌드에 실패했습니다."
    exit 1
fi

echo ""
echo "🎉 패키징 완료!"
echo "💡 사용법:"
echo "   1. Finder에서 dist 폴더를 엽니다"
echo "   2. 'KeiaiLAB_블로그_글생성기_by_혁' 파일을 더블클릭하여 실행합니다"
echo "   3. 또는 터미널에서 './dist/KeiaiLAB_블로그_글생성기_by_혁' 명령으로 실행합니다"
echo ""
echo "⚠️  참고사항:"
echo "   - 처음 실행 시 macOS Gatekeeper 경고가 나타날 수 있습니다"
echo "   - 시스템 환경설정 > 보안 및 개인정보보호에서 '확인 없이 열기'를 클릭하세요"
echo "   - .env 파일이 앱 내부에 포함되어 있습니다" 