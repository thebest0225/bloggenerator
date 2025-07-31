import streamlit as st
import urllib.request
import urllib.parse
import urllib.error
import json
import re
import time
from collections import Counter
from openai import OpenAI
import prompts
import io
import requests

# 페이지 설정
st.set_page_config(
    page_title="KeiaiLAB 블로그 글생성기",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 커스텀 CSS 스타일
st.markdown("""
<style>
    .main-header {
        text-align: center;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3rem;
        font-weight: 800;
        margin-bottom: 0.5rem;
    }
    
    .sub-header {
        text-align: center;
        color: #666;
        font-size: 1.2rem;
        margin-bottom: 2rem;
    }
    
    .metric-container {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin: 0.5rem 0;
    }
    
    .result-container {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 15px;
        border-left: 5px solid #667eea;
        margin: 1rem 0;
    }
    
    .generated-title {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        border-left: 4px solid #764ba2;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    
    .stButton>button {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 25px;
        padding: 0.5rem 2rem;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    
    .sidebar-content {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
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

def test_naver_api_connection(client_id, client_secret):
    """네이버 API 연결 상태 테스트"""
    try:
        headers = {
            'X-Naver-Client-Id': client_id,
            'X-Naver-Client-Secret': client_secret
        }
        # 간단한 테스트 검색으로 API 연결 확인
        url = "https://openapi.naver.com/v1/search/blog"
        params = {'query': 'test', 'display': 1}
        
        response = requests.get(url, headers=headers, params=params, timeout=5)
        return response.status_code == 200
    except:
        return False

def test_openai_api_connection(api_key):
    """OpenAI API 연결 상태 테스트"""
    try:
        client = OpenAI(api_key=api_key)
        # 간단한 API 호출로 연결 확인
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "테스트"}],
            max_tokens=1,
            timeout=5
        )
        return True
    except:
        return False

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
    text = text.replace('<b>', '').replace('</b>', '')
    text = text.replace('&quot;', '"').replace('&lt;', '<').replace('&gt;', '>')
    text = text.replace('&amp;', '&').replace('&#39;', "'")
    return text.strip()

def extract_blog_data(search_result):
    """블로그 데이터 추출"""
    if not search_result or 'items' not in search_result:
        return [], []
    
    titles = []
    descriptions = []
    
    for item in search_result['items']:
        clean_title = clean_html_tags(item['title'])
        clean_desc = clean_html_tags(item['description'])
        titles.append(clean_title)
        descriptions.append(clean_desc)
    
    return titles, descriptions

def analyze_title_patterns(titles):
    """제목 패턴 분석"""
    analysis = {
        'total_count': len(titles),
        'avg_length': sum(len(title) for title in titles) / len(titles) if titles else 0,
        'length_distribution': {},
        'has_numbers': 0,
        'has_question_mark': 0,
        'has_exclamation': 0,
        'has_parentheses': 0,
        'has_quotes': 0,
        'keyword_frequency': Counter()
    }
    
    for title in titles:
        length_range = f"{(len(title)//10)*10}-{(len(title)//10)*10+9}"
        analysis['length_distribution'][length_range] = analysis['length_distribution'].get(length_range, 0) + 1
        
        if re.search(r'\d', title):
            analysis['has_numbers'] += 1
        if '?' in title:
            analysis['has_question_mark'] += 1
        if '!' in title:
            analysis['has_exclamation'] += 1
        if '(' in title or ')' in title:
            analysis['has_parentheses'] += 1
        if '"' in title or "'" in title:
            analysis['has_quotes'] += 1
        
        words = re.findall(r'[가-힣]{2,}', title)
        analysis['keyword_frequency'].update(words)
    
    return analysis

def analyze_with_gpt(titles, descriptions, query, openai_api_key, analysis_type='comprehensive'):
    """GPT 분석"""
    if not openai_api_key:
        return "OpenAI API 키가 설정되지 않았습니다."
    
    if not titles:
        return "분석할 블로그 제목이 없습니다."
    
    try:
        client = OpenAI(api_key=openai_api_key)
        basic_analysis = analyze_title_patterns(titles)
        prompt = prompts.get_analysis_prompt(analysis_type, query, titles, descriptions, basic_analysis)
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": prompts.get_system_prompt_analysis()},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=4000
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        return f"GPT 분석 중 오류 발생: {e}"

def generate_new_titles(analysis_result, query, openai_api_key, num_titles=10):
    """새로운 제목 생성"""
    if not openai_api_key:
        return "OpenAI API 키가 설정되지 않았습니다."
    
    try:
        client = OpenAI(api_key=openai_api_key)
        prompt = prompts.create_title_generation_prompt(query, analysis_result, num_titles)
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": prompts.get_system_prompt_generation()},
                {"role": "user", "content": prompt}
            ],
            temperature=0.8,
            max_tokens=3000
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        return f"제목 생성 중 오류 발생: {e}"

def main():
    # 헤더
    st.markdown('<h1 class="main-header">✨ KeiaiLAB 블로그 글생성기</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">AI 기반 블로그 제목 분석 및 생성 도구</p>', unsafe_allow_html=True)
    
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
        
        # API 키 상태 표시
        with st.spinner("API 연결 상태 확인 중..."):
            naver_status = test_naver_api_connection(client_id, client_secret)
            openai_status = test_openai_api_connection(openai_api_key)
        
        if naver_status:
            st.success("✅ 네이버 API 연결됨")
        else:
            st.warning("⚠️ 네이버 API 연결 확인 필요")
            
        if openai_status:
            st.success("✅ OpenAI API 연결됨")
        else:
            st.warning("⚠️ OpenAI API 연결 확인 필요")
        
        st.markdown("---")
        
        # 검색 설정
        st.markdown("### 🔍 검색 설정")
        search_count = st.slider("분석할 블로그 개수", 10, 100, 50)
        sort_method = st.radio("정렬 방식", ["날짜순 (최신순)", "정확도순"])
        sort_value = 'date' if sort_method == "날짜순 (최신순)" else 'sim'
        
        st.markdown("---")
        
        # 분석 설정
        st.markdown("### 🧠 분석 설정")
        analysis_types = prompts.get_available_analysis_types()
        analysis_labels = [f"{config['name']} - {config['description']}" for config in analysis_types.values()]
        analysis_keys = list(analysis_types.keys())
        
        selected_analysis = st.selectbox(
            "분석 유형 선택",
            options=analysis_keys,
            format_func=lambda x: analysis_types[x]['name'],
            help="원하는 분석 유형을 선택하세요"
        )
        
        st.markdown("---")
        
        # 제목 생성 설정
        st.markdown("### ✨ 제목 생성 설정")
        num_titles = st.slider("생성할 제목 개수", 5, 30, 10)
    
    # 메인 영역
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### 🎯 키워드 입력")
        query = st.text_input(
            "분석할 키워드를 입력하세요",
            placeholder="예: 반려동물, 요리, 여행 등",
            help="네이버 블로그에서 검색할 키워드를 입력하세요"
        )
    
    with col2:
        st.markdown("### 🚀 실행")
        # 분석 실행
        if st.button("분석 시작", key="main_analysis_button", use_container_width=True):
            if not query.strip():
                st.warning("키워드를 입력해주세요!")
                return
            
            # 세션 상태 초기화
            if 'analysis_result' in st.session_state:
                del st.session_state.analysis_result
            if 'titles' in st.session_state:
                del st.session_state.titles
            
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
                    
                    st.session_state.analysis_result = analysis_result
                    st.session_state.titles = titles
                    st.session_state.query = query
                    
                    # 탭으로 결과 분리
                    tab1, tab2 = st.tabs(["📝 수집된 제목 목록", "📋 AI 분석 결과"])
                    
                    with tab1:
                        st.markdown("#### 🔍 검색된 블로그 제목들")
                        for i, title in enumerate(titles, 1):
                            st.write(f"**{i:2d}.** {title}")
                    
                    with tab2:
                        st.markdown("#### 🧠 AI 분석 보고서")
                        st.markdown(f'<div class="result-container">{analysis_result}</div>', unsafe_allow_html=True)
                    
                    # 제목 생성 옵션
                    st.markdown("### ✨ 새로운 제목 생성")
                    
                    col1, col2 = st.columns([1, 1])
                    with col1:
                        if st.button("🎯 새로운 제목 생성", key="generate_titles_button", use_container_width=True):
                            with st.spinner(f"✨ {num_titles}개의 새로운 제목 생성 중..."):
                                generated_titles = generate_new_titles(analysis_result, query, openai_api_key, num_titles)
                            
                            st.session_state.generated_titles = generated_titles
                            
                            # 생성된 제목 표시
                            st.markdown("### 🎉 생성된 새로운 제목들")
                            st.markdown(f'<div class="result-container">{generated_titles}</div>', unsafe_allow_html=True)
                    
                    with col2:
                        if st.button("💾 결과 다운로드", key="download_results_button", use_container_width=True):
                            if 'analysis_result' in st.session_state:
                                # 결과 파일 생성
                                timestamp = time.strftime("%Y%m%d_%H%M%S")
                                filename = f"blog_analysis_{query}_{timestamp}.txt"
                                
                                content = f"""=== KeiaiLAB 블로그 제목 분석 및 생성 결과 ===
검색 키워드: {query}
분석 일시: {time.strftime('%Y-%m-%d %H:%M:%S')}
분석 유형: {analysis_types[selected_analysis]['name']}

=== 심화 분석 결과 ===
{st.session_state.analysis_result}

"""
                                
                                if 'generated_titles' in st.session_state:
                                    content += f"""
=== 생성된 새로운 블로그 제목들 ===
{st.session_state.generated_titles}
"""
                                
                                st.download_button(
                                    label="📄 텍스트 파일 다운로드",
                                    data=content,
                                    file_name=filename,
                                    mime="text/plain",
                                    use_container_width=True
                                )
            else:
                st.error("검색 결과에서 제목을 추출할 수 없습니다.")
        else:
            st.error("블로그 검색에 실패했습니다. API 설정을 확인해주세요.")
    
    # 푸터
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; padding: 2rem;">
        <p><strong>KeiaiLAB 블로그 글생성기</strong> | AI 기반 블로그 제목 분석 및 생성 도구</p>
        <p>Powered by GPT-4o & Naver Search API</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main() 