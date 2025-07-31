# 📝 KeiaiLAB 블로그 글생성기 - 웹버전

AI 기반 블로그 제목 분석 및 신규 제목 생성 도구의 웹 애플리케이션 버전입니다.

## 🌟 주요 기능

- 🔍 **네이버 블로그 검색**: 키워드별 블로그 제목 수집 및 분석
- 🧠 **AI 분석**: GPT-4를 활용한 제목 트렌드 분석
- ✨ **제목 생성**: AI 기반 새로운 블로그 제목 생성 (4000자+ 글)
- 🎨 **이미지 생성**: DALL-E 3을 활용한 블로그 이미지 자동 생성
- 📊 **카테고리별 키워드**: 트렌드/재테크/건강 등 8개 카테고리
- 📱 **반응형 디자인**: 모바일/태블릿/데스크톱 최적화

## 🚀 빠른 시작

### 1. 환경 설정

#### 필수 요구사항
- Docker & Docker Compose
- 네이버 블로그 검색 API 키
- OpenAI API 키

#### API 키 발급
1. **네이버 API 키**:
   - [네이버 개발자 센터](https://developers.naver.com/) 접속
   - 애플리케이션 등록 후 Client ID/Secret 발급

2. **OpenAI API 키**:
   - [OpenAI Platform](https://platform.openai.com/) 접속
   - API Keys에서 새 키 생성

### 2. 설치 및 실행

#### 자동 배포 (권장)
```bash
# 1. 저장소 클론
git clone <repository-url>
cd keiailab-blog-generator

# 2. .env 파일 생성
cat > .env << EOF
NAVER_CLIENT_ID=your_naver_client_id
NAVER_CLIENT_SECRET_KEY=your_naver_client_secret
OPENAI_API_KEY=your_openai_api_key
EOF

# 3. 자동 배포 실행
chmod +x deploy.sh
./deploy.sh
```

#### 수동 배포
```bash
# Docker Compose로 실행
docker-compose up -d

# 상태 확인
docker-compose ps

# 로그 확인
docker-compose logs -f
```

### 3. 접속
웹 브라우저에서 `http://localhost:5000` 접속

## 📁 파일 구조

```
keiailab-blog-generator/
├── web_app.py              # Flask 웹 애플리케이션
├── templates/
│   └── index.html          # 메인 웹 페이지
├── prompts.py              # AI 프롬프트 설정
├── requirements_web.txt    # Python 의존성
├── Dockerfile              # Docker 이미지 설정
├── docker-compose.yml      # Docker Compose 설정
├── deploy.sh               # 자동 배포 스크립트
├── .env                    # 환경변수 (직접 생성 필요)
└── README_WEB.md          # 이 문서
```

## 🔧 설정 옵션

### 환경변수 (.env)
```bash
# 네이버 API 설정
NAVER_CLIENT_ID=your_client_id
NAVER_CLIENT_SECRET_KEY=your_client_secret

# OpenAI API 설정
OPENAI_API_KEY=your_openai_api_key

# Flask 설정 (선택사항)
FLASK_ENV=production
SECRET_KEY=your_secret_key
```

### Docker Compose 설정
포트 변경을 원하는 경우 `docker-compose.yml` 파일에서 수정:
```yaml
ports:
  - "8080:5000"  # 로컬 포트를 8080으로 변경
```

## 🌐 외부 서버 배포

### 1. VPS/클라우드 서버 배포

#### AWS EC2 예시
```bash
# EC2 인스턴스에 접속 후
sudo yum update -y
sudo yum install -y docker
sudo service docker start
sudo curl -L "https://github.com/docker/compose/releases/download/1.29.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 프로젝트 파일 업로드 후
./deploy.sh
```

#### 보안 그룹 설정
- 인바운드 규칙에 포트 5000 추가
- HTTP(80), HTTPS(443) 포트도 함께 열기

### 2. 도메인 연결

#### Nginx 리버스 프록시 설정
```nginx
server {
    listen 80;
    server_name yourdomain.com;
    
    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

#### SSL 인증서 설정 (Let's Encrypt)
```bash
sudo certbot --nginx -d yourdomain.com
```

### 3. Docker Swarm/Kubernetes 배포

#### Docker Swarm
```bash
# Swarm 초기화
docker swarm init

# 스택 배포
docker stack deploy -c docker-compose.yml blog-generator
```

#### Kubernetes
```yaml
# k8s-deployment.yaml 생성 후
kubectl apply -f k8s-deployment.yaml
```

## 🛠️ 관리 명령어

### Docker Compose 명령어
```bash
# 서비스 시작
docker-compose up -d

# 서비스 중지
docker-compose down

# 서비스 재시작
docker-compose restart

# 실시간 로그 확인
docker-compose logs -f

# 서비스 상태 확인
docker-compose ps

# 이미지 재빌드
docker-compose build --no-cache
```

### 컨테이너 접속
```bash
# 컨테이너 내부 접속
docker-compose exec blog-generator /bin/bash

# Python 스크립트 실행
docker-compose exec blog-generator python -c "print('Hello')"
```

## 📊 모니터링

### 로그 확인
```bash
# 애플리케이션 로그
docker-compose logs blog-generator

# 실시간 로그 모니터링
docker-compose logs -f --tail=100
```

### 리소스 사용량
```bash
# 컨테이너 리소스 사용량
docker stats

# 시스템 리소스 사용량
top
htop
```

## 🔒 보안 설정

### 1. 환경변수 보안
```bash
# .env 파일 권한 설정
chmod 600 .env

# Docker secrets 사용 (권장)
echo "your_api_key" | docker secret create openai_key -
```

### 2. 방화벽 설정
```bash
# UFW 방화벽 설정
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw enable
```

### 3. HTTPS 강제 적용
```python
# web_app.py에 추가
from flask_talisman import Talisman

app = Flask(__name__)
Talisman(app, force_https=True)
```

## 🐛 문제 해결

### 일반적인 오류

1. **포트 이미 사용 중**
   ```bash
   # 포트 사용 프로세스 확인
   lsof -i :5000
   
   # 프로세스 종료
   kill -9 <PID>
   ```

2. **Docker 권한 오류**
   ```bash
   # 사용자를 docker 그룹에 추가
   sudo usermod -aG docker $USER
   newgrp docker
   ```

3. **API 키 오류**
   - `.env` 파일 내용 확인
   - API 키 유효성 검증
   - 네이버 API 사용량 한도 확인

4. **메모리 부족**
   ```bash
   # 시스템 메모리 확인
   free -h
   
   # Docker 메모리 제한 설정
   docker-compose.yml에 메모리 제한 추가
   ```

### 성능 최적화

1. **워커 프로세스 조정**
   ```bash
   # Dockerfile에서 워커 수 조정
   CMD ["gunicorn", "--workers", "2", ...]  # CPU 코어 수에 맞게 조정
   ```

2. **캐싱 구현**
   ```python
   # Redis 캐싱 추가
   pip install redis flask-caching
   ```

3. **정적 파일 최적화**
   ```bash
   # Nginx로 정적 파일 서빙
   # CSS/JS 파일 압축
   ```

## 📈 확장성

### 수평 확장
```yaml
# docker-compose.yml
version: '3.8'
services:
  blog-generator:
    build: .
    deploy:
      replicas: 3  # 인스턴스 3개로 확장
    ports:
      - "5000-5002:5000"
```

### 로드 밸런서
```yaml
# nginx.conf
upstream blog_app {
    server 127.0.0.1:5000;
    server 127.0.0.1:5001;
    server 127.0.0.1:5002;
}
```

## 💾 백업 및 복원

### 데이터 백업
```bash
# 컨테이너 데이터 백업
docker run --rm -v blog_data:/backup alpine tar czf - /backup > backup.tar.gz
```

### 설정 백업
```bash
# 전체 프로젝트 백업
tar -czf blog-generator-backup.tar.gz \
  web_app.py templates/ prompts.py .env docker-compose.yml
```

## 📞 지원

### 로그 수집
문제 신고 시 다음 정보를 포함해주세요:
- 운영체제 정보
- Docker 버전
- 에러 로그
- .env 파일 내용 (API 키 제외)

### 연락처
- 개발자: 혁 (KeiaiLAB)
- 이메일: [연락처 이메일]
- GitHub: [저장소 URL]

---

## 📄 라이센스

이 프로젝트는 MIT 라이센스 하에 제공됩니다.

## 🙏 기여하기

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

**KeiaiLAB 블로그 글생성기 by 혁** - AI로 더 나은 블로그 콘텐츠를 만들어보세요! 🚀 