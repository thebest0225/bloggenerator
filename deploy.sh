#!/bin/bash

# KeiaiLAB 블로그 글생성기 웹버전 배포 스크립트

echo "🌐 KeiaiLAB 블로그 글생성기 웹버전 배포를 시작합니다..."

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 현재 디렉토리
CURRENT_DIR=$(pwd)

# .env 파일 존재 확인
if [ ! -f ".env" ]; then
    echo -e "${RED}❌ .env 파일이 없습니다!${NC}"
    echo -e "${YELLOW}💡 다음 내용으로 .env 파일을 생성해주세요:${NC}"
    echo ""
    echo "NAVER_CLIENT_ID=your_naver_client_id"
    echo "NAVER_CLIENT_SECRET_KEY=your_naver_client_secret"
    echo "OPENAI_API_KEY=your_openai_api_key"
    echo ""
    exit 1
fi

# prompts.py 파일 존재 확인
if [ ! -f "prompts.py" ]; then
    echo -e "${RED}❌ prompts.py 파일이 없습니다!${NC}"
    echo -e "${YELLOW}💡 prompts.py 파일을 현재 디렉토리에 복사해주세요.${NC}"
    exit 1
fi

# Docker 설치 확인
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker가 설치되지 않았습니다.${NC}"
    echo -e "${YELLOW}💡 다음 사이트에서 Docker를 설치해주세요: https://docs.docker.com/get-docker/${NC}"
    exit 1
fi

# Docker Compose 설치 확인
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}❌ Docker Compose가 설치되지 않았습니다.${NC}"
    echo -e "${YELLOW}💡 다음 사이트에서 Docker Compose를 설치해주세요: https://docs.docker.com/compose/install/${NC}"
    exit 1
fi

# 기존 컨테이너 정리
echo -e "${BLUE}🧹 기존 컨테이너를 정리합니다...${NC}"
docker-compose down 2>/dev/null || true

# Docker 이미지 빌드
echo -e "${BLUE}🔨 Docker 이미지를 빌드합니다...${NC}"
docker-compose build

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Docker 이미지 빌드에 실패했습니다.${NC}"
    exit 1
fi

# 컨테이너 시작
echo -e "${GREEN}🚀 웹 애플리케이션을 시작합니다...${NC}"
docker-compose up -d

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ 배포가 완료되었습니다!${NC}"
    echo ""
    echo -e "${BLUE}📋 배포 정보:${NC}"
    echo -e "${BLUE}🌐 웹 주소:${NC} http://localhost:5000"
    echo -e "${BLUE}🔧 관리 명령어:${NC}"
    echo "  - 중지: docker-compose down"
    echo "  - 재시작: docker-compose restart"
    echo "  - 로그 확인: docker-compose logs -f"
    echo "  - 상태 확인: docker-compose ps"
    echo ""
    
    # 컨테이너 상태 확인
    echo -e "${BLUE}📊 컨테이너 상태:${NC}"
    docker-compose ps
    
    echo ""
    echo -e "${GREEN}🎉 웹 브라우저에서 http://localhost:5000 으로 접속하세요!${NC}"
    
    # 자동으로 브라우저 열기 (옵션)
    read -p "지금 브라우저를 열까요? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        if command -v xdg-open &> /dev/null; then
            xdg-open http://localhost:5000
        elif command -v open &> /dev/null; then
            open http://localhost:5000
        elif command -v start &> /dev/null; then
            start http://localhost:5000
        else
            echo -e "${YELLOW}⚠️  브라우저를 자동으로 열 수 없습니다. 수동으로 http://localhost:5000 에 접속해주세요.${NC}"
        fi
    fi
else
    echo -e "${RED}❌ 배포에 실패했습니다.${NC}"
    echo -e "${YELLOW}💡 다음 명령어로 로그를 확인해보세요:${NC}"
    echo "docker-compose logs"
    exit 1
fi

echo -e "${GREEN}🎯 배포 완료!${NC}" 