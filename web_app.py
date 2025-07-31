from flask import Flask, render_template, request, jsonify, session, send_file, send_from_directory, redirect, url_for
from flask_cors import CORS
import urllib.request
import urllib.parse
import urllib.error
import json
import re
import time
import threading
import os
import sys
import tempfile
import shutil
from datetime import datetime
import uuid

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    import requests
    from pytrends.request import TrendReq
    TRENDS_AVAILABLE = True
except ImportError:
    TRENDS_AVAILABLE = False
    print("⚠️ pytrends가 설치되지 않았습니다. 'pip install pytrends requests' 실행하세요.")

try:
    import prompts
    PROMPTS_AVAILABLE = True
except ImportError:
    PROMPTS_AVAILABLE = False

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # 실제 배포시 변경 필요
app.config['SESSION_TYPE'] = 'filesystem'
CORS(app)

# 패스워드 설정
ADMIN_PASSWORD = "0225"

class BlogWebApp:
    def __init__(self):
        self.client_id = None
        self.client_secret = None
        self.openai_api_key = None
        self.load_env_variables()

        # 임시 결과 저장용 (실제 배포시에는 Redis나 DB 사용 권장)
        self.temp_results = {}

    def load_env_variables(self):
        """환경변수 로드"""
        print("🔧 환경변수 로드 시작...")
        
        # 먼저 시스템 환경변수에서 가져오기 (Replit Secrets)
        self.client_id = os.environ.get('NAVER_CLIENT_ID')
        self.client_secret = os.environ.get('NAVER_CLIENT_SECRET_KEY')
        self.openai_api_key = os.environ.get('OPENAI_API_KEY')

        print(f"📋 시스템 환경변수 확인:")
        print(f"  - NAVER_CLIENT_ID: {'있음 (' + self.client_id[:8] + '...)' if self.client_id else '없음'}")
        print(f"  - NAVER_CLIENT_SECRET_KEY: {'있음 (' + self.client_secret[:8] + '...)' if self.client_secret else '없음'}")
        print(f"  - OPENAI_API_KEY: {'있음 (' + self.openai_api_key[:8] + '...)' if self.openai_api_key else '없음'}")

        # 환경변수가 없으면 .env 파일에서 시도
        if not all([self.client_id, self.client_secret, self.openai_api_key]):
            env_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
            print(f"📁 .env 파일 경로: {env_file_path}")

            try:
                with open(env_file_path, 'r', encoding='utf-8') as f:
                    print("📄 .env 파일에서 환경변수 로드 중...")
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            key = key.strip()
                            value = value.strip()

                            if key == 'NAVER_CLIENT_ID' and not self.client_id:
                                self.client_id = value
                                print(f"  ✓ NAVER_CLIENT_ID 로드됨")
                            elif key == 'NAVER_CLIENT_SECRET_KEY' and not self.client_secret:
                                self.client_secret = value
                                print(f"  ✓ NAVER_CLIENT_SECRET_KEY 로드됨")
                            elif key == 'OPENAI_API_KEY' and not self.openai_api_key:
                                self.openai_api_key = value
                                print(f"  ✓ OPENAI_API_KEY 로드됨")
            except FileNotFoundError:
                print(f"❌ .env 파일을 찾을 수 없습니다: {env_file_path}")
                print("💡 Replit Secrets에 다음 키들을 설정해주세요:")
                print("   - NAVER_CLIENT_ID")
                print("   - NAVER_CLIENT_SECRET_KEY") 
                print("   - OPENAI_API_KEY")

        # 최종 로드된 환경변수 상태 출력
        print(f"🔍 최종 환경변수 상태:")
        print(f"  - NAVER_CLIENT_ID: {'✅ 설정됨' if self.client_id else '❌ 설정 필요'}")
        print(f"  - NAVER_CLIENT_SECRET_KEY: {'✅ 설정됨' if self.client_secret else '❌ 설정 필요'}")
        print(f"  - OPENAI_API_KEY: {'✅ 설정됨' if self.openai_api_key else '❌ 설정 필요'}")
        
        if not self.client_id or not self.client_secret:
            print("⚠️ 네이버 API 키가 설정되지 않았습니다. 검색 기능이 작동하지 않습니다.")
        if not self.openai_api_key:
            print("⚠️ OpenAI API 키가 설정되지 않았습니다. AI 분석 기능이 작동하지 않습니다.")

    def search_naver_blog(self, query, display=50, sort='date'):
        """네이버 블로그 검색"""
        if not self.client_id or not self.client_secret:
            raise Exception("네이버 API 키가 설정되지 않았습니다. Secrets에서 NAVER_CLIENT_ID와 NAVER_CLIENT_SECRET_KEY를 확인해주세요.")

        print(f"🔍 네이버 API 호출 시작: {query}")
        print(f"📊 Client ID: {self.client_id[:8]}...")
        print(f"🔐 Client Secret: {self.client_secret[:8]}...")

        enc_text = urllib.parse.quote(query)
        url = f"https://openapi.naver.com/v1/search/blog.json?query={enc_text}&display={display}&sort={sort}"

        request = urllib.request.Request(url)
        request.add_header("X-Naver-Client-Id", str(self.client_id))
        request.add_header("X-Naver-Client-Secret", str(self.client_secret))
        request.add_header("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")

        try:
            print(f"🌐 API URL: {url}")
            response = urllib.request.urlopen(request, timeout=30)
            if response.getcode() == 200:
                response_body = response.read()
                result = json.loads(response_body.decode('utf-8'))
                print(f"✅ API 호출 성공: {result.get('total', 0)}건 검색됨")
                return result
            else:
                error_body = response.read().decode('utf-8') if response else "응답 없음"
                print(f"❌ API 응답 오류: HTTP {response.getcode()}")
                print(f"📝 오류 내용: {error_body}")
                raise Exception(f"네이버 API 응답 오류: HTTP {response.getcode()}")
        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8') if hasattr(e, 'read') else str(e)
            print(f"❌ HTTP 오류: {e.code} - {error_body}")
            if e.code == 401:
                raise Exception("네이버 API 인증 실패. API 키를 확인해주세요.")
            elif e.code == 400:
                raise Exception("잘못된 요청입니다. 검색어를 확인해주세요.")
            else:
                raise Exception(f"네이버 API 오류 (HTTP {e.code}): {error_body}")
        except urllib.error.URLError as e:
            print(f"❌ 네트워크 연결 오류: {e}")
            raise Exception(f"네트워크 연결 오류가 발생했습니다. 인터넷 연결을 확인해주세요.")
        except Exception as e:
            print(f"❌ 예상치 못한 오류: {str(e)}")
            raise Exception(f"API 호출 중 오류 발생: {str(e)}")

    def clean_html_tags(self, text):
        """HTML 태그 제거"""
        clean = re.compile('<.*?>')
        return re.sub(clean, '', text)

    def extract_blog_data(self, search_result):
        """블로그 데이터 추출"""
        if not search_result or 'items' not in search_result:
            return [], []

        titles = []
        descriptions = []

        for item in search_result['items']:
            title = self.clean_html_tags(item.get('title', ''))
            description = self.clean_html_tags(item.get('description', ''))

            if title:
                titles.append(title)
                descriptions.append(description)

        return titles, descriptions

    def analyze_with_gpt(self, titles, descriptions, query, analysis_type='comprehensive'):
        """GPT로 블로그 제목과 본문 내용 종합 분석"""
        if not OPENAI_AVAILABLE:
            raise Exception("OpenAI 라이브러리가 설치되지 않았습니다.")

        if not self.openai_api_key:
            raise Exception("OpenAI API 키가 설정되지 않았습니다.")

        client = OpenAI(api_key=self.openai_api_key)

        print(f"🔍 분석 시작: 제목 {len(titles)}개, 본문 {len(descriptions)}개")
        print(f"📊 분석 유형: {analysis_type}")

        if PROMPTS_AVAILABLE:
            try:
                analysis_types = prompts.get_available_analysis_types()
                analysis_key = None
                for key, config in analysis_types.items():
                    if config['name'] == analysis_type:
                        analysis_key = key
                        break

                if not analysis_key:
                    analysis_key = 'comprehensive'

                system_prompt = prompts.get_system_prompt(analysis_key)
                user_prompt = prompts.create_content_analysis_prompt(query, titles, descriptions, analysis_key)
                print("✅ prompts.py에서 분석 프롬프트 생성 완료")
            except Exception as e:
                print(f"❌ prompts.py 사용 중 오류: {e}")
                system_prompt = "당신은 블로그 콘텐츠 분석 전문가입니다."
                user_prompt = self.create_fallback_content_analysis_prompt(query, titles, descriptions)
        else:
            print("❌ prompts.py 모듈을 사용할 수 없습니다.")
            system_prompt = "당신은 블로그 콘텐츠 분석 전문가입니다."
            user_prompt = self.create_fallback_content_analysis_prompt(query, titles, descriptions)

        print("🚀 OpenAI API 호출 시작 (제목 + 본문 종합 분석)")

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=4000,
            temperature=0.7
        )

        analysis_result = response.choices[0].message.content
        print(f"✅ 제목 + 본문 종합 분석 완료 ({len(analysis_result)}자)")

        return analysis_result

    def create_fallback_content_analysis_prompt(self, query, titles, descriptions):
        """프롬프트 모듈이 없을 때 사용할 기본 분석 프롬프트 - 제목과 본문 종합 분석"""
        content_list = []
        for i, (title, desc) in enumerate(zip(titles, descriptions)):
            # 본문 내용을 더 많이 포함하여 분석의 정확도 향상
            desc_preview = desc[:500] if desc else "본문 내용 없음"
            content_list.append(f"{i+1}. 제목: {title}\n   본문 내용: {desc_preview}{'...' if len(desc) > 500 else ''}")

        return f"""다음은 '{query}' 키워드로 검색한 네이버 블로그의 제목과 본문 내용입니다. 
제목과 본문을 종합적으로 분석하여 깊이 있는 인사이트를 제공해주세요.

=== 블로그 콘텐츠 목록 ({len(titles)}개) ===
{chr(10).join(content_list)}

=== 제목 + 본문 종합 분석 요청 ===

## 1. 콘텐츠 트렌드 및 방향성 분석
- 현재 '{query}' 관련 가장 인기 있는 주제와 접근 방식
- 제목에서 드러나는 독자들의 주요 관심사
- **본문 내용을 통해 파악되는 실제 다뤄지는 세부 주제들**
- **제목과 본문에서 공통으로 나타나는 핵심 키워드와 패턴**
- 시의성 있는 키워드와 트렌드 변화

## 2. 콘텐츠 품질 및 깊이 분석
- **제목과 본문 내용의 일치도 및 정합성 평가**
- 표면적 정보 vs 심화 내용의 비율
- **본문에서 제공하는 실용적 정보의 구체성과 깊이**
- 독자에게 실질적 도움이 되는 콘텐츠의 특징
- **본문에서 다루는 주요 문제점과 해결책의 질**

## 3. 콘텐츠 구조 및 접근 방식 분석
- 효과적인 제목 구조와 본문 전개 패턴
- **본문에서 나타나는 정보 전달 방식 (가이드형, 경험담, 리뷰, 비교분석 등)**
- **본문에서 독자 참여를 유도하는 요소들과 스타일**
- SEO 최적화 관점에서의 키워드 활용 (제목 + 본문)
- **본문에서 사용하는 언어 톤과 독자와의 소통 방식**

## 4. 시장 기회 및 차별화 전략
- **현재 콘텐츠들의 본문 분석을 통한 한계점과 개선 기회**
- **본문에서 다루지 못하고 있는 독자들의 궁금증과 니즈**
- 차별화 가능한 새로운 접근 방식과 콘텐츠 각도
- **본문 분석을 바탕으로 한 경쟁력 있는 콘텐츠 작성 전략**

## 5. 독자 니즈 및 검색 의도 종합 분석
- **제목과 본문을 통해 파악되는 검색자들의 진짜 목적과 기대사항**
- **본문에서 해결하려는 구체적인 문제들과 해결 수준**
- 정보 탐색 단계별 니즈 차이와 만족도
- **본문 내용으로 판단한 독자의 지식 수준과 관심 영역**

## 6. 새로운 블로그 글 작성을 위한 전략적 제안
- **분석된 콘텐츠들과 차별화할 수 있는 독창적 접근법**
- **본문 분석을 통해 발견한 콘텐츠 공백 영역**
- **더 나은 정보 제공을 위한 구체적인 구성과 내용 제안**
- **독자 만족도를 높일 수 있는 실용적 팁과 가이드라인**

각 분석 항목에 대해 실제 제목과 본문 내용을 인용하며 구체적인 예시와 함께 실용적인 인사이트를 제공해주세요. 
특히 본문 내용 분석을 통해 얻은 깊이 있는 통찰을 강조해주세요."""

    def generate_titles_with_gpt(self, analysis_result, query, num_titles=10):
        """새로운 블로그 제목 생성 - 숫자와 제목만 출력"""
        if not OPENAI_AVAILABLE:
            raise Exception("OpenAI 라이브러리가 설치되지 않았습니다.")

        if not self.openai_api_key:
            raise Exception("OpenAI API 키가 설정되지 않았습니다.")

        client = OpenAI(api_key=self.openai_api_key)

        # 현재 시점 정보 추가
        from datetime import datetime
        current_year = datetime.now().year
        next_year = current_year + 1

        # 간단하고 명확한 프롬프트 사용
        system_prompt = f"""당신은 매력적인 블로그 제목을 생성하는 전문가입니다. 
현재는 {current_year}년이며, 시의성 있는 최신 정보를 반영해야 합니다.
반드시 숫자와 제목만 출력하고, 다른 설명이나 분류는 절대 포함하지 마세요."""

        user_prompt = f"""키워드 '{query}'에 대해 {num_titles}개의 매력적인 블로그 제목을 생성해주세요.

🕐 **현재 시점 정보 (매우 중요!)**
- 현재는 {current_year}년입니다
- 전망이나 예측을 언급할 때는 {current_year}년 하반기, {next_year}년, {next_year + 1}년 등 미래 시점을 사용하세요
- 2023년, 2024년 같은 과거 연도는 절대 사용하지 마세요

🚨 **절대 중요한 규칙** 🚨
- 반드시 "숫자. 제목" 형식으로만 출력
- "유형:", "타겟:", "키워드:", "특징:", "설명:" 등 어떤 추가 정보도 절대 금지
- 제목 뒤에 설명이나 분류를 붙이지 마세요
- 오직 제목만 출력하세요

✅ **올바른 예시:**
1. {query} 초보자를 위한 완벽 가이드
2. {query} 실전 활용법 총정리
3. {query}로 성공하는 3가지 방법
4. {current_year}년 최신 {query} 트렌드 분석
5. {next_year}년 {query} 전망과 대비책

❌ **절대 금지 예시:**
1. {query} 초보자를 위한 완벽 가이드
**유형:** 정보 제공형
2. 2024년 {query} 전망 (과거 연도 사용 금지!)

지금 바로 {num_titles}개의 제목을 숫자와 제목만으로 생성해주세요."""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=1500,
            temperature=0.8
        )

        return response.choices[0].message.content

    def generate_blog_content(self, title, keyword, prompt_type, additional_prompt="", min_chars=6000, max_chars=12000, analysis_result=None):
        """SEO 최적화된 블로그 글 생성"""
        # min_chars와 max_chars를 정수로 변환 (문자열로 들어올 경우 대비)
        try:
            min_chars = int(min_chars) if min_chars else 6000
            max_chars = int(max_chars) if max_chars else 12000
        except (ValueError, TypeError):
            min_chars = 6000
            max_chars = 12000
            
        # SEO 최적화를 위한 최소 글자수 설정 (문단별 1500자 × 5문단)
        if min_chars < 7500:  # 5문단 × 1500자 = 7500자 최소
            min_chars = 7500
            print(f"🔍 문단별 1500자 구조를 위해 최소 글자수를 7500자로 설정했습니다.")
        
        # 키워드 밀도 분석을 위한 예상 키워드 개수 계산
        target_keyword_count = max(8, min_chars // 300)  # 300자당 1개 키워드 목표
        
        print(f"🔍 SEO 최적화 목표:")
        print(f"  - 메인 키워드 '{keyword}': {target_keyword_count}회 이상")
        print(f"  - 키워드 밀도: 2-3% 목표")
        print(f"  - LSI 키워드: 15-20개 포함")
        print(f"  - 구조: 도입부(1500자) + 본문3단락(각1500자) + 결론부(1500자) = 최소 7500자")

        print(f"🎯 블로그 글 생성 시작")
        print(f"📝 제목: {title}")
        print(f"🔑 키워드: {keyword}")
        print(f"📊 프롬프트 유형: {prompt_type}")
        print(f"📏 글자수 범위: {min_chars}-{max_chars}자")
        print(f"➕ 추가 프롬프트: {additional_prompt[:100] if additional_prompt else '없음'}")
        print(f"🧠 분석 결과 포함: {'예' if analysis_result else '아니오'}")

        if not OPENAI_AVAILABLE:
            raise Exception("OpenAI 라이브러리가 설치되지 않았습니다.")

        if not self.openai_api_key:
            raise Exception("OpenAI API 키가 설정되지 않았습니다.")

        client = OpenAI(api_key=self.openai_api_key)

        try:
            # 초기 프롬프트 생성
            if PROMPTS_AVAILABLE:
                print("✅ prompts.py 모듈이 사용 가능합니다.")
                try:
                    # 사용 가능한 프롬프트 타입 확인
                    available_prompts = prompts.get_blog_content_prompts()
                    print(f"📋 사용 가능한 프롬프트 타입: {list(available_prompts.keys())}")

                    if prompt_type not in available_prompts:
                        print(f"⚠️ 요청된 프롬프트 타입 '{prompt_type}'이 없습니다. 'informative'로 변경합니다.")
                        prompt_type = 'informative'

                    print(f"🎯 사용할 프롬프트 타입: {prompt_type}")

                    prompt_data = prompts.create_blog_content_prompt(
                        title=title,
                        keyword=keyword,
                        prompt_type=prompt_type,
                        additional_prompt=additional_prompt,
                        min_chars=min_chars,
                        max_chars=max_chars,
                        analysis_result=analysis_result
                    )

                    system_prompt = prompt_data['system_prompt']
                    user_prompt = prompt_data['user_prompt']

                    print("✅ prompts.py에서 프롬프트 생성 완료")
                    print(f"📝 시스템 프롬프트 길이: {len(system_prompt)}자")
                    print(f"📝 사용자 프롬프트 길이: {len(user_prompt)}자")

                except Exception as e:
                    print(f"❌ prompts.py 사용 중 오류 발생: {e}")
                    # Fallback 프롬프트
                    system_prompt, user_prompt = self._create_fallback_prompts(title, keyword, min_chars, max_chars, additional_prompt)

            else:
                print("❌ prompts.py 모듈을 사용할 수 없습니다.")
                # Fallback 프롬프트
                system_prompt, user_prompt = self._create_fallback_prompts(title, keyword, min_chars, max_chars, additional_prompt)

            print("🚀 OpenAI API 호출 시작 (초기 생성)")

            # 구조화된 긴 블로그 글 한 번에 생성 (이어쓰기 없음)
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=15000,  # 토큰 수 증가로 긴 글 생성 지원
                temperature=0.7
            )

            generated_content = response.choices[0].message.content
            char_count = len(generated_content)

            print(f"✅ 구조화된 블로그 글 생성 완료")
            print(f"📏 생성된 글자수: {char_count}자")
            print(f"🎯 목표 달성: {'✅' if char_count >= min_chars else '❌'}")
            
            if char_count >= min_chars:
                print(f"🎉 성공: {char_count}자로 목표 {min_chars}자를 달성했습니다!")
                print(f"📝 구조: 도입부 + 본문3단락 + 결론부 = 총 5문단 구성")
            else:
                print(f"⚠️ 목표 글자수에 미달하였지만 구조화된 글이 완성되었습니다: {char_count}자")
                print(f"💡 다음 번에는 더 상세한 프롬프트를 사용해보세요.")

            # SEO 분석 수행
            seo_analysis = self._analyze_seo_content(generated_content, keyword)
            
            print(f"📊 SEO 분석 결과:")
            print(f"  - 키워드 '{keyword}' 출현 빈도: {seo_analysis['keyword_count']}회")
            print(f"  - 키워드 밀도: {seo_analysis['keyword_density']:.1f}%")
            print(f"  - SEO 점수: {seo_analysis['seo_score']}/100점")
            
            return generated_content

        except Exception as e:
            print(f"❌ 블로그 글 생성 실패: {str(e)}")
            raise e

    

    def _analyze_seo_content(self, content, keyword):
        """생성된 콘텐츠의 SEO 요소 분석"""
        import re
        
        # 키워드 출현 횟수 계산 (대소문자 무시)
        keyword_count = len(re.findall(re.escape(keyword), content, re.IGNORECASE))
        
        # 전체 단어 수 계산
        word_count = len(content.split())
        
        # 키워드 밀도 계산 (%)
        keyword_density = (keyword_count / word_count) * 100 if word_count > 0 else 0
        
        # SEO 점수 계산 (기본 기준)
        seo_score = 0
        
        # 키워드 출현 빈도 점수 (30점)
        if keyword_count >= 5:
            seo_score += min(30, keyword_count * 3)
        
        # 키워드 밀도 점수 (20점) - 2-3%가 이상적
        if 1.5 <= keyword_density <= 4.0:
            seo_score += 20
        elif keyword_density > 0:
            seo_score += 10
        
        # 글 길이 점수 (20점)
        char_count = len(content)
        if char_count >= 6000:
            seo_score += 20
        elif char_count >= 3000:
            seo_score += 15
        elif char_count >= 1500:
            seo_score += 10
        
        # 구조적 요소 점수 (30점)
        if '**' in content:  # 강조 표시
            seo_score += 10
        if content.count('\n\n') >= 3:  # 단락 구분
            seo_score += 10
        if '1.' in content or '2.' in content:  # 리스트 구조
            seo_score += 10
        
        return {
            'keyword_count': keyword_count,
            'keyword_density': keyword_density,
            'char_count': char_count,
            'word_count': word_count,
            'seo_score': min(100, seo_score)
        }
    
    def _create_fallback_prompts(self, title, keyword, min_chars, max_chars, additional_prompt):
        """Fallback 프롬프트 생성"""
        system_prompt = f"""당신은 전문적인 블로그 글 작성자입니다. 

🚨🚨🚨🚨🚨 **문단별 글자수 준수 절대 명령** 🚨🚨🚨🚨🚨
‼️‼️‼️ 각 문단은 반드시 **1500자 이상**으로 작성해야 합니다! ‼️‼️‼️
‼️‼️‼️ 전체 글은 반드시 **한글 기준 {min_chars}자 이상** 작성해야 합니다! ‼️‼️‼️
‼️‼️‼️ 도입부, 본문 각 소제목, 결론부 모두 1500자 이상 필수! ‼️‼️‼️
🔥🔥🔥 1500자 미만 문단은 절대 불허! 반드시 1500자 이상! 🔥🔥🔥

자연스럽고 친근한 톤으로 작성하되, 각 문단의 충분한 분량을 반드시 지켜야 합니다."""

        user_prompt = f"""🎯 **문단별 글자수 기준 글 작성 미션** 🎯

제목: {title}
키워드: {keyword}

🚨🚨🚨🚨🚨 **문단별 글자수 절대 명령** 🚨🚨🚨🚨🚨
‼️‼️‼️ 각 문단은 반드시 **1500자 이상**으로 작성! ‼️‼️‼️
‼️‼️‼️ 전체 글은 반드시 **한글 기준 {min_chars}자 이상** 작성! ‼️‼️‼️
‼️‼️‼️ 최대 {max_chars}자까지 작성 가능! ‼️‼️‼️
🔥🔥🔥 1500자 미만 문단은 절대 불허! 반드시 1500자 이상! 🔥🔥🔥

💪💪💪 **문단별 글자수 절대 기준** 💪💪💪

1. **도입부** (1500자 이상 절대 필수!)
   - 독자의 관심을 끄는 흥미로운 시작
   - 주제 소개와 글의 목적
   - 독자가 얻을 수 있는 가치 제시
   - 개인적인 경험이나 공감 요소 포함
   - 구체적인 사례와 배경 설명 추가

2. **본문 1단락** (1500자 이상 절대 필수!)
   - 핵심 내용의 첫 번째 요소
   - 구체적인 설명과 예시
   - 실제 사례나 경험담 포함
   - 단계별 방법론과 실용적 팁
   - 독자의 상황별 적용 방법

3. **본문 2단락** (1500자 이상 절대 필수!)
   - 핵심 내용의 두 번째 요소
   - 심화된 내용과 추가 인사이트
   - 다양한 관점과 접근법 제시
   - 주의사항과 문제 해결 방법
   - 성공 사례와 실패 사례 비교

4. **결론부** (1500자 이상 절대 필수!)
   - 내용 요약과 핵심 메시지
   - 독자를 위한 마지막 조언
   - 행동 유도와 격려 메시지
   - 실천 방법과 단계별 가이드
   - 해시태그 15-20개 포함

🔥🔥🔥🔥🔥 **극도로 중요한 작성 규칙** 🔥🔥🔥🔥🔥
‼️‼️‼️ 각 문단을 1500자 이상으로 극도로 자세하게! ‼️‼️‼️
‼️‼️‼️ 예시와 경험담을 대량 포함! ‼️‼️‼️
‼️‼️‼️ 감정과 생각을 풍부하게 표현! ‼️‼️‼️
‼️‼️‼️ {min_chars}자 미만이면 더 많은 내용 추가! ‼️‼️‼️
‼️‼️‼️ 글을 중간에 끊지 말고 끝까지! ‼️‼️‼️

## 글 마지막에 반드시 포함:
**해시태그 추천:** (15-20개)
관련 해시태그들을 추천해주세요."""

        if additional_prompt:
            user_prompt += f"\n\n추가 요청사항:\n{additional_prompt}"

        return system_prompt, user_prompt

    def _create_fallback_title_prompt(self, query, analysis_result, num_titles):
        """Fallback 제목 생성 프롬프트"""
        return f"""키워드 '{query}'에 대해 {num_titles}개의 매력적인 블로그 제목을 생성해주세요.

🎯 **제목 생성 요구사항**
- 클릭하고 싶게 만드는 매력적인 제목
- SEO에 최적화된 키워드 포함
- 독자의 호기심을 자극하는 내용
- 다양한 스타일과 접근법 사용

📋 **출력 형식**
반드시 다음 형식으로만 출력해주세요:

1. [첫 번째 제목]
2. [두 번째 제목]
3. [세 번째 제목]
...
{num_titles}. [마지막 제목]

⚠️ **중요한 규칙**
- 각 제목 앞에는 반드시 "숫자. " 형식으로 번호 표시
- 제목 외에 다른 설명이나 분류는 절대 포함하지 말 것
- "유형:", "타겟:", "목적:" 등의 추가 정보는 포함하지 말 것
- 오직 제목만 출력할 것

{f'📊 분석 결과 참고:{chr(10)}{analysis_result[:500]}...' if analysis_result else ''}

지금 바로 {num_titles}개의 제목을 위 형식으로만 생성해주세요."""

    def generate_dall_e_images(self, title, content, keyword, num_images=4):
        """DALL-E 이미지 생성"""
        if not OPENAI_AVAILABLE:
            raise Exception("OpenAI 라이브러리가 설치되지 않았습니다.")

        if not self.openai_api_key:
            raise Exception("OpenAI API 키가 설정되지 않았습니다.")

        client = OpenAI(api_key=self.openai_api_key)

        # 이미지 프롬프트 생성
        prompts_text = self.create_image_prompts(title, content, keyword, num_images)

        generated_images = []

        for i, prompt in enumerate(prompts_text[:num_images]):
            try:
                response = client.images.generate(
                    model="dall-e-3",
                    prompt=prompt,
                    size="1024x1024",
                    quality="standard",
                    n=1
                )

                if response and response.data and len(response.data) > 0:
                    image_url = response.data[0].url
                    generated_images.append({
                        'prompt': prompt,
                        'url': image_url,
                        'index': i+1
                    })

                time.sleep(1)  # API 호출 간격 조절

            except Exception as e:
                print(f"이미지 {i+1} 생성 오류: {str(e)}")
                continue

        return generated_images

    def create_image_prompts(self, title, content, keyword, num_images=4):
        """블로그 내용 기반으로 이미지 생성 프롬프트 생성"""
        try:
            # GPT로 콘텐츠 분류 및 이미지 프롬프트 생성
            client = OpenAI(api_key=self.openai_api_key)

            prompt_request = f"""
다음 블로그 글을 분석하여 이미지 유형을 분류하고, 전문적인 사진 스타일의 DALL-E 프롬프트 {num_images}개를 생성해주세요.

제목: {title}
키워드: {keyword}

블로그 내용:
{content[:2000]}

=== 작업 순서 ===
1단계: 글 내용을 분석하여 주요 이미지 유형을 "인물", "자연", "제품/사물" 중에서 분류
2단계: 분류된 유형에 맞는 전문 사진 템플릿을 적용하여 4개의 다른 프롬프트 생성

=== 유형별 템플릿 ===
[인물 유형]: "Professional photography portrait of {{인물 묘사}}, natural lighting, soft background blur, Canon EOS R5, 85mm lens, realistic skin texture, high resolution, 4K quality"

[자연 유형]: "High-resolution landscape photography of {{자연환경 묘사}}, vivid color grading, cinematic lighting, Sony Alpha 7R IV, 24mm lens, realistic environmental textures, ultra-detailed, 4K quality"

[제품/사물 유형]: "Professional product photography of {{제품 또는 사물 묘사}}, minimalist background, subtle studio lighting, Nikon D850, macro lens, sharp details, realistic textures, ultra-detailed, 4K quality"

=== 프롬프트 생성 규칙 ===
- 각 프롬프트는 블로그 내용의 다른 측면이나 장면을 반영
- 모든 프롬프트는 동일한 템플릿 구조 사용, 내용만 차별화
- 한국적 느낌이나 아시아인 특징 반영 (별도 언급 없으면)
- 영어로 작성, 구체적이고 상세한 묘사 포함

출력 형식:
분류된 유형: [인물/자연/제품사물]
1. [완성된 프롬프트]
2. [완성된 프롬프트]
3. [완성된 프롬프트]
4. [완성된 프롬프트]
"""

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "당신은 전문 사진작가이자 DALL-E 프롬프트 전문가입니다. 블로그 내용을 분석하여 적절한 유형을 분류하고, 고품질의 전문적인 사진 스타일 프롬프트를 생성합니다."},
                    {"role": "user", "content": prompt_request}
                ],
                max_tokens=1500,
                temperature=0.7
            )

            prompts_text = response.choices[0].message.content
            print(f"Generated prompts text: {prompts_text}")

            # 프롬프트 파싱
            prompts = []
            if prompts_text and prompts_text.strip():
                lines = prompts_text.split('\n')
                for line in lines:
                    line = line.strip()
                    # 숫자로 시작하는 프롬프트 라인 찾기
                    if re.match(r'^\d+\.\s*', line):
                        prompt = re.sub(r'^\d+\.\s*', '', line).strip()
                        if prompt and len(prompt) > 20:  # 최소 길이 확인
                            prompts.append(prompt)

            # 생성된 프롬프트가 부족하면 백업 프롬프트 사용
            if len(prompts) < num_images:
                backup_prompts = self.get_backup_professional_prompts(title, keyword, num_images)
                prompts.extend(backup_prompts[len(prompts):])

            return prompts[:num_images]

        except Exception as e:
            print(f"이미지 프롬프트 생성 오류: {str(e)}")
            return self.get_backup_professional_prompts(title, keyword, num_images)

    def get_backup_professional_prompts(self, title, keyword, num_images=4):
        """백업용 전문 사진 스타일 프롬프트"""
        # 키워드 기반으로 유형 추측
        person_keywords = ['사람', '인물', '직업', '생활', '일상', '관계', '가족', '친구', '연인', '아이', '어른', '남성', '여성']
        nature_keywords = ['자연', '산', '바다', '강', '숲', '꽃', '나무', '풍경', '하늘', '구름', '일출', '일몰', '계절', '날씨']
        product_keywords = ['제품', '음식', '요리', '기술', '도구', '장비', '물건', '아이템', '브랜드', '서비스']

        content_type = "제품/사물"  # 기본값
        
        title_lower = title.lower()
        keyword_lower = keyword.lower()
        
        if any(word in title_lower or word in keyword_lower for word in person_keywords):
            content_type = "인물"
        elif any(word in title_lower or word in keyword_lower for word in nature_keywords):
            content_type = "자연"

        if content_type == "인물":
            return [
                f"Professional photography portrait of a smiling Korean person enjoying {keyword}, natural lighting, soft background blur, Canon EOS R5, 85mm lens, realistic skin texture, high resolution, 4K quality",
                f"Professional photography portrait of Korean people discussing {keyword}, natural lighting, soft background blur, Canon EOS R5, 85mm lens, realistic skin texture, high resolution, 4K quality",
                f"Professional photography portrait of a Korean professional working with {keyword}, natural lighting, soft background blur, Canon EOS R5, 85mm lens, realistic skin texture, high resolution, 4K quality",
                f"Professional photography portrait of Korean family members experiencing {keyword} together, natural lighting, soft background blur, Canon EOS R5, 85mm lens, realistic skin texture, high resolution, 4K quality"
            ][:num_images]
        elif content_type == "자연":
            return [
                f"High-resolution landscape photography of Korean natural scenery featuring {keyword}, vivid color grading, cinematic lighting, Sony Alpha 7R IV, 24mm lens, realistic environmental textures, ultra-detailed, 4K quality",
                f"High-resolution landscape photography of beautiful Korean mountains and {keyword}, vivid color grading, cinematic lighting, Sony Alpha 7R IV, 24mm lens, realistic environmental textures, ultra-detailed, 4K quality",
                f"High-resolution landscape photography of Korean traditional garden with {keyword} elements, vivid color grading, cinematic lighting, Sony Alpha 7R IV, 24mm lens, realistic environmental textures, ultra-detailed, 4K quality",
                f"High-resolution landscape photography of Korean coastal area showcasing {keyword}, vivid color grading, cinematic lighting, Sony Alpha 7R IV, 24mm lens, realistic environmental textures, ultra-detailed, 4K quality"
            ][:num_images]
        else:  # 제품/사물
            return [
                f"Professional product photography of premium {keyword} items, minimalist background, subtle studio lighting, Nikon D850, macro lens, sharp details, realistic textures, ultra-detailed, 4K quality",
                f"Professional product photography of modern {keyword} design, minimalist background, subtle studio lighting, Nikon D850, macro lens, sharp details, realistic textures, ultra-detailed, 4K quality",
                f"Professional product photography of elegant {keyword} arrangement, minimalist background, subtle studio lighting, Nikon D850, macro lens, sharp details, realistic textures, ultra-detailed, 4K quality",
                f"Professional product photography of innovative {keyword} concept, minimalist background, subtle studio lighting, Nikon D850, macro lens, sharp details, realistic textures, ultra-detailed, 4K quality"
            ][:num_images]

    def get_realtime_popular_keywords(self):
        """네이버 실시간 인기검색어 가져오기 (대체 방법)"""
        try:
            # DataLab API 대신 블로그 검색 기반으로 인기도 측정
            return self.get_naver_realtime_search()
        except Exception as e:
            print(f"실시간 인기검색어 조회 오류: {e}")
            return self.get_fallback_trending_keywords()

    def process_datalab_result(self, result):
        """DataLab 결과 처리"""
        trending_keywords = []

        if 'results' in result:
            for group in result['results']:
                group_name = group.get('title', '')
                data = group.get('data', [])

                if data:
                    # 최근 데이터 기준으로 정렬
                    latest_data = sorted(data, key=lambda x: x['period'], reverse=True)
                    if latest_data:
                        trending_keywords.append({
                            'category': group_name,
                            'keywords': group.get('keywords', []),
                            'trend_score': latest_data[0]['ratio']
                        })

        return trending_keywords

    def get_fallback_trending_keywords(self):
        """실시간 검색어 API 실패시 대체 트렌딩 키워드"""
        return [
            {'category': '🔥 AI/테크', 'keywords': ['ChatGPT', 'Claude', 'Gemini', 'AI그림', '코딩'], 'trend_score': 95},
            {'category': '💰 재테크', 'keywords': ['주식', '비트코인', '부동산', '금리', '환율'], 'trend_score': 88},
            {'category': '🏃‍♀️ 건강', 'keywords': ['다이어트', '홈트', '필라테스', '단백질', '수면'], 'trend_score': 82},
            {'category': '🍳 요리', 'keywords': ['에어프라이어', '다이어트식단', '간편요리', '베이킹', '도시락'], 'trend_score': 78},
            {'category': '✈️ 여행', 'keywords': ['제주도', '부산여행', '해외여행', '캠핑', '호텔'], 'trend_score': 75}
        ]

    def get_naver_blog_data(self, query, display=20):
        """네이버 블로그 검색 API 호출"""
        if not self.naver_client_id or not self.naver_client_secret:
            raise Exception("네이버 API 키가 설정되지 않았습니다.")

        url = "https://openapi.naver.com/v1/search/blog.json"
        headers = {
            "X-Naver-Client-Id": self.naver_client_id,
            "X-Naver-Client-Secret": self.naver_client_secret
        }
        params = {
            "query": query,
            "display": display,
            "sort": "sim"
        }

        try:
            #Removed import requests since it wasn't being used and was causing import error.
            #import requests
            #response = requests.get(url, headers=headers, params=params)
            #response.raise_for_status()
            #return response.json()
            return None #Returning None as the request part is commented out
        except Exception as e:
            print(f"네이버 API 호출 오류: {str(e)}")
            return None

    def get_google_trending_keywords(self):
        """Google Trends에서 실시간 트렌딩 키워드 가져오기"""
        try:
            if not TRENDS_AVAILABLE:
                return self.get_fallback_google_keywords()
            
            pytrends = TrendReq(hl='ko', tz=540)  # 한국 시간대
            
            # 실시간 트렌드 가져오기
            trending_searches_df = pytrends.trending_searches(pn='south_korea')
            
            if trending_searches_df is not None and not trending_searches_df.empty:
                trending_keywords = []
                for i, keyword in enumerate(trending_searches_df[0].head(10)):
                    trending_keywords.append({
                        'rank': i + 1,
                        'keyword': keyword,
                        'source': 'Google Trends',
                        'category': '🔥 실시간 인기'
                    })
                
                print(f"✅ Google Trends에서 {len(trending_keywords)}개 키워드 수집")
                return trending_keywords
            else:
                return self.get_fallback_google_keywords()
                
        except Exception as e:
            print(f"Google Trends API 오류: {str(e)}")
            return self.get_fallback_google_keywords()
    
    def get_naver_datalab_keywords(self):
        """네이버 DataLab에서 실시간 트렌드 키워드 가져오기"""
        try:
            if not self.client_id or not self.client_secret:
                return self.get_fallback_naver_keywords()
            
            # 네이버 DataLab API 호출
            url = "https://openapi.naver.com/v1/datalab/search"
            headers = {
                "X-Naver-Client-Id": self.client_id,
                "X-Naver-Client-Secret": self.client_secret,
                "Content-Type": "application/json"
            }
            
            # 최근 1주일 인기 키워드 검색
            from datetime import datetime, timedelta
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
            
            # 인기 키워드들로 검색량 비교
            popular_keywords = ['ChatGPT', '다이어트', '부동산', '주식', '여행', '요리', '운동', '영화', '게임', '쇼핑']
            
            body = {
                "startDate": start_date,
                "endDate": end_date,
                "timeUnit": "date",
                "keywordGroups": [{"groupName": keyword, "keywords": [keyword]} for keyword in popular_keywords[:5]]
            }
            
            response = requests.post(url, headers=headers, json=body)
            
            if response.status_code == 200:
                data = response.json()
                naver_keywords = []
                
                for i, group in enumerate(data.get('results', [])):
                    keyword = group.get('title', '')
                    # 최근 검색량 계산
                    recent_data = group.get('data', [])
                    if recent_data:
                        avg_ratio = sum(item['ratio'] for item in recent_data[-3:]) / len(recent_data[-3:])
                        naver_keywords.append({
                            'rank': i + 1,
                            'keyword': keyword,
                            'source': 'Naver DataLab',
                            'category': '📊 검색량 상위',
                            'trend_score': round(avg_ratio, 1)
                        })
                
                print(f"✅ 네이버 DataLab에서 {len(naver_keywords)}개 키워드 수집")
                return naver_keywords
            else:
                print(f"네이버 DataLab API 오류: {response.status_code}")
                return self.get_fallback_naver_keywords()
                
        except Exception as e:
            print(f"네이버 DataLab API 오류: {str(e)}")
            return self.get_fallback_naver_keywords()
    
    def get_fallback_google_keywords(self):
        """Google Trends 실패시 대체 키워드"""
        return [
            {'rank': 1, 'keyword': 'ChatGPT', 'source': 'Google Trends (Fallback)', 'category': '🤖 AI'},
            {'rank': 2, 'keyword': '다이어트', 'source': 'Google Trends (Fallback)', 'category': '💪 건강'},
            {'rank': 3, 'keyword': '부동산', 'source': 'Google Trends (Fallback)', 'category': '🏠 투자'},
            {'rank': 4, 'keyword': '여행', 'source': 'Google Trends (Fallback)', 'category': '✈️ 여행'},
            {'rank': 5, 'keyword': '주식', 'source': 'Google Trends (Fallback)', 'category': '📈 금융'}
        ]
    
    def get_fallback_naver_keywords(self):
        """네이버 DataLab 실패시 대체 키워드"""
        return [
            {'rank': 1, 'keyword': '요리레시피', 'source': 'Naver DataLab (Fallback)', 'category': '🍳 요리'},
            {'rank': 2, 'keyword': '홈트레이닝', 'source': 'Naver DataLab (Fallback)', 'category': '💪 운동'},
            {'rank': 3, 'keyword': '넷플릭스', 'source': 'Naver DataLab (Fallback)', 'category': '🎬 엔터'},
            {'rank': 4, 'keyword': '인테리어', 'source': 'Naver DataLab (Fallback)', 'category': '🏡 홈'},
            {'rank': 5, 'keyword': '사이드잡', 'source': 'Naver DataLab (Fallback)', 'category': '💼 부업'}
        ]



    def get_fallback_popular_keywords(self):
        """API 실패시 대체 인기 키워드"""
        return [
            {'keyword': 'ChatGPT', 'result_count': 50000, 'popularity_score': 95},
            {'keyword': '다이어트', 'result_count': 45000, 'popularity_score': 88},
            {'keyword': '부동산', 'result_count': 40000, 'popularity_score': 82},
            {'keyword': '주식', 'result_count': 38000, 'popularity_score': 78},
            {'keyword': '여행', 'result_count': 35000, 'popularity_score': 75},
            {'keyword': '요리', 'result_count': 32000, 'popularity_score': 72},
            {'keyword': '운동', 'result_count': 30000, 'popularity_score': 68},
            {'keyword': '영화', 'result_count': 28000, 'popularity_score': 65},
            {'keyword': '게임', 'result_count': 25000, 'popularity_score': 62},
            {'keyword': '패션', 'result_count': 22000, 'popularity_score': 58}
        ]

    def get_predefined_categories(self):
        """미리 정의된 카테고리들 반환"""
        return {
            "🔥 트렌드/핫이슈": {
                "keywords": ["ChatGPT", "인공지능", "메타버스", "NFT", "가상화폐", "전기차", "ESG", "구독경제", "MZ세대", "클린뷰티", "비건", "제로웨이스트", "틱톡", "릴스", "숏폼", "AI그림"],
                "description": "최신 화제, 뉴스, 사회적 이슈",
                "color": "linear-gradient(135deg, #ff6b6b, #ee5a24)"
            },
            "💰 재테크/투자": {
                "keywords": ["주식", "부동산", "가상화폐", "비트코인", "투자", "펀드", "적금", "연금", "세금", "절세", "파이어족", "경제독립", "코인", "ETF", "채권", "배당주"],
                "description": "주식, 부동산, 투자 관련 정보",
                "color": "linear-gradient(135deg, #2ecc71, #27ae60)"
            },
            "🏃‍♀️ 건강/피트니스": {
                "keywords": ["다이어트", "홈트레이닝", "요가", "필라테스", "러닝", "헬스", "단백질", "비타민", "수면", "스트레칭", "마라톤", "크로스핏", "PT", "체중감량", "근력운동", "유산소"],
                "description": "운동, 다이어트, 건강관리",
                "color": "linear-gradient(135deg, #3498db, #2980b9)"
            },
            "🍳 요리/레시피": {
                "keywords": ["에어프라이어", "홈쿡", "다이어트식단", "간편요리", "베이킹", "비건요리", "키토식단", "도시락", "브런치", "디저트", "발효음식", "한식", "양식", "중식", "일식", "분식"],
                "description": "음식, 요리법, 맛집 정보",
                "color": "linear-gradient(135deg, #f39c12, #e67e22)"
            },
            "✈️ 여행/관광": {
                "keywords": ["제주도", "부산", "강릉", "경주", "전주", "해외여행", "캠핑", "글램핑", "호텔", "펜션", "배낭여행", "패키지여행", "일본여행", "유럽여행", "동남아여행", "국내여행"],
                "description": "국내외 여행, 명소, 숙박",
                "color": "linear-gradient(135deg, #9b59b6, #8e44ad)"
            },
            "🎮 취미/엔터": {
                "keywords": ["독서", "영화", "게임", "드라마", "웹툰", "음악", "그림", "사진", "넷플릭스", "유튜브", "스트리밍", "OTT", "애니메이션", "K팝", "드라마추천", "영화추천"],
                "description": "게임, 영화, 드라마, 음악",
                "color": "linear-gradient(135deg, #e74c3c, #c0392b)"
            },
            "👔 비즈니스/마케팅": {
                "keywords": ["창업", "부업", "마케팅", "브랜딩", "SNS마케팅", "유튜브", "블로그", "온라인쇼핑", "이커머스", "스타트업", "프리랜서", "사이드잡", "디지털마케팅", "광고", "콘텐츠마케팅", "인플루언서"],
                "description": "창업, 마케팅, 온라인 사업",
                "color": "linear-gradient(135deg, #34495e, #2c3e50)"
            },
            "🏠 라이프스타일": {
                "keywords": ["인테리어", "정리정돈", "미니멀라이프", "가드닝", "반려동물", "육아", "교육", "패션", "뷰티", "스킨케어", "홈데코", "살림", "청소", "수납", "홈카페", "플랜테리어"],
                "description": "인테리어, 패션, 일상",
                "color": "linear-gradient(135deg, #1abc9c, #16a085)"
            },
            "💻 IT/테크": {
                "keywords": ["프로그래밍", "앱개발", "웹개발", "코딩", "개발자", "IT트렌드", "스마트폰", "갤럭시", "아이폰", "노트북", "태블릿", "AI", "빅데이터", "클라우드", "보안", "블록체인"],
                "description": "프로그래밍, IT, 테크 정보",
                "color": "linear-gradient(135deg, #6c5ce7, #5f3dc4)"
            },
            "📚 교육/학습": {
                "keywords": ["영어공부", "토익", "토플", "자격증", "공무원", "취업", "면접", "자기계발", "온라인강의", "독학", "스터디", "시험", "학원", "인강", "어학연수", "유학"],
                "description": "교육, 학습, 자기계발",
                "color": "linear-gradient(135deg, #fd79a8, #e84393)"
            },
            "🚗 자동차/모빌리티": {
                "keywords": ["자동차", "전기차", "하이브리드", "중고차", "신차", "자동차리뷰", "카페", "드라이브", "캠핑카", "모터사이클", "자전거", "킥보드", "대중교통", "택시", "카셰어링", "렌터카"],
                "description": "자동차, 모빌리티, 교통",
                "color": "linear-gradient(135deg, #00b894, #00a085)"
            },
            "🏥 의료/건강정보": {
                "keywords": ["건강검진", "병원", "의료정보", "건강관리", "약물", "질병", "예방접종", "한의학", "치과", "성형", "피부과", "내과", "정신건강", "스트레스", "우울증", "불안"],
                "description": "의료, 건강, 질병 정보",
                "color": "linear-gradient(135deg, #00cec9, #00b894)"
            }
        }

# 웹앱 인스턴스 생성
blog_app = BlogWebApp()

def require_auth(f):
    """인증 필요 데코레이터"""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('authenticated'):
            return jsonify({'error': '인증이 필요합니다.', 'redirect': '/login'}), 401
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    """메인 페이지"""
    # 패스워드 인증 체크
    if not session.get('authenticated'):
        return redirect(url_for('login'))
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """로그인 페이지"""
    if request.method == 'POST':
        password = request.form.get('password')
        if password == ADMIN_PASSWORD:
            session['authenticated'] = True
            return redirect(url_for('index'))
        else:
            error = "잘못된 패스워드입니다."
            return render_template('login.html', error=error)
    return render_template('login.html')

@app.route('/logout')
def logout():
    """로그아웃"""
    session.pop('authenticated', None)
    return redirect(url_for('login'))

@app.route('/attached_assets/<path:filename>')
def attached_assets(filename):
    """attached_assets 폴더의 파일 서빙"""
    return send_from_directory('attached_assets', filename)

@app.route('/api/search', methods=['POST'])
@require_auth
def api_search():
    """네이버 블로그 검색 API"""
    try:
        data = request.get_json()
        keyword = data.get('keyword', '').strip()
        search_count = data.get('search_count', 50)
        sort_type = data.get('sort_type', 'date')

        print(f"🔍 검색 요청 받음: '{keyword}' (개수: {search_count}, 정렬: {sort_type})")

        if not keyword:
            return jsonify({'error': '키워드를 입력해주세요'}), 400

        # 환경변수 체크
        if not blog_app.client_id or not blog_app.client_secret:
            return jsonify({
                'error': '네이버 API 키가 설정되지 않았습니다. Secrets에서 NAVER_CLIENT_ID와 NAVER_CLIENT_SECRET_KEY를 설정해주세요.',
                'details': {
                    'client_id_set': bool(blog_app.client_id),
                    'client_secret_set': bool(blog_app.client_secret)
                }
            }), 400

        # 네이버 블로그 검색
        search_result = blog_app.search_naver_blog(keyword, search_count, sort_type)
        
        if not search_result:
            return jsonify({'error': '검색 결과를 가져올 수 없습니다.'}), 500
            
        titles, descriptions = blog_app.extract_blog_data(search_result)

        if not titles:
            return jsonify({'error': '검색된 블로그 제목이 없습니다. 다른 키워드를 시도해보세요.'}), 404

        # 결과를 세션에 저장
        session_id = str(uuid.uuid4())
        blog_app.temp_results[session_id] = {
            'keyword': keyword,
            'search_result': search_result,
            'titles': titles,
            'descriptions': descriptions,
            'timestamp': datetime.now()
        }

        print(f"✅ 검색 완료: {len(titles)}개 제목 수집됨")

        return jsonify({
            'success': True,
            'session_id': session_id,
            'total_results': search_result.get('total', 0),
            'collected_titles': len(titles),
            'titles': titles,  # 전체 검색 결과 반환
            'average_length': sum(len(t) for t in titles)/len(titles) if titles else 0
        })

    except Exception as e:
        print(f"❌ 검색 API 오류: {str(e)}")
        import traceback
        print(f"📝 오류 상세: {traceback.format_exc()}")
        
        return jsonify({
            'error': str(e),
            'type': 'search_error',
            'suggestion': '네이버 API 키 설정을 확인하거나 다른 키워드를 시도해보세요.'
        }), 500

@app.route('/api/analyze', methods=['POST'])
@require_auth
def api_analyze():
    """AI 분석 API"""
    try:
        data = request.get_json()
        session_id = data.get('session_id')
        analysis_type = data.get('analysis_type', 'comprehensive')

        if not session_id or session_id not in blog_app.temp_results:
            return jsonify({'error': '유효하지 않은 세션입니다'}), 400

        result_data = blog_app.temp_results[session_id]

        # AI 분석 실행
        analysis_result = blog_app.analyze_with_gpt(
            result_data['titles'], 
            result_data['descriptions'], 
            result_data['keyword'], 
            analysis_type
        )

        # 분석 결과 저장
        blog_app.temp_results[session_id]['analysis_result'] = analysis_result
        blog_app.temp_results[session_id]['analysis_type'] = analysis_type

        return jsonify({
            'success': True,
            'analysis_result': analysis_result
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/generate_titles', methods=['POST'])
@require_auth
def api_generate_titles():
    """새로운 제목 생성 API"""
    try:
        data = request.get_json()
        session_id = data.get('session_id')
        num_titles = data.get('num_titles', 10)

        if not session_id or session_id not in blog_app.temp_results:
            return jsonify({'error': '유효하지 않은 세션입니다'}), 400

        result_data = blog_app.temp_results[session_id]

        if 'analysis_result' not in result_data:
            return jsonify({'error': '먼저 분석을 실행해주세요'}), 400

        # 새로운 제목 생성
        generated_titles = blog_app.generate_titles_with_gpt(
            result_data['analysis_result'],
            result_data['keyword'],
            num_titles
        )

        # 제목 파싱 - 숫자로 시작하는 제목만 추출
        extracted_titles = []
        
        if generated_titles and generated_titles.strip():
            print(f"🔍 원본 GPT 응답: {generated_titles[:500]}...")
            
            # 줄별로 분리
            lines = [line.strip() for line in generated_titles.split('\n') if line.strip()]
            
            import re
            for line in lines:
                # 숫자로 시작하는 줄 찾기 (1. 제목, 1) 제목, 1 제목 등)
                match = re.match(r'^\d+[\.\)\s]\s*(.+)', line)
                if match:
                    title = match.group(1).strip()
                    
                    # 마크다운 제거
                    title = re.sub(r'\*\*([^*]+)\*\*', r'\1', title)
                    title = re.sub(r'\*([^*]+)\*', r'\1', title)
                    
                    # 금지된 키워드들이 포함되지 않았는지 확인
                    forbidden_keywords = ['유형:', '타겟:', '목적:', '키워드:', '특징:', '설명:', 
                                        '**유형**', '**타겟**', '**목적**', '**키워드**', '**특징**', '**설명**']
                    
                    # 제목에 금지된 키워드가 없고, 적절한 길이인 경우만 추가
                    if (not any(keyword in title for keyword in forbidden_keywords) and 
                        title and len(title) > 5 and len(title) < 200):
                        extracted_titles.append(title)
                        print(f"✅ 추출된 제목: {title}")
                    else:
                        print(f"❌ 제외된 라인: {title}")
        
        # 추출된 제목이 부족하면 fallback 제목 생성
        if len(extracted_titles) < num_titles:
            needed = num_titles - len(extracted_titles)
            print(f"⚠️ 제목 부족 ({len(extracted_titles)}/{num_titles}), fallback 제목 {needed}개 추가")
            
            fallback_titles = [
                f"{result_data['keyword']} 완벽 가이드",
                f"{result_data['keyword']} 초보자를 위한 안내서", 
                f"{result_data['keyword']} 알아야 할 모든 것",
                f"{result_data['keyword']} 실전 활용법",
                f"{result_data['keyword']} 추천 및 후기",
                f"{result_data['keyword']} 성공 사례 분석",
                f"{result_data['keyword']} 전문가 노하우",
                f"{result_data['keyword']} 단계별 방법론",
                f"{result_data['keyword']} 트렌드 분석",
                f"{result_data['keyword']} 실무 적용기",
                f"{result_data['keyword']} 비교 분석",
                f"{result_data['keyword']} 선택 가이드"
            ]
            
            # 기존 제목과 중복되지 않는 fallback 제목만 추가
            for fallback in fallback_titles:
                if fallback not in extracted_titles and len(extracted_titles) < num_titles:
                    extracted_titles.append(fallback)

        # 최종 제목 리스트를 지정된 개수로 제한
        extracted_titles = extracted_titles[:num_titles]
        
        print(f"🎯 최종 제목 개수: {len(extracted_titles)}")
        for i, title in enumerate(extracted_titles):
            print(f"  {i+1}. {title}")

        # 생성된 제목 저장
        blog_app.temp_results[session_id]['generated_titles'] = extracted_titles

        return jsonify({
            'success': True,
            'titles': extracted_titles
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/generate_blog', methods=['POST'])
@require_auth
def api_generate_blog():
    """블로그 글 생성 API"""
    try:
        data = request.get_json()
        session_id = data.get('session_id')
        selected_title = data.get('title')
        prompt_type = data.get('prompt_type', 'informative')
        additional_prompt = data.get('additional_prompt', '')
        min_chars = data.get('min_chars', 4000)
        max_chars = data.get('max_chars', 8000)

        if not session_id or session_id not in blog_app.temp_results:
            return jsonify({'error': '유효하지 않은 세션입니다'}), 400

        if not selected_title:
            return jsonify({'error': '제목을 선택해주세요'}), 400

        result_data = blog_app.temp_results[session_id]

        # 분석 결과가 있으면 함께 전달
        analysis_result = result_data.get('analysis_result')

        # 블로그 글 생성 (글자수 설정 및 분석 결과 포함)
        blog_content = blog_app.generate_blog_content(
            selected_title,
            result_data['keyword'],
            prompt_type,
            additional_prompt,
            min_chars,
            max_chars,
            analysis_result
        )

        # 생성된 블로그 글 저장
        blog_app.temp_results[session_id]['blog_content'] = {
            'title': selected_title,
            'content': blog_content,
            'prompt_type': prompt_type,
            'additional_prompt': additional_prompt,
            'min_chars': min_chars,
            'max_chars': max_chars
        }

        # SEO 분석 수행
        seo_analysis = blog_app._analyze_seo_content(blog_content, result_data['keyword'])
        
        return jsonify({
            'success': True,
            'title': selected_title,
            'content': blog_content,
            'char_count': len(blog_content),
            'seo_analysis': seo_analysis,
            'keyword': result_data['keyword']
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/generate_images', methods=['POST'])
@require_auth
def api_generate_images():
    """이미지 생성 API"""
    try:
        data = request.get_json()
        session_id = data.get('session_id')
        num_images = data.get('num_images', 4)

        if not session_id or session_id not in blog_app.temp_results:
            return jsonify({'error': '유효하지 않은 세션입니다'}), 400

        result_data = blog_app.temp_results[session_id]

        if 'blog_content' not in result_data:
            return jsonify({'error': '먼저 블로그 글을 생성해주세요'}), 400

        blog_data = result_data['blog_content']

        # 이미지 생성
        generated_images = blog_app.generate_dall_e_images(
            blog_data['title'],
            blog_data['content'],
            result_data['keyword'],
            num_images
        )

        # 생성된 이미지 저장
        blog_app.temp_results[session_id]['generated_images'] = generated_images

        return jsonify({
            'success': True,
            'images': generated_images
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/categories')
@require_auth
def api_categories():
    """카테고리 목록 API"""
    try:
        categories = blog_app.get_predefined_categories()
        return jsonify({
            'success': True,
            'categories': categories
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/category-keywords')
@require_auth
def api_category_keywords():
    """카테고리별 키워드 API"""
    try:
        categories = blog_app.get_predefined_categories()
        category_list = []
        
        for name, data in categories.items():
            category_list.append({
                'name': name,
                'icon': name.split()[0],
                'description': data['description'],
                'keywords': data['keywords']
            })
        
        return jsonify(category_list)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/recommended-keywords')
@require_auth
def api_recommended_keywords_route():
    """추천 키워드 API"""
    try:
        # Google 트렌드 키워드 가져오기
        google_keywords = blog_app.get_google_trending_keywords()
        
        # 네이버 DataLab 트렌드 키워드 가져오기  
        naver_keywords = blog_app.get_naver_datalab_keywords()
        
        # 결과 조합
        trending_data = {
            'google_trends': google_keywords,
            'naver_datalab': naver_keywords,
            'update_time': datetime.now().isoformat()
        }
        
        return jsonify(trending_data)
        
    except Exception as e:
        print(f"트렌드 키워드 API 오류: {str(e)}")
        # Fallback 데이터 반환
        fallback_data = {
            'google_trends': [
                {'rank': 1, 'keyword': 'ChatGPT', 'category': '🤖 AI', 'source': 'Fallback'},
                {'rank': 2, 'keyword': '다이어트', 'category': '💪 건강', 'source': 'Fallback'}
            ],
            'naver_datalab': [
                {'rank': 1, 'keyword': '요리레시피', 'category': '🍳 요리', 'source': 'Fallback'},
                {'rank': 2, 'keyword': '홈트레이닝', 'category': '💪 운동', 'source': 'Fallback'}
            ],
            'update_time': datetime.now().isoformat()
        }
        return jsonify(fallback_data)

@app.route('/api/recommended_keywords')
def api_recommended_keywords():
    """실시간 트렌드 키워드 API (Google + Naver)"""
    try:
        import random
        from datetime import datetime
        
        current_hour = datetime.now().hour
        
        # Google 트렌드 키워드 가져오기
        google_keywords = blog_app.get_google_trending_keywords()
        
        # 네이버 DataLab 트렌드 키워드 가져오기  
        naver_keywords = blog_app.get_naver_datalab_keywords()
        
        # 결과 조합
        trending_data = {
            'google_trends': google_keywords,
            'naver_trends': naver_keywords,
            'time_period': f"🕐 {current_hour}시",
            'update_time': datetime.now().isoformat()
        }
        
        return jsonify({
            'success': True,
            'trending_data': trending_data
        })
        
    except Exception as e:
        print(f"트렌드 키워드 API 오류: {str(e)}")
        # Fallback으로 기존 방식 사용
        return api_recommended_keywords_fallback()

def api_recommended_keywords_fallback():
    """추천 키워드 API 실패시 대체 함수"""
    try:
        import random
        from datetime import datetime
        
        current_hour = datetime.now().hour
        
        # 시간대별 키워드 풀
        time_keywords = {
            'morning': [
                {'keyword': '모닝루틴', 'category': '🌅 라이프'},
                {'keyword': '아침운동', 'category': '🌅 건강'},
                {'keyword': '아침식단', 'category': '🌅 요리'}
            ],
            'afternoon': [
                {'keyword': '점심메뉴', 'category': '☀️ 요리'},
                {'keyword': '업무효율', 'category': '☀️ 비즈니스'},
                {'keyword': '카페추천', 'category': '☀️ 맛집'}
            ],
            'evening': [
                {'keyword': '저녁요리', 'category': '🌙 요리'},
                {'keyword': '넷플릭스', 'category': '🌙 엔터'},
                {'keyword': '독서', 'category': '🌙 취미'}
            ]
        }
        
        # 시간대별 선택
        if 6 <= current_hour < 12:
            selected = time_keywords['morning']
            time_label = "🌅 아침"
        elif 12 <= current_hour < 18:
            selected = time_keywords['afternoon'] 
            time_label = "☀️ 오후"
        else:
            selected = time_keywords['evening']
            time_label = "🌙 저녁"
        
        # Fallback 트렌드 데이터
        trending_data = {
            'google_trends': [
                {'rank': 1, 'keyword': 'ChatGPT', 'category': '🤖 AI', 'source': 'Fallback'},
                {'rank': 2, 'keyword': '다이어트', 'category': '💪 건강', 'source': 'Fallback'}
            ],
            'naver_trends': [
                {'rank': 1, 'keyword': '요리레시피', 'category': '🍳 요리', 'source': 'Fallback'},
                {'rank': 2, 'keyword': '홈트레이닝', 'category': '💪 운동', 'source': 'Fallback'}
            ],
            'time_period': time_label,
            'update_time': datetime.now().isoformat()
        }
        
        return jsonify({
            'success': True,
            'trending_data': trending_data
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/results/<session_id>')
def api_get_results(session_id):
    """결과 조회 API"""
    try:
        if session_id not in blog_app.temp_results:
            return jsonify({'error': '유효하지 않은 세션입니다'}), 400

        result_data = blog_app.temp_results[session_id]

        return jsonify({
            'success': True,
            'data': {
                'keyword': result_data.get('keyword'),
                'titles': result_data.get('titles', []),
                'analysis_result': result_data.get('analysis_result'),
                'generated_titles': result_data.get('generated_titles', []),
                'blog_content': result_data.get('blog_content'),
                'generated_images': result_data.get('generated_images', [])
            }
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/search', methods=['POST'])
def search():
    """네이버 블로그 검색"""
    try:
        data = request.get_json()
        keyword = data.get('keyword', '').strip()
        display = data.get('display', 15)
        sort = data.get('sort', 'sim')

        if not keyword:
            return jsonify({'error': '키워드를 입력해주세요'}), 400

        # 네이버 블로그 검색
        search_result = blog_app.search_naver_blog(keyword, display, sort)
        
        if not search_result or 'items' not in search_result:
            return jsonify({'error': '검색 결과가 없습니다'}), 400

        # 결과 가공
        results = []
        for item in search_result['items']:
            results.append({
                'title': blog_app.clean_html_tags(item.get('title', '')),
                'description': blog_app.clean_html_tags(item.get('description', '')),
                'link': item.get('link', ''),
                'postdate': item.get('postdate', '')
            })

        # 세션에 결과 저장
        session_id = str(uuid.uuid4())
        blog_app.temp_results[session_id] = {
            'keyword': keyword,
            'search_result': search_result,
            'results': results,
            'timestamp': datetime.now()
        }

        return jsonify({
            'success': True,
            'keyword': keyword,
            'results': results,
            'session_id': session_id,
            'total': search_result.get('total', 0)
        })

    except Exception as e:
        print(f"검색 오류: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/analyze', methods=['POST'])
def analyze():
    """AI 분석"""
    try:
        # 세션에서 마지막 검색 결과 가져오기
        latest_session = None
        for session_id, data in blog_app.temp_results.items():
            if latest_session is None or data['timestamp'] > blog_app.temp_results[latest_session]['timestamp']:
                latest_session = session_id

        if not latest_session:
            return jsonify({'error': '먼저 검색을 실행해주세요'}), 400

        result_data = blog_app.temp_results[latest_session]
        titles = [item['title'] for item in result_data['results']]
        descriptions = [item['description'] for item in result_data['results']]

        # AI 분석 실행
        analysis_result = blog_app.analyze_with_gpt(
            titles, descriptions, result_data['keyword']
        )

        # 분석 결과 저장
        blog_app.temp_results[latest_session]['analysis_result'] = analysis_result

        return jsonify({
            'success': True,
            'analysis': analysis_result,
            'session_id': latest_session
        })

    except Exception as e:
        print(f"분석 오류: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/generate-titles', methods=['POST'])
def generate_titles():
    """제목 생성"""
    try:
        # 세션에서 마지막 분석 결과 가져오기
        latest_session = None
        for session_id, data in blog_app.temp_results.items():
            if 'analysis_result' in data:
                if latest_session is None or data['timestamp'] > blog_app.temp_results[latest_session]['timestamp']:
                    latest_session = session_id

        if not latest_session:
            return jsonify({'error': '먼저 분석을 실행해주세요'}), 400

        result_data = blog_app.temp_results[latest_session]

        # 제목 생성
        generated_titles = blog_app.generate_titles_with_gpt(
            result_data['analysis_result'],
            result_data['keyword'],
            10
        )

        # 제목 파싱
        titles = []
        if generated_titles:
            lines = generated_titles.split('\n')
            for line in lines:
                line = line.strip()
                if line and not line.startswith('#') and len(line) > 5:
                    # 번호 제거
                    import re
                    cleaned = re.sub(r'^\d+\.\s*', '', line)
                    if cleaned:
                        titles.append(cleaned)

        # 생성된 제목 저장
        blog_app.temp_results[latest_session]['generated_titles'] = titles

        return jsonify({
            'success': True,
            'titles': titles,
            'session_id': latest_session
        })

    except Exception as e:
        print(f"제목 생성 오류: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/generate-blog', methods=['POST'])
def generate_blog():
    """블로그 글 생성"""
    try:
        data = request.get_json()
        title = data.get('title', '').strip()
        min_chars = data.get('min_chars', 4000)
        max_chars = data.get('max_chars', 8000)

        if not title:
            return jsonify({'error': '제목을 선택해주세요'}), 400

        # 세션에서 키워드 찾기
        keyword = None
        analysis_result = None
        for session_id, session_data in blog_app.temp_results.items():
            if 'keyword' in session_data:
                keyword = session_data['keyword']
                analysis_result = session_data.get('analysis_result')
                break

        if not keyword:
            return jsonify({'error': '키워드 정보를 찾을 수 없습니다'}), 400

        # 블로그 글 생성
        blog_content = blog_app.generate_blog_content(
            title, keyword, 'informative', '', min_chars, max_chars, analysis_result
        )

        return jsonify({
            'success': True,
            'title': title,
            'content': blog_content,
            'char_count': len(blog_content)
        })

    except Exception as e:
        print(f"블로그 생성 오류: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/generate-images', methods=['POST'])
def generate_images():
    """이미지 생성"""
    try:
        data = request.get_json()
        title = data.get('title', '')
        content = data.get('content', '')
        count = data.get('count', 4)

        if not title or not content:
            return jsonify({'error': '제목과 내용이 필요합니다'}), 400

        # 키워드와 세션 ID 찾기
        keyword = None
        target_session_id = None
        for session_id, session_data in blog_app.temp_results.items():
            if 'keyword' in session_data:
                keyword = session_data['keyword']
                target_session_id = session_id
                break

        if not keyword:
            keyword = title  # 키워드가 없으면 제목 사용

        # 이미지 생성
        generated_images = blog_app.generate_dall_e_images(
            title, content, keyword, count
        )

        # 세션에 이미지 저장 (세션 ID가 있는 경우)
        if target_session_id and target_session_id in blog_app.temp_results:
            blog_app.temp_results[target_session_id]['generated_images'] = generated_images
            print(f"✅ 이미지가 세션 {target_session_id}에 저장되었습니다.")
        
        return jsonify({
            'success': True,
            'images': generated_images,
            'session_id': target_session_id  # 클라이언트에 세션 ID 전달
        })

    except Exception as e:
        print(f"이미지 생성 오류: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/download_images/<session_id>')
def api_download_images(session_id):
    """이미지 ZIP 다운로드 API"""
    try:
        print(f"🔍 다운로드 요청 세션 ID: {session_id}")
        print(f"📋 사용 가능한 세션들: {list(blog_app.temp_results.keys())}")
        
        if session_id not in blog_app.temp_results:
            print(f"❌ 유효하지 않은 세션 ID: {session_id}")
            return jsonify({'error': '유효하지 않은 세션입니다'}), 400

        result_data = blog_app.temp_results[session_id]
        generated_images = result_data.get('generated_images', [])
        
        print(f"📸 찾은 이미지 개수: {len(generated_images)}")

        if not generated_images:
            print("❌ 다운로드할 이미지가 없습니다.")
            return jsonify({'error': '다운로드할 이미지가 없습니다. 먼저 이미지를 생성해주세요.'}), 400

        import zipfile
        import io
        import urllib.request
        import urllib.error

        # 메모리에서 ZIP 파일 생성
        zip_buffer = io.BytesIO()
        successful_downloads = 0

        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for i, image in enumerate(generated_images):
                try:
                    print(f"📥 이미지 {i+1} 다운로드 시작: {image['url'][:50]}...")
                    
                    # urllib을 사용하여 이미지 다운로드 (requests 대신)
                    request = urllib.request.Request(image['url'])
                    request.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
                    
                    with urllib.request.urlopen(request, timeout=30) as response:
                        image_data = response.read()

                    # ZIP 파일에 이미지 추가
                    filename = f"generated_image_{i+1}.png"
                    zip_file.writestr(filename, image_data)
                    successful_downloads += 1
                    
                    print(f"✅ 이미지 {i+1} 다운로드 완료")

                except Exception as e:
                    print(f"❌ 이미지 {i+1} 다운로드 오류: {e}")
                    continue

        if successful_downloads == 0:
            return jsonify({'error': '모든 이미지 다운로드에 실패했습니다.'}), 500

        zip_buffer.seek(0)

        # 키워드나 제목을 사용한 파일명 생성
        keyword = result_data.get('keyword', 'images')
        safe_keyword = "".join(c for c in keyword if c.isalnum() or c in (' ', '-', '_')).rstrip()
        if not safe_keyword:
            safe_keyword = 'generated_images'
        filename = f"{safe_keyword}_images.zip"
        
        print(f"📦 ZIP 파일 생성 완료: {filename} ({successful_downloads}개 이미지)")

        return send_file(
            zip_buffer,
            mimetype='application/zip',
            as_attachment=True,
            download_name=filename
        )

    except Exception as e:
        print(f"❌ ZIP 파일 생성 오류: {str(e)}")
        import traceback
        print(f"📝 오류 상세: {traceback.format_exc()}")
        return jsonify({'error': f'ZIP 파일 생성 중 오류 발생: {str(e)}'}), 500

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') != 'production'
    app.run(debug=debug, host='0.0.0.0', port=port)