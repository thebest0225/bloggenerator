import streamlit as st
import urllib.request
import urllib.parse
import urllib.error
import json
import re
import time
import io
from openai import OpenAI
import prompts

# 페이지 설정
st.set_page_config(
    page_title="KeiaiLAB 블로그 글생성기",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS 스타일
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        text-align: center;
        color: white;
    }
    .result-container {
        background-color: #f8f9fa;
        padding: 1.5rem;
        border-radius: 8px;
        border-left: 4px solid #667eea;
        margin: 1rem 0;
        white-space: pre-wrap;
    }
    .metric-container {
        background-color: #ffffff;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        text-align: center;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

def load_env_variables():
    """환경변수 로드"""
    env_vars = {}
    try:
        with open('.env', 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key.strip()] = value.strip()
    except FileNotFoundError:
        return None, None, None
    
    return (
        env_vars.get('NAVER_CLIENT_ID'),
        env_vars.get('NAVER_CLIENT_SECRET_KEY'),
        env_vars.get('OPENAI_API_KEY')
    )

def search_naver_blog(query, client_id, client_secret, display=50, sort='date'):
    """네이버 블로그 검색"""
    enc_text = urllib.parse.quote(query)
    url = f"https://openapi.naver.com/v1/search/blog.json?query={enc_text}&display={display}&sort={sort}"
    
    request = urllib.request.Request(url)
    request.add_header("X-Naver-Client-Id", client_id)
    request.add_header("X-Naver-Client-Secret", client_secret)
    
    try:
        response = urllib.request.urlopen(request)
        if response.getcode() == 200:
            response_body = response.read()
            return json.loads(response_body.decode('utf-8'))
        else:
            st.error(f"API 응답 오류: HTTP {response.getcode()}")
            return None
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8')
        st.error(f"네이버 API 오류 ({e.code}): {error_body}")
        st.info("💡 .env 파일의 NAVER_CLIENT_SECRET_KEY를 네이버 개발자센터에서 다시 확인해주세요.")
        return None
    except Exception as e:
        st.error(f"API 호출 중 오류 발생: {e}")
        return None

def clean_html_tags(text):
    """HTML 태그 제거"""
    clean = re.compile('<.*?>')
    return re.sub(clean, '', text)

def extract_blog_data(search_result):
    """블로그 데이터 추출"""
    if not search_result or 'items' not in search_result:
        return [], []
    
    titles = []
    descriptions = []
    
    for item in search_result['items']:
        title = clean_html_tags(item.get('title', ''))
        description = clean_html_tags(item.get('description', ''))
        
        if title:
            titles.append(title)
            descriptions.append(description)
    
    return titles, descriptions

def analyze_with_gpt(titles, descriptions, query, openai_api_key, analysis_type='comprehensive'):
    """GPT로 블로그 제목 분석"""
    try:
        client = OpenAI(api_key=openai_api_key)
        
        # 프롬프트 생성
        system_prompt = prompts.get_system_prompt(analysis_type)
        user_prompt = prompts.create_analysis_prompt(query, titles, analysis_type)
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=3000,
            temperature=0.7
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        st.error(f"GPT 분석 중 오류 발생: {e}")
        return None

def generate_new_titles(analysis_result, query, openai_api_key, num_titles=10):
    """새로운 블로그 제목 생성"""
    try:
        client = OpenAI(api_key=openai_api_key)
        
        system_prompt = prompts.get_title_generation_system_prompt()
        user_prompt = prompts.create_title_generation_prompt(query, analysis_result, num_titles)
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=2000,
            temperature=0.8
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        st.error(f"제목 생성 중 오류 발생: {e}")
        return None

def main():
    # 헤더
    st.markdown("""
    <div class="main-header">
        <h1>📝 KeiaiLAB 블로그 글생성기</h1>
        <p>AI 기반 블로그 제목 분석 및 신규 제목 생성 도구</p>
    </div>
    """, unsafe_allow_html=True)
    
    # 환경변수 로드
    client_id, client_secret, openai_api_key = load_env_variables()
    
    if not all([client_id, client_secret, openai_api_key]):
        st.error("🚨 .env 파일을 확인해주세요. API 키가 필요합니다.")
        st.info("""
        다음 내용으로 .env 파일을 생성해주세요:
        ```
        NAVER_CLIENT_ID=your_naver_client_id
        NAVER_CLIENT_SECRET_KEY=your_naver_client_secret
        OPENAI_API_KEY=your_openai_api_key
        ```
        """)
        return
    
    # 사이드바 설정
    with st.sidebar:
        st.markdown("### ⚙️ 설정")
        
        # 검색 설정
        st.markdown("### 🔍 검색 설정")
        search_count = st.slider("분석할 블로그 개수", 10, 100, 50)
        sort_method = st.radio("정렬 방식", ["날짜순 (최신순)", "정확도순"])
        sort_value = 'date' if sort_method == "날짜순 (최신순)" else 'sim'
        
        st.markdown("---")
        
        # 분석 설정
        st.markdown("### 🧠 분석 설정")
        analysis_types = prompts.get_available_analysis_types()
        
        selected_analysis = st.selectbox(
            "분석 유형 선택",
            options=list(analysis_types.keys()),
            format_func=lambda x: analysis_types[x]['name'],
            help="원하는 분석 유형을 선택하세요"
        )
        
        st.markdown("---")
        
        # 제목 생성 설정
        st.markdown("### ✨ 제목 생성 설정")
        num_titles = st.slider("생성할 제목 개수", 5, 30, 10)
    
    # 메인 영역
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.markdown("### 🔍 키워드 입력")
        query = st.text_input(
            "분석할 키워드를 입력하세요",
            placeholder="예: 반려동물, 요리, 여행 등",
            help="네이버 블로그에서 검색할 키워드를 입력하세요"
        )
    
    with col2:
        st.markdown("### 🚀 실행")
        analyze_button = st.button("분석 시작", use_container_width=True, type="primary")
    
    # 분석 실행
    if analyze_button and query.strip():
        with st.spinner("🔍 네이버 블로그 검색 중..."):
            search_result = search_naver_blog(query, client_id, client_secret, search_count, sort_value)
        
        if search_result:
            titles, descriptions = extract_blog_data(search_result)
            
            if titles:
                # 검색 결과 요약
                st.markdown("### 📊 검색 결과 요약")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("총 검색 결과", f"{search_result.get('total', 0):,}개")
                with col2:
                    st.metric("수집된 제목", f"{len(titles)}개")
                with col3:
                    st.metric("평균 제목 길이", f"{sum(len(t) for t in titles)/len(titles):.1f}자")
                
                # 분석 실행
                with st.spinner("🧠 AI 분석 중..."):
                    analysis_result = analyze_with_gpt(titles, descriptions, query, openai_api_key, selected_analysis)
                
                if analysis_result:
                    # 탭으로 결과 분리
                    tab1, tab2 = st.tabs(["📝 수집된 제목 목록", "📋 AI 분석 결과"])
                    
                    with tab1:
                        st.markdown("#### 🔍 검색된 블로그 제목들")
                        for i, title in enumerate(titles, 1):
                            st.write(f"**{i:2d}.** {title}")
                    
                    with tab2:
                        st.markdown("#### 🧠 AI 분석 보고서")
                        st.markdown(f'<div class="result-container">{analysis_result}</div>', unsafe_allow_html=True)
                    
                    # 제목 생성 및 다운로드 버튼
                    st.markdown("### ✨ 추가 기능")
                    
                    col1, col2 = st.columns([1, 1])
                    with col1:
                        if st.button("🎯 새로운 제목 생성", use_container_width=True):
                            with st.spinner(f"✨ {num_titles}개의 새로운 제목 생성 중..."):
                                generated_titles = generate_new_titles(analysis_result, query, openai_api_key, num_titles)
                            
                            if generated_titles:
                                st.markdown("### 🎉 생성된 새로운 제목들")
                                st.markdown(f'<div class="result-container">{generated_titles}</div>', unsafe_allow_html=True)
                    
                    with col2:
                        if st.button("💾 결과 다운로드", use_container_width=True):
                            # 결과 파일 생성
                            timestamp = time.strftime("%Y%m%d_%H%M%S")
                            filename = f"blog_analysis_{query}_{timestamp}.txt"
                            
                            content = f"""=== KeiaiLAB 블로그 제목 분석 및 생성 결과 ===
검색 키워드: {query}
분석 일시: {time.strftime('%Y-%m-%d %H:%M:%S')}
분석 유형: {analysis_types[selected_analysis]['name']}

=== 검색 결과 요약 ===
총 검색 결과: {search_result.get('total', 0):,}개
수집된 제목: {len(titles)}개
평균 제목 길이: {sum(len(t) for t in titles)/len(titles):.1f}자

=== 수집된 제목 목록 ===
""" + "\n".join([f"{i:2d}. {title}" for i, title in enumerate(titles, 1)]) + f"""

=== AI 분석 결과 ===
{analysis_result}
"""
                            
                            # 다운로드 제공
                            st.download_button(
                                label="📥 파일 다운로드",
                                data=content.encode('utf-8'),
                                file_name=filename,
                                mime='text/plain',
                                use_container_width=True
                            )
                else:
                    st.error("AI 분석에 실패했습니다.")
            else:
                st.warning("수집된 블로그 제목이 없습니다.")
        else:
            st.error("블로그 검색에 실패했습니다. API 설정을 확인해주세요.")
    
    elif analyze_button and not query.strip():
        st.warning("키워드를 입력해주세요!")

if __name__ == "__main__":
    main() 