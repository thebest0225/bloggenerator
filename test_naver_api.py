import urllib.request
import urllib.parse
import urllib.error
import json

def test_naver_api():
    client_id = 'yWjoRi9eiWKCk4SOTO47'
    client_secret = 'iIcoJD9rsC'
    query = 'test'
    
    enc_text = urllib.parse.quote(query)
    url = f'https://openapi.naver.com/v1/search/blog.json?query={enc_text}&display=1&sort=date'
    
    request = urllib.request.Request(url)
    request.add_header('X-Naver-Client-Id', client_id)
    request.add_header('X-Naver-Client-Secret', client_secret)
    
    try:
        response = urllib.request.urlopen(request)
        print(f'응답 코드: {response.getcode()}')
        
        if response.getcode() == 200:
            response_body = response.read()
            result = json.loads(response_body.decode('utf-8'))
            print(f'검색 결과 수: {result.get("total", 0)}')
            print('API 호출 성공!')
            return True
        else:
            print('API 호출 실패')
            return False
            
    except urllib.error.HTTPError as e:
        print(f'HTTP 오류 {e.code}: {e.read().decode("utf-8")}')
        return False
    except Exception as e:
        print(f'오류: {e}')
        return False

if __name__ == "__main__":
    test_naver_api() 