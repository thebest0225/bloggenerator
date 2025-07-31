#!/bin/bash

# Mac용 KeiaiLAB 블로그 글생성기 환경 설정 스크립트

echo "🍎 Mac용 KeiaiLAB 블로그 글생성기 환경 설정을 시작합니다..."

# Python 버전 확인
echo "🐍 Python 버전 확인 중..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
    echo "✅ Python $PYTHON_VERSION 발견"
else
    echo "❌ Python3가 설치되지 않았습니다."
    echo "Homebrew를 통해 Python을 설치하시겠습니까? (y/n)"
    read -r response
    if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        if ! command -v brew &> /dev/null; then
            echo "Homebrew를 먼저 설치합니다..."
            /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        fi
        brew install python
    else
        echo "Python 설치를 건너뜁니다. 수동으로 설치해주세요."
        exit 1
    fi
fi

# 가상환경 생성 여부 확인
echo ""
echo "🔧 가상환경을 생성하시겠습니까? (권장) (y/n)"
read -r venv_response

if [[ "$venv_response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
    echo "📦 가상환경 생성 중..."
    python3 -m venv venv
    
    echo "✅ 가상환경이 생성되었습니다."
    echo "다음 명령어로 가상환경을 활성화하세요:"
    echo "source venv/bin/activate"
    echo ""
    echo "가상환경을 지금 활성화하고 계속하시겠습니까? (y/n)"
    read -r activate_response
    
    if [[ "$activate_response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        source venv/bin/activate
        echo "✅ 가상환경이 활성화되었습니다."
    fi
fi

# 필요한 패키지 설치
echo "📦 필요한 패키지 설치 중..."
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
else
    echo "requirements.txt 파일이 없습니다. 개별 패키지를 설치합니다..."
    pip install openai>=1.0.0 urllib3>=1.26.0 customtkinter>=5.0.0 pyinstaller>=5.0.0 Pillow>=9.0.0 requests>=2.28.0
fi

echo "✅ 패키지 설치 완료!"

# .env 파일 확인
echo ""
echo "🔐 .env 파일 확인 중..."
if [ -f ".env" ]; then
    echo "✅ .env 파일이 존재합니다."
    echo "API 키가 올바르게 설정되어 있는지 확인해주세요."
else
    echo "⚠️  .env 파일이 없습니다."
    echo ".env 파일을 생성하시겠습니까? (y/n)"
    read -r env_response
    
    if [[ "$env_response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        echo "NAVER_CLIENT_ID=your_naver_client_id" > .env
        echo "NAVER_CLIENT_SECRET_KEY=your_naver_client_secret" >> .env
        echo "OPENAI_API_KEY=your_openai_api_key" >> .env
        echo "✅ .env 파일이 생성되었습니다."
        echo "⚠️  .env 파일을 열어서 실제 API 키로 수정해주세요."
    fi
fi

# 프로그램 실행 테스트
echo ""
echo "🚀 프로그램 실행 테스트를 하시겠습니까? (y/n)"
read -r test_response

if [[ "$test_response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
    echo "프로그램을 실행합니다..."
    python3 desktop_gui.py &
    echo "✅ 프로그램이 실행되었습니다!"
fi

echo ""
echo "🎉 환경 설정이 완료되었습니다!"
echo ""
echo "📋 다음 단계:"
echo "1. .env 파일에 실제 API 키를 입력하세요"
echo "2. 프로그램 테스트: python3 desktop_gui.py"
echo "3. .app 번들 생성: ./build_mac_app.sh"
echo "4. 단일 실행파일 생성: ./build_mac.sh"
echo ""
echo "💡 유용한 명령어:"
echo "- 가상환경 활성화: source venv/bin/activate"
echo "- 가상환경 비활성화: deactivate"
echo "- 패키지 목록 확인: pip list" 