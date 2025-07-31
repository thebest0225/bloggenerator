#!/bin/bash

# Mac용 KeiaiLAB 블로그 글생성기 .app 번들 패키징 스크립트

echo "🍎 Mac용 KeiaiLAB 블로그 글생성기 .app 번들 패키징 시작..."

# 필요한 패키지 설치
echo "📦 필요한 패키지 설치 중..."
pip install pyinstaller customtkinter openai

# 이전 빌드 파일 정리
echo "🧹 이전 빌드 파일 정리 중..."
rm -rf build/
rm -rf dist/
rm -f *.spec

# PyInstaller로 Mac용 .app 번들 생성
echo "🔨 Mac용 .app 번들 빌드 중..."
pyinstaller \
    --onedir \
    --windowed \
    --name "KeiaiLAB_블로그_글생성기_by_혁" \
    --add-data ".env:." \
    --add-data "prompts.py:." \
    --hidden-import customtkinter \
    --hidden-import openai \
    --hidden-import PIL \
    --hidden-import PIL.Image \
    --hidden-import urllib3 \
    --clean \
    desktop_gui.py

# 빌드 결과 확인
if [ -d "dist/KeiaiLAB_블로그_글생성기_by_혁.app" ]; then
    echo "✅ Mac용 .app 번들이 성공적으로 생성되었습니다!"
    echo "📁 위치: dist/KeiaiLAB_블로그_글생성기_by_혁.app"
    
    # .app 번들에 실행 권한 부여
    chmod +x "dist/KeiaiLAB_블로그_글생성기_by_혁.app/Contents/MacOS/KeiaiLAB_블로그_글생성기_by_혁"
    echo "🔐 실행 권한이 설정되었습니다."
    
    # 번들 크기 확인
    echo "📊 앱 번들 정보:"
    du -sh "dist/KeiaiLAB_블로그_글생성기_by_혁.app"
    
    # Info.plist 파일에 추가 정보 설정
    echo "📋 Info.plist 설정 중..."
    INFO_PLIST="dist/KeiaiLAB_블로그_글생성기_by_혁.app/Contents/Info.plist"
    
    # Bundle identifier 추가
    /usr/libexec/PlistBuddy -c "Set :CFBundleIdentifier com.keiailab.bloggenerator" "$INFO_PLIST" 2>/dev/null || \
    /usr/libexec/PlistBuddy -c "Add :CFBundleIdentifier string com.keiailab.bloggenerator" "$INFO_PLIST"
    
    # Bundle version 추가
    /usr/libexec/PlistBuddy -c "Set :CFBundleVersion 1.0.0" "$INFO_PLIST" 2>/dev/null || \
    /usr/libexec/PlistBuddy -c "Add :CFBundleVersion string 1.0.0" "$INFO_PLIST"
    
    # Bundle display name 추가
    /usr/libexec/PlistBuddy -c "Set :CFBundleDisplayName KeiaiLAB 블로그 글생성기 by 혁" "$INFO_PLIST" 2>/dev/null || \
    /usr/libexec/PlistBuddy -c "Add :CFBundleDisplayName string 'KeiaiLAB 블로그 글생성기 by 혁'" "$INFO_PLIST"
    
    echo "✅ Info.plist 설정 완료"
    
else
    echo "❌ 빌드에 실패했습니다."
    exit 1
fi

echo ""
echo "🎉 .app 번들 패키징 완료!"
echo "💡 사용법:"
echo "   1. Finder에서 dist 폴더를 엽니다"
echo "   2. 'KeiaiLAB_블로그_글생성기_by_혁.app'을 Applications 폴더로 드래그합니다"
echo "   3. Launchpad에서 앱을 찾아 실행하거나 Finder에서 더블클릭합니다"
echo ""
echo "⚠️  참고사항:"
echo "   - 처음 실행 시 macOS Gatekeeper 경고가 나타날 수 있습니다"
echo "   - 시스템 환경설정 > 보안 및 개인정보보호에서 '확인 없이 열기'를 클릭하세요"
echo "   - .env 파일과 prompts.py가 앱 내부에 포함되어 있습니다"
echo "   - 인터넷 연결이 필요합니다 (OpenAI API, 네이버 API 사용)" 