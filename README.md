# 📝 KeiaiLAB 블로그 글생성기 by 혁

AI 기반 블로그 제목 분석 및 신규 제목/글 생성 도구

## 🚀 주요 기능

### 🔍 네이버 블로그 분석
- 키워드 기반 네이버 블로그 검색
- 블로그 제목 수집 및 분석
- AI를 활용한 트렌드 분석

### 🎯 AI 기반 제목 생성
- GPT-4를 활용한 매력적인 블로그 제목 생성
- 다양한 분석 유형 지원
- 카테고리별 트렌드 키워드 제공

### ✍️ 블로그 글 생성
- 6가지 글 유형 지원 (정보형, 경험형, 비교형, 튜토리얼형, 트렌드형, 리뷰형)
- 4000자 이상 고품질 콘텐츠 생성
- 맞춤형 추가 요청사항 반영

### 🎨 AI 이미지 생성
- DALL-E 3를 활용한 블로그 이미지 생성
- 글 내용에 맞는 이미지 프롬프트 자동 생성
- 한국적 스타일 및 국가별 특색 반영

## 🖥️ 지원 플랫폼

### 데스크톱 앱 (CustomTkinter)
- Windows/Mac 지원
- 직관적인 GUI 인터페이스
- 다크모드/라이트모드 지원
- 로컬 파일 저장 기능

### 웹 앱 (Flask)
- 반응형 웹 디자인
- 실시간 진행상황 표시
- 브라우저 기반 접근
- 모바일 최적화

## 📋 시스템 요구사항

### 필수 요구사항
- Python 3.8 이상
- 네이버 개발자 API 키
- OpenAI API 키

### 권장 사항
- Python 3.10+
- 8GB 이상 RAM
- 인터넷 연결

## 🛠️ 설치 및 실행

### 1. 저장소 클론
```bash
git clone https://github.com/thebest0225/bloggenerator.git
cd bloggenerator
```

### 2. 환경 설정
```bash
# 가상환경 생성 (권장)
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 또는
venv\Scripts\activate  # Windows

# 의존성 설치
pip install -r requirements.txt
```

### 3. API 키 설정
`.env.example` 파일을 `.env`로 복사하고 API 키를 입력:

```env
NAVER_CLIENT_ID=your_naver_client_id
NAVER_CLIENT_SECRET_KEY=your_naver_secret_key
OPENAI_API_KEY=your_openai_api_key
```

### 4. 애플리케이션 실행

#### 데스크톱 앱
```bash
python desktop_gui.py
```

#### 웹 앱
```bash
python web_app.py
```
브라우저에서 `http://localhost:5000` 접속

## 🔧 API 키 발급 방법

### 네이버 개발자 센터
1. [네이버 개발자 센터](https://developers.naver.com/) 접속
2. 애플리케이션 등록
3. 검색 API 선택
4. Client ID, Client Secret 발급

### OpenAI API
1. [OpenAI Platform](https://platform.openai.com/) 접속
2. API Keys 메뉴에서 새 키 생성
3. 사용량에 따른 과금 주의

## 📦 프로젝트 구조

```
bloggenerator/
├── desktop_gui.py          # 데스크톱 GUI 앱
├── web_app.py             # Flask 웹 앱
├── prompts.py             # AI 프롬프트 관리
├── requirements.txt       # Python 의존성
├── templates/
│   └── index.html        # 웹 앱 템플릿
├── blog_data/            # 생성된 블로그 저장소
├── deploy.sh             # 배포 스크립트
├── docker-compose.yml    # Docker 설정
└── README.md            # 프로젝트 문서
```

## 🌟 주요 특징

### 🎨 사용자 친화적 인터페이스
- 직관적이고 현대적인 디자인
- 단계별 안내와 실시간 피드백
- 다중 탭 구조로 효율적인 워크플로우

### 🧠 고급 AI 분석
- GPT-4 기반 심층 분석
- 트렌드 패턴 인식
- 맞춤형 콘텐츠 생성

### 🔄 자동화된 워크플로우
- 키워드 입력부터 완성된 블로그까지 원클릭
- 이미지 자동 생성 및 저장
- HTML 미리보기 및 복사 기능

## 🚀 배포 옵션

### Docker 배포
```bash
docker-compose up -d
```

### 클라우드 배포
- AWS, GCP, Azure 지원
- 환경변수 기반 설정
- SSL 인증서 자동 설정

## 🤝 기여하기

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다. 자세한 내용은 `LICENSE` 파일을 참조하세요.

## 🙏 감사의 말

- OpenAI GPT-4 API
- 네이버 개발자 센터
- CustomTkinter 라이브러리
- Flask 웹 프레임워크

## 📞 문의

프로젝트 관련 문의사항이 있으시면 GitHub Issues를 통해 연락해 주세요.

---

**Made with ❤️ by 혁** 