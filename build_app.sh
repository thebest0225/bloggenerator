#!/bin/bash

# macOS .app 번들 생성 스크립트
# 사용법: ./build_app.sh

echo "🍎 KeiaiLAB 블로그 글생성기 .app 번들 생성을 시작합니다..."

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 현재 디렉토리
CURRENT_DIR=$(pwd)
APP_NAME="KeiaiLAB 블로그 글생성기"
BUNDLE_ID="com.keiailab.bloggenerator"
VERSION="1.0.0"

# 가상환경 활성화 (있는 경우)
if [ -d "venv" ]; then
    echo -e "${BLUE}🔄 가상환경을 활성화합니다...${NC}"
    source venv/bin/activate
fi

# 필요한 패키지 설치 확인
echo -e "${BLUE}📦 필요한 패키지를 확인합니다...${NC}"
python -c "import customtkinter, openai, requests" 2>/dev/null
if [ $? -ne 0 ]; then
    echo -e "${YELLOW}⚠️  필요한 패키지를 설치합니다...${NC}"
    pip install -r requirements.txt
fi

# PyInstaller 설치 확인
python -c "import PyInstaller" 2>/dev/null
if [ $? -ne 0 ]; then
    echo -e "${YELLOW}📦 PyInstaller를 설치합니다...${NC}"
    pip install pyinstaller
fi

# 이전 빌드 파일 정리
echo -e "${BLUE}🧹 이전 빌드 파일을 정리합니다...${NC}"
rm -rf build/
rm -rf dist/
rm -f *.spec

# .app 번들 생성
echo -e "${GREEN}🚀 .app 번들을 생성합니다...${NC}"

# PyInstaller 명령어 실행
pyinstaller \
    --name="$APP_NAME" \
    --windowed \
    --onedir \
    --icon=icon.icns \
    --add-data=".env:." \
    --add-data="prompts.py:." \
    --add-data="blog_settings.json:." \
    --hidden-import=PIL \
    --hidden-import=PIL._tkinter_finder \
    --hidden-import=customtkinter \
    --hidden-import=openai \
    --hidden-import=requests \
    --hidden-import=urllib3 \
    --hidden-import=tkinter \
    --hidden-import=tkinter.ttk \
    --clean \
    --noconfirm \
    desktop_gui.py

# 빌드 성공 확인
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ .app 번들 생성이 완료되었습니다!${NC}"
    
    # .app 번들 위치
    APP_PATH="dist/$APP_NAME.app"
    
    # Info.plist 수정
    echo -e "${BLUE}📝 Info.plist를 설정합니다...${NC}"
    PLIST_PATH="$APP_PATH/Contents/Info.plist"
    
    # CFBundleIdentifier 설정
    /usr/libexec/PlistBuddy -c "Set :CFBundleIdentifier $BUNDLE_ID" "$PLIST_PATH" 2>/dev/null || \
    /usr/libexec/PlistBuddy -c "Add :CFBundleIdentifier string $BUNDLE_ID" "$PLIST_PATH"
    
    # CFBundleDisplayName 설정
    /usr/libexec/PlistBuddy -c "Set :CFBundleDisplayName $APP_NAME" "$PLIST_PATH" 2>/dev/null || \
    /usr/libexec/PlistBuddy -c "Add :CFBundleDisplayName string $APP_NAME" "$PLIST_PATH"
    
    # CFBundleVersion 설정
    /usr/libexec/PlistBuddy -c "Set :CFBundleVersion $VERSION" "$PLIST_PATH" 2>/dev/null || \
    /usr/libexec/PlistBuddy -c "Add :CFBundleVersion string $VERSION" "$PLIST_PATH"
    
    # 실행 권한 설정
    echo -e "${BLUE}🔑 실행 권한을 설정합니다...${NC}"
    chmod +x "$APP_PATH/Contents/MacOS/$APP_NAME"
    
    # 파일 크기 확인
    APP_SIZE=$(du -sh "$APP_PATH" | cut -f1)
    
    echo -e "${GREEN}🎉 성공! .app 번들이 생성되었습니다!${NC}"
    echo ""
    echo -e "${BLUE}📁 위치:${NC} $APP_PATH"
    echo -e "${BLUE}📏 크기:${NC} $APP_SIZE"
    echo -e "${BLUE}🆔 Bundle ID:${NC} $BUNDLE_ID"
    echo -e "${BLUE}📋 버전:${NC} $VERSION"
    echo ""
    
    # .app 실행 방법 안내
    echo -e "${YELLOW}🚀 실행 방법:${NC}"
    echo "1. Finder에서 다음 위치로 이동: $APP_PATH"
    echo "2. .app 파일을 더블클릭하여 실행"
    echo "3. 또는 터미널에서: open \"$APP_PATH\""
    echo ""
    
    # Gatekeeper 우회 방법 안내
    echo -e "${YELLOW}🔐 Gatekeeper 오류가 발생하는 경우:${NC}"
    echo "1. 시스템 환경설정 > 보안 및 개인 정보 보호 > 일반"
    echo "2. '확인되지 않은 개발자의 앱 허용' 클릭"
    echo "3. 또는 터미널에서: sudo xattr -r -d com.apple.quarantine \"$APP_PATH\""
    echo ""
    
    # 자동으로 .app 열기 (선택사항)
    read -p "지금 .app을 실행하시겠습니까? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${GREEN}🚀 앱을 실행합니다...${NC}"
        open "$APP_PATH"
    fi
    
else
    echo -e "${RED}❌ .app 번들 생성에 실패했습니다.${NC}"
    echo -e "${YELLOW}💡 다음 사항을 확인해주세요:${NC}"
    echo "1. Python과 필요한 패키지가 모두 설치되어 있는지 확인"
    echo "2. .env 파일과 prompts.py 파일이 존재하는지 확인"
    echo "3. 파일 권한이 올바른지 확인"
    exit 1
fi

echo -e "${GREEN}🎯 .app 번들 생성 완료!${NC}" 