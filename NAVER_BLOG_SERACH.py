import urllib.request
import urllib.parse
import json
import os
import time
from openai import OpenAI

def load_env_variables():
    """
    .env 파일에서 네이버 클라이언트 정보와 OpenAI API 키를 읽어옵니다.
    """
    env_vars = {}
    try:
        with open('.env', 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key.strip()] = value.strip()
    except FileNotFoundError:
        print("Error: .env 파일을 찾을 수 없습니다.")
        print("다음 내용으로 .env 파일을 생성해주세요:")
        print("NAVER_CLIENT_ID=your_naver_client_id")
        print("NAVER_CLIENT_SECRET_KEY=your_naver_client_secret")
        print("OPENAI_API_KEY=your_openai_api_key")
        return None, None, None
    
    client_id = env_vars.get('NAVER_CLIENT_ID')
    client_secret = env_vars.get('NAVER_CLIENT_SECRET_KEY')
    openai_api_key = env_vars.get('OPENAI_API_KEY')
    
    if not client_id or not client_secret:
        print("Error: .env 파일에서 네이버 클라이언트 정보를 찾을 수 없습니다.")
        return None, None, None
    
    if not openai_api_key:
        print("Warning: .env 파일에서 OPENAI_API_KEY를 찾을 수 없습니다. GPT 분석 기능을 사용할 수 없습니다.")
    
    return client_id, client_secret, openai_api_key

def search_naver_blog(query, client_id, client_secret, display=30, sort='date'):
    """
    네이버 블로그 검색 API를 호출하여 검색 결과를 반환합니다.
    
    Args:
        query (str): 검색할 키워드
        client_id (str): 네이버 클라이언트 ID
        client_secret (str): 네이버 클라이언트 시크릿
        display (int): 가져올 검색 결과 개수 (최대 100)
        sort (str): 정렬 방법 ('sim': 정확도순, 'date': 날짜순)
    
    Returns:
        dict: 검색 결과 JSON 데이터
    """
    # 검색어를 URL 인코딩
    enc_text = urllib.parse.quote(query)
    
    # API URL 구성
    url = f"https://openapi.naver.com/v1/search/blog.json?query={enc_text}&display={display}&sort={sort}"
    
    # HTTP 요청 생성
    request = urllib.request.Request(url)
    request.add_header("X-Naver-Client-Id", client_id)
    request.add_header("X-Naver-Client-Secret", client_secret)
    
    try:
        # API 호출
        response = urllib.request.urlopen(request)
        rescode = response.getcode()
        
        if rescode == 200:
            response_body = response.read()
            return json.loads(response_body.decode('utf-8'))
        else:
            print(f"Error Code: {rescode}")
            return None
            
    except Exception as e:
        print(f"API 호출 중 오류 발생: {e}")
        return None

def clean_html_tags(text):
    """
    HTML 태그를 제거하고 특수문자를 정리합니다.
    """
    text = text.replace('<b>', '').replace('</b>', '')
    text = text.replace('&quot;', '"').replace('&lt;', '<').replace('&gt;', '>')
    text = text.replace('&amp;', '&').replace('&#39;', "'")
    return text.strip()

def extract_blog_titles(search_result):
    """
    검색 결과에서 블로그 제목들을 추출하여 리스트로 반환합니다.
    
    Args:
        search_result (dict): 네이버 블로그 검색 결과
    
    Returns:
        list: 정제된 블로그 제목 리스트
    """
    if not search_result or 'items' not in search_result:
        return []
    
    titles = []
    for item in search_result['items']:
        clean_title = clean_html_tags(item['title'])
        titles.append(clean_title)
    
    return titles

def create_blog_analysis_prompt(query, titles, analysis_type="comprehensive"):
    """
    블로그 제목 분석을 위한 고도화된 프롬프트를 생성합니다.
    
    Args:
        query (str): 검색 키워드
        titles (list): 블로그 제목 리스트
        analysis_type (str): 분석 유형
    
    Returns:
        str: 분석용 프롬프트
    """
    
    titles_text = "\n".join([f"{i+1}. {title}" for i, title in enumerate(titles)])
    
    if analysis_type == "comprehensive":
        prompt = f"""
다음은 '{query}' 키워드로 검색한 네이버 블로그 제목들입니다. 이 제목들을 종합적으로 분석해주세요.

=== 블로그 제목 목록 ===
{titles_text}

=== 분석 요청 사항 ===
다음 관점에서 상세하게 분석해주세요:

1. **트렌드 및 인사이트 분석**
   - 현재 '{query}' 관련해서 어떤 주제들이 인기인지
   - 시기적 특성이나 계절성이 보이는지
   - 새로운 트렌드나 변화하는 관심사는 무엇인지

2. **콘텐츠 카테고리 분류**
   - 제목들을 주요 카테고리별로 분류
   - 각 카테고리의 비중과 특징
   - 가장 많이 다뤄지는 하위 주제들

3. **타이틀 구조 및 SEO 분석**
   - 효과적인 제목 패턴 분석 (길이, 구조, 키워드 배치)
   - 클릭을 유도하는 제목 요소들
   - SEO 관점에서 잘 작성된 제목들의 특징

4. **감정 및 톤 분석**
   - 제목들의 전반적인 감정 톤 (긍정적/부정적/중립적)
   - 호기심을 자극하는 표현 방식
   - 독자의 관심을 끄는 언어적 특징

5. **키워드 및 언어 패턴**
   - 자주 등장하는 핵심 키워드들
   - 함께 사용되는 연관 단어들
   - 특별한 언어적 패턴이나 표현법

6. **콘텐츠 예측 및 추천**
   - 이 제목들을 보고 예상되는 콘텐츠 품질
   - 현재 부족해 보이는 콘텐츠 영역
   - 새로운 콘텐츠 아이디어 제안

7. **시장 기회 분석**
   - 경쟁이 치열한 영역과 틈새 영역
   - 차별화할 수 있는 접근 방식
   - 블로그 운영자에게 주는 인사이트

각 분석은 구체적인 예시와 함께 제시해주시고, 실용적인 조언도 포함해주세요.
"""
    
    elif analysis_type == "trend":
        prompt = f"""
'{query}' 키워드로 검색한 네이버 블로그 제목들을 분석하여 현재 트렌드와 시장 인사이트를 도출해주세요.

=== 블로그 제목 목록 ===
{titles_text}

=== 트렌드 분석 요청 ===
1. 현재 가장 주목받는 하위 주제 TOP 5
2. 새롭게 떠오르는 트렌드 키워드
3. 시기별 특성 (계절성, 이벤트성 등)
4. 향후 예상되는 트렌드 방향
5. 블로그 시장에서의 기회 영역
"""
    
    elif analysis_type == "seo":
        prompt = f"""
'{query}' 관련 블로그 제목들을 SEO와 마케팅 관점에서 분석해주세요.

=== 블로그 제목 목록 ===
{titles_text}

=== SEO 분석 요청 ===
1. 효과적인 제목 구조 패턴
2. 클릭률을 높이는 제목 요소들
3. 키워드 활용 전략
4. 제목 길이와 가독성
5. 개선할 수 있는 제목 예시 3개 제안
"""
    
    return prompt

def analyze_with_gpt(titles, query, openai_api_key, analysis_type="comprehensive"):
    """
    OpenAI GPT-4o를 사용하여 블로그 제목들을 분석합니다.
    
    Args:
        titles (list): 블로그 제목 리스트
        query (str): 검색 키워드
        openai_api_key (str): OpenAI API 키
        analysis_type (str): 분석 유형
    
    Returns:
        str: GPT 분석 결과
    """
    if not openai_api_key:
        return "OpenAI API 키가 설정되지 않았습니다."
    
    if not titles:
        return "분석할 블로그 제목이 없습니다."
    
    try:
        client = OpenAI(api_key=openai_api_key)
        
        prompt = create_blog_analysis_prompt(query, titles, analysis_type)
        
        print("GPT-4o로 블로그 제목 분석 중...")
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system", 
                    "content": "당신은 블로그 콘텐츠와 디지털 마케팅 전문가입니다. 블로그 제목들을 분석하여 트렌드, SEO, 마케팅 인사이트를 제공하는 것이 주요 역할입니다. 분석은 구체적이고 실용적이어야 하며, 데이터 기반의 객관적인 관점을 유지해야 합니다."
                },
                {
                    "role": "user", 
                    "content": prompt
                }
            ],
            temperature=0.7,
            max_tokens=4000
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        return f"GPT 분석 중 오류 발생: {e}"

def display_blog_titles(search_result):
    """
    검색 결과에서 블로그 제목들을 출력합니다.
    
    Args:
        search_result (dict): 네이버 블로그 검색 결과
    """
    if not search_result or 'items' not in search_result:
        print("검색 결과가 없습니다.")
        return
    
    items = search_result['items']
    total = search_result.get('total', 0)
    
    print(f"\n=== 검색 결과 총 {total}개 중 상위 {len(items)}개 ===\n")
    
    for i, item in enumerate(items, 1):
        title = clean_html_tags(item['title'])
        print(f"{i:2d}. {title}")
    
    print()

def main():
    """
    메인 함수: 키워드를 입력받고 네이버 블로그 검색 및 GPT 분석을 실행합니다.
    """
    print("=== 네이버 블로그 검색 + GPT 분석 프로그램 ===")
    
    # 환경변수 로드
    client_id, client_secret, openai_api_key = load_env_variables()
    if not client_id or not client_secret:
        return
    
    print(f"네이버 클라이언트 ID: {client_id}")
    if openai_api_key:
        print(f"OpenAI API 키: {openai_api_key[:8]}...")
    print()
    
    # 검색 키워드 입력
    while True:
        query = input("검색할 키워드를 입력하세요 (종료: 'quit' 또는 'exit'): ").strip()
        
        if query.lower() in ['quit', 'exit', '종료']:
            print("프로그램을 종료합니다.")
            break
        
        if not query:
            print("키워드를 입력해주세요.")
            continue
        
        # 정렬 방식 선택
        print("\n정렬 방식을 선택하세요:")
        print("1. 날짜순 (최신순) - 웹사이트와 더 유사")
        print("2. 정확도순")
        
        sort_choice = input("선택 (1 또는 2, 기본값: 1): ").strip()
        sort_method = 'date' if sort_choice != '2' else 'sim'
        sort_name = '날짜순' if sort_method == 'date' else '정확도순'
        
        print(f"\n'{query}' 검색 중... ({sort_name})")
        
        # 네이버 블로그 검색 실행
        result = search_naver_blog(query, client_id, client_secret, display=30, sort=sort_method)
        
        if result:
            display_blog_titles(result)
            
            # GPT 분석 옵션
            if openai_api_key:
                print("\n=== GPT-4o 분석 옵션 ===")
                print("1. 종합 분석 (트렌드, SEO, 카테고리 등 전체)")
                print("2. 트렌드 분석 (현재 인기 주제, 새로운 트렌드)")
                print("3. SEO 분석 (제목 구조, 키워드 활용)")
                print("4. 분석 건너뛰기")
                
                analysis_choice = input("\n분석 유형을 선택하세요 (1-4, 기본값: 1): ").strip()
                
                if analysis_choice != '4':
                    analysis_types = {
                        '1': 'comprehensive',
                        '2': 'trend', 
                        '3': 'seo'
                    }
                    analysis_type = analysis_types.get(analysis_choice, 'comprehensive')
                    
                    # 블로그 제목 추출
                    titles = extract_blog_titles(result)
                    
                    # GPT 분석 실행
                    analysis_result = analyze_with_gpt(titles, query, openai_api_key, analysis_type)
                    
                    print("\n" + "="*60)
                    print("🤖 GPT-4o 블로그 제목 분석 결과")
                    print("="*60)
                    print(analysis_result)
                    print("="*60)
            else:
                print("\n⚠️  GPT 분석을 사용하려면 .env 파일에 OPENAI_API_KEY를 설정해주세요.")
        else:
            print("검색에 실패했습니다.")
        
        print("\n" + "-" * 80)

if __name__ == "__main__":
    main()