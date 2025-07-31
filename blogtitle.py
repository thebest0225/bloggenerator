import urllib.request
import urllib.parse
import json
import os
import time
import re
from collections import Counter
from openai import OpenAI
import prompts

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
        print("Error: .env 파일에서 OPENAI_API_KEY를 찾을 수 없습니다. GPT 분석 기능이 필요합니다.")
        return None, None, None
    
    return client_id, client_secret, openai_api_key

def search_naver_blog(query, client_id, client_secret, display=50, sort='date'):
    """
    네이버 블로그 검색 API를 호출하여 검색 결과를 반환합니다.
    """
    enc_text = urllib.parse.quote(query)
    url = f"https://openapi.naver.com/v1/search/blog.json?query={enc_text}&display={display}&sort={sort}"
    
    request = urllib.request.Request(url)
    request.add_header("X-Naver-Client-Id", client_id)
    request.add_header("X-Naver-Client-Secret", client_secret)
    
    try:
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

def extract_blog_data(search_result):
    """
    검색 결과에서 블로그 제목과 설명을 추출하여 리스트로 반환합니다.
    """
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
    """
    제목들의 기본적인 패턴을 분석합니다.
    """
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
    
    # 길이별 분포
    for title in titles:
        length_range = f"{(len(title)//10)*10}-{(len(title)//10)*10+9}"
        analysis['length_distribution'][length_range] = analysis['length_distribution'].get(length_range, 0) + 1
    
    # 패턴 분석
    for title in titles:
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
        
        # 간단한 키워드 추출 (2글자 이상)
        words = re.findall(r'[가-힣]{2,}', title)
        analysis['keyword_frequency'].update(words)
    
    return analysis





def analyze_with_gpt(titles, descriptions, query, openai_api_key, analysis_type='comprehensive'):
    """
    GPT-4o를 사용하여 블로그 제목들을 심화 분석합니다.
    """
    if not openai_api_key:
        return "OpenAI API 키가 설정되지 않았습니다."
    
    if not titles:
        return "분석할 블로그 제목이 없습니다."
    
    try:
        client = OpenAI(api_key=openai_api_key)
        
        # 기본 패턴 분석
        basic_analysis = analyze_title_patterns(titles)
        
        # prompts.py에서 분석 프롬프트 가져오기
        prompt = prompts.get_analysis_prompt(analysis_type, query, titles, descriptions, basic_analysis)
        
        print("GPT-4o로 블로그 제목 심화 분석 중...")
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system", 
                    "content": prompts.get_system_prompt_analysis()
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

def generate_new_titles(analysis_result, query, openai_api_key, num_titles=10):
    """
    분석 결과를 바탕으로 새로운 블로그 제목들을 생성합니다.
    """
    if not openai_api_key:
        return "OpenAI API 키가 설정되지 않았습니다."
    
    try:
        client = OpenAI(api_key=openai_api_key)
        
        # prompts.py에서 제목 생성 프롬프트 가져오기
        prompt = prompts.create_title_generation_prompt(query, analysis_result, num_titles)
        
        print(f"GPT-4o로 새로운 블로그 제목 {num_titles}개 생성 중...")
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system", 
                    "content": prompts.get_system_prompt_generation()
                },
                {
                    "role": "user", 
                    "content": prompt
                }
            ],
            temperature=0.8,
            max_tokens=3000
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        return f"제목 생성 중 오류 발생: {e}"

def display_blog_titles(search_result):
    """
    검색 결과에서 블로그 제목들을 출력합니다.
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

def get_number_input(prompt, min_val=1, max_val=50, default=10):
    """
    숫자 입력을 받고 유효성을 검사합니다.
    """
    while True:
        user_input = input(f"{prompt} ({min_val}-{max_val}, 기본값: {default}): ").strip()
        
        if not user_input:
            return default
        
        try:
            num = int(user_input)
            if min_val <= num <= max_val:
                return num
            else:
                print(f"❌ {min_val}과 {max_val} 사이의 숫자를 입력해주세요.")
        except ValueError:
            print("❌ 올바른 숫자를 입력해주세요.")

def save_results_to_file(query, analysis_result, generated_titles):
    """
    분석 결과와 생성된 제목들을 파일로 저장합니다.
    """
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    filename = f"blog_analysis_{query}_{timestamp}.txt"
    
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f"=== 블로그 제목 분석 및 생성 결과 ===\n")
            f.write(f"검색 키워드: {query}\n")
            f.write(f"분석 일시: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            f.write("=== 심화 분석 결과 ===\n")
            f.write(analysis_result)
            f.write("\n\n")
            
            f.write("=== 생성된 새로운 블로그 제목들 ===\n")
            f.write(generated_titles)
            f.write("\n")
        
        print(f"\n💾 결과가 '{filename}' 파일로 저장되었습니다.")
        
    except Exception as e:
        print(f"❌ 파일 저장 중 오류 발생: {e}")

def main():
    """
    메인 함수: 네이버 블로그 검색, 심화 분석, 새 제목 생성을 실행합니다.
    """
    print("="*60)
    print("🚀 고도화된 블로그 제목 분석 및 생성 프로그램")
    print("="*60)
    
    # 환경변수 로드
    client_id, client_secret, openai_api_key = load_env_variables()
    if not client_id or not client_secret or not openai_api_key:
        return
    
    print(f"✅ 네이버 클라이언트 ID: {client_id}")
    print(f"✅ OpenAI API 키: {openai_api_key[:8]}...")
    print()
    
    while True:
        # 검색 키워드 입력
        query = input("🔍 분석할 키워드를 입력하세요 (종료: 'quit' 또는 'exit'): ").strip()
        
        if query.lower() in ['quit', 'exit', '종료']:
            print("👋 프로그램을 종료합니다.")
            break
        
        if not query:
            print("❌ 키워드를 입력해주세요.")
            continue
        
        # 검색 개수 설정
        search_count = get_number_input("📊 분석할 블로그 개수를 설정하세요", 10, 100, 50)
        
        # 정렬 방식 선택
        print("\n📈 정렬 방식을 선택하세요:")
        print("1. 날짜순 (최신순)")
        print("2. 정확도순")
        
        sort_choice = input("선택 (1 또는 2, 기본값: 1): ").strip()
        sort_method = 'date' if sort_choice != '2' else 'sim'
        sort_name = '날짜순' if sort_method == 'date' else '정확도순'
        
        print(f"\n🔍 '{query}' 검색 중... ({sort_name}, {search_count}개)")
        
        # 네이버 블로그 검색 실행
        result = search_naver_blog(query, client_id, client_secret, display=search_count, sort=sort_method)
        
        if result:
            display_blog_titles(result)
            
            # 블로그 데이터 추출
            titles, descriptions = extract_blog_data(result)
            
            print("\n" + "="*60)
            print("🧠 심화 분석 시작")
            print("="*60)
            
            # GPT 심화 분석 실행
            analysis_result = analyze_with_gpt(titles, descriptions, query, openai_api_key)
            
            print("\n" + "="*60)
            print("📋 블로그 제목 심화 분석 결과")
            print("="*60)
            print(analysis_result)
            
            # 새로운 제목 생성 옵션
            print("\n" + "="*60)
            print("✨ 새로운 블로그 제목 생성")
            print("="*60)
            
            generate_choice = input("분석 결과를 바탕으로 새로운 제목을 생성하시겠습니까? (y/n, 기본값: y): ").strip().lower()
            
            if generate_choice != 'n':
                # 생성할 제목 개수 입력
                num_titles = get_number_input("💡 생성할 제목 개수를 설정하세요", 5, 30, 10)
                
                # 새로운 제목 생성
                generated_titles = generate_new_titles(analysis_result, query, openai_api_key, num_titles)
                
                print("\n" + "="*60)
                print(f"🎯 새롭게 생성된 블로그 제목 {num_titles}개")
                print("="*60)
                print(generated_titles)
                
                # 결과 저장 옵션
                save_choice = input("\n💾 분석 결과와 생성된 제목을 파일로 저장하시겠습니까? (y/n, 기본값: y): ").strip().lower()
                
                if save_choice != 'n':
                    save_results_to_file(query, analysis_result, generated_titles)
            
        else:
            print("❌ 검색에 실패했습니다.")
        
        print("\n" + "="*80)
        print()

if __name__ == "__main__":
    main() 