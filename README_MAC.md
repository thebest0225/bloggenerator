# 🍎 Mac용 KeiaiLAB 블로그 글생성기 by 혁

Mac 사용자를 위한 설치 및 사용 가이드입니다.

## 📋 요구사항

- **macOS**: 10.14 (Mojave) 이상
- **Python**: 3.8 이상 (패키징 시에만 필요)
- **인터넷 연결**: OpenAI API, 네이버 API 사용

## 🚀 빠른 시작 (이미 빌드된 앱 사용)

1. **앱 다운로드**: `dist/KeiaiLAB_블로그_글생성기_by_혁.app` 파일을 다운로드
2. **앱 설치**: Applications 폴더로 드래그 앤 드롭
3. **첫 실행**: Gatekeeper 경고 시 "시스템 환경설정 > 보안 및 개인정보보호"에서 허용
4. **API 키 설정**: 앱 내부에 .env 파일이 포함되어 있어 별도 설정 불필요

## 🔨 직접 빌드하기

### 1. 환경 준비

```bash
# Python 3.8+ 설치 (Homebrew 사용)
brew install python

# 가상환경 생성 (권장)
python3 -m venv venv
source venv/bin/activate

# 필요한 패키지 설치
pip install pyinstaller customtkinter openai
```

### 2. 소스코드 준비

```bash
# 소스코드 다운로드 후
cd /path/to/project

# 필요한 파일들 확인
ls -la
# 다음 파일들이 있어야 함:
# - desktop_gui.py
# - prompts.py
# - .env
# - build_mac.sh
# - build_mac_app.sh
```

### 3. 패키징 실행

#### 방법 1: 단일 실행파일 생성

```bash
# 스크립트에 실행 권한 부여
chmod +x build_mac.sh

# 빌드 실행
./build_mac.sh
```

#### 방법 2: .app 번들 생성 (권장)

```bash
# 스크립트에 실행 권한 부여
chmod +x build_mac_app.sh

# 빌드 실행
./build_mac_app.sh
```

### 4. 수동 빌드 (고급 사용자)

```bash
# .app 번들 생성
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
```

## 📱 앱 사용법

### 첫 실행

1. **Gatekeeper 우회**:
   - 앱을 처음 실행하면 "확인되지 않은 개발자" 경고가 나타날 수 있습니다
   - 시스템 환경설정 > 보안 및 개인정보보호로 이동
   - "확인 없이 열기" 버튼 클릭

2. **앱 권한**:
   - 네트워크 액세스 권한 허용
   - 파일 저장을 위한 Documents 폴더 접근 권한 허용

### 주요 기능

- **키워드 분석**: 네이버 블로그 데이터 수집 및 AI 분석
- **제목 생성**: AI 기반 매력적인 블로그 제목 생성
- **블로그 글 생성**: 4000-5000자 분량의 고품질 블로그 글 작성
- **이미지 생성**: DALL-E 3 기반 이미지 자동 생성
- **다크모드**: 라이트/다크 모드 전환 지원

## 🔧 문제 해결

### 앱이 실행되지 않을 때

```bash
# 터미널에서 직접 실행하여 오류 확인
/Applications/KeiaiLAB_블로그_글생성기_by_혁.app/Contents/MacOS/KeiaiLAB_블로그_글생성기_by_혁
```

### 권한 문제

```bash
# 실행 권한 부여
chmod +x "/Applications/KeiaiLAB_블로그_글생성기_by_혁.app/Contents/MacOS/KeiaiLAB_블로그_글생성기_by_혁"

# Gatekeeper 우회 (자신의 책임 하에)
sudo spctl --master-disable
```

### API 키 오류

- 앱 내부의 .env 파일에 올바른 API 키가 설정되어 있는지 확인
- 네트워크 연결 상태 확인
- 방화벽 설정으로 인한 차단 여부 확인

## 📁 파일 구조

```
KeiaiLAB_블로그_글생성기_by_혁.app/
├── Contents/
│   ├── Info.plist
│   ├── MacOS/
│   │   └── KeiaiLAB_블로그_글생성기_by_혁
│   └── Resources/
│       ├── .env
│       ├── prompts.py
│       └── [기타 리소스 파일들]
```

## 🔄 업데이트

새 버전으로 업데이트하려면:

1. 기존 앱 삭제: Applications 폴더에서 휴지통으로 이동
2. 새 버전 다운로드 및 설치
3. 첫 실행 시 다시 Gatekeeper 허용 필요

## 💡 팁

- **성능 최적화**: 백그라운드 앱을 최소화하여 AI 생성 속도 향상
- **저장 위치**: 생성된 파일들은 자동으로 Documents/blog_data 폴더에 저장
- **바로가기**: Cmd+Q로 앱 종료, Cmd+W로 창 닫기
- **다중 실행**: 여러 개의 앱 인스턴스 동시 실행 가능

## 🆘 지원

문제가 발생하면:

1. 터미널에서 직접 실행하여 오류 메시지 확인
2. Console.app에서 앱 관련 로그 확인
3. 개발자에게 오류 로그와 함께 문의

---

**개발자**: 혁  
**버전**: 1.0.0  
**최종 업데이트**: 2024년 