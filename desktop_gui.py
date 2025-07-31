import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
import customtkinter as ctk
import urllib.request
import urllib.parse
import urllib.error
import json
import re
import time
import threading
import os
import sys
import webbrowser
import tempfile
import shutil
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("OpenAI 라이브러리가 설치되지 않았습니다. 'pip install openai' 명령으로 설치해주세요.")

try:
    import prompts
    PROMPTS_AVAILABLE = True
except ImportError:
    PROMPTS_AVAILABLE = False
    print("prompts.py 파일이 없습니다.")

class BlogAnalyzerApp:
    def __init__(self, root):
        self.root = root
        
        # CustomTkinter 테마 설정
        ctk.set_appearance_mode("light")  # 라이트 모드
        ctk.set_default_color_theme("blue")  # 파란색 테마
        
        self.root.title("📝 KeiaiLAB 블로그 글생성기 by 혁")
        self.root.geometry("1400x900")  # 크기를 조금 더 크게
        
        # 변수 초기화
        self.client_id = None
        self.client_secret = None
        self.openai_api_key = None
        self.search_result = None
        self.titles = []
        self.descriptions = []
        self.analysis_result = ""
        self.last_blog_settings = None  # 마지막 블로그 설정 저장용
        self.last_generated_blog = None  # 마지막 생성된 블로그 내용 저장용
        self.last_generated_images = []  # 마지막 생성된 이미지들 저장용
        self.blog_folder_path = None  # 블로그 폴더 경로 저장용
        self.current_theme = "light"  # 현재 테마 상태
        
        # 환경변수 로드
        self.load_env_variables()
        
        # 저장된 블로그 설정 불러오기
        self.load_settings_from_file()
        
        # 저장된 테마 설정 불러오기
        self.load_theme_settings()
        
        # GUI 구성
        self.create_widgets()
        
        # 스타일 설정
        self.setup_styles()
    
    def load_env_variables(self):
        """환경변수 로드"""
        env_vars = {}
        
        # PyInstaller 환경에서 파일 경로 찾기
        if getattr(sys, 'frozen', False):
            # PyInstaller로 패키징된 환경
            bundle_dir = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
        else:
            # 개발 환경
            bundle_dir = os.path.dirname(os.path.abspath(__file__))
        
        env_file_path = os.path.join(bundle_dir, '.env')
        
        try:
            with open(env_file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        env_vars[key.strip()] = value.strip()
        except FileNotFoundError:
            messagebox.showerror("오류", f".env 파일을 찾을 수 없습니다.\n경로: {env_file_path}\n\n다음 내용으로 .env 파일을 생성해주세요:\nNAVER_CLIENT_ID=your_id\nNAVER_CLIENT_SECRET_KEY=your_secret\nOPENAI_API_KEY=your_key")
            return
        
        self.client_id = env_vars.get('NAVER_CLIENT_ID')
        self.client_secret = env_vars.get('NAVER_CLIENT_SECRET_KEY')
        self.openai_api_key = env_vars.get('OPENAI_API_KEY')
        
                # 필수 API 키 체크
        if not all([self.client_id, self.client_secret, self.openai_api_key]):
            messagebox.showerror("오류", "필수 API 키가 올바르게 설정되지 않았습니다.\n.env 파일을 확인해주세요.")

    def load_theme_settings(self):
        """저장된 테마 설정 불러오기"""
        try:
            if os.path.exists('theme_settings.json'):
                with open('theme_settings.json', 'r', encoding='utf-8') as f:
                    theme_data = json.load(f)
                    saved_theme = theme_data.get('theme', 'light')
                    self.current_theme = saved_theme
                    ctk.set_appearance_mode(saved_theme)
            else:
                # 기본값으로 라이트 모드 설정
                self.current_theme = "light"
                ctk.set_appearance_mode("light")
        except Exception as e:
            print(f"테마 설정 불러오기 오류: {e}")
            self.current_theme = "light"
            ctk.set_appearance_mode("light")
    
    def save_theme_settings(self):
        """테마 설정 저장하기"""
        try:
            theme_data = {'theme': self.current_theme}
            with open('theme_settings.json', 'w', encoding='utf-8') as f:
                json.dump(theme_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"테마 설정 저장 오류: {e}")
    
    def toggle_theme(self):
        """다크모드/라이트모드 전환"""
        if self.current_theme == "light":
            self.current_theme = "dark"
            ctk.set_appearance_mode("dark")
        else:
            self.current_theme = "light"
            ctk.set_appearance_mode("light")
        
        # 설정 저장
        self.save_theme_settings()
        
        # 토글 스위치 상태 업데이트
        if hasattr(self, 'theme_switch'):
            if self.current_theme == "dark":
                self.theme_switch.select()
            else:
                self.theme_switch.deselect()
    
    def create_themed_toplevel(self, parent, title, geometry):
        """현재 테마를 적용한 새 창 생성"""
        window = tk.Toplevel(parent)
        window.title(title)
        window.geometry(geometry)
        
        # 현재 테마에 맞는 배경색 설정
        if self.current_theme == "dark":
            window.configure(bg='#212121')
        else:
            window.configure(bg='#fafafa')
        
        return window
    
    def setup_styles(self):
        """스타일 설정"""
        style = ttk.Style()
        
        # 현대적인 테마 설정
        style.theme_use('clam')
        
        # 메인 버튼 스타일 (검은색 텍스트)
        style.configure('Primary.TButton', 
                       font=('맑은 고딕', 10, 'bold'),
                       foreground='black',
                       background='#e6f3ff',
                       borderwidth=2,
                       relief='raised')
        
        # 보조 버튼 스타일
        style.configure('Secondary.TButton', 
                       font=('맑은 고딕', 9),
                       foreground='#2c3e50',
                       background='#f0fff0')
        
        # 카테고리 버튼 스타일 추가
        style.configure('Category.TButton', 
                       font=('맑은 고딕', 10),
                       foreground='#2c3e50',
                       background='#e8f4fd',
                       borderwidth=1,
                       relief='raised')
        
        # 라벨 스타일
        style.configure('Title.TLabel',
                       font=('맑은 고딕', 12, 'bold'),
                       foreground='#2c3e50',
                       background='#fafafa')
        
        style.configure('Subtitle.TLabel',
                       font=('맑은 고딕', 9),
                       foreground='#34495e',
                       background='#fafafa')
    
    def create_widgets(self):
        """GUI 위젯 생성"""
        # 메인 프레임
        main_frame = ctk.CTkFrame(self.root)
        main_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        
        # 헤더 프레임 (제목 + 다크모드 토글)
        header_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        header_frame.grid(row=0, column=0, columnspan=3, sticky="ew", pady=(20, 10))
        
        # 제목
        title_label = ctk.CTkLabel(header_frame, text="📝 KeiaiLAB 블로그 글생성기 by 혁", 
                                  font=ctk.CTkFont(family="맑은 고딕", size=24, weight="bold"),
                                  text_color="#1f538d")
        title_label.grid(row=0, column=0, sticky="w", padx=(0, 20))
        
        # 다크모드 토글 프레임
        theme_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        theme_frame.grid(row=0, column=1, sticky="e")
        
        theme_label = ctk.CTkLabel(theme_frame, text="🌙 다크모드:", 
                                  font=ctk.CTkFont(family="맑은 고딕", size=12, weight="bold"))
        theme_label.grid(row=0, column=0, padx=(0, 10))
        
        # 다크모드 토글 스위치
        self.theme_switch = ctk.CTkSwitch(theme_frame, text="", width=50, height=24,
                                         command=self.toggle_theme)
        self.theme_switch.grid(row=0, column=1)
        
        # 현재 테마에 따라 스위치 상태 설정
        if self.current_theme == "dark":
            self.theme_switch.select()
        else:
            self.theme_switch.deselect()
        
        header_frame.columnconfigure(0, weight=1)
        
        subtitle_label = ctk.CTkLabel(main_frame, text="AI 기반 블로그 제목 분석 및 신규 제목 생성 도구",
                                     font=ctk.CTkFont(family="맑은 고딕", size=14),
                                     text_color="#5a5a5a")
        subtitle_label.grid(row=1, column=0, columnspan=3, pady=(0, 30))
        
        # 좌측 설정 패널
        self.create_settings_panel(main_frame)
        
        # 우측 결과 패널
        self.create_results_panel(main_frame)
        
        # 하단 상태바
        self.create_status_bar(main_frame)
        
        # 그리드 가중치 설정
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=2)
        main_frame.rowconfigure(2, weight=1)
    
    def create_settings_panel(self, parent):
        """설정 패널 생성"""
        settings_frame = ctk.CTkFrame(parent)
        settings_frame.grid(row=2, column=0, sticky="nsew", padx=(0, 20), pady=(0, 20))
        
        # 설정 제목
        settings_title = ctk.CTkLabel(settings_frame, text="🔧 설정", 
                                     font=ctk.CTkFont(family="맑은 고딕", size=18, weight="bold"),
                                     text_color="#1f538d")
        settings_title.grid(row=0, column=0, sticky="w", padx=20, pady=(10, 5))
        
        # 키워드 입력
        keyword_label = ctk.CTkLabel(settings_frame, text="🔍 검색 키워드:",
                                    font=ctk.CTkFont(family="맑은 고딕", size=14, weight="bold"))
        keyword_label.grid(row=1, column=0, sticky="w", padx=20, pady=(5, 2))
        
        # 안내 메시지
        guide_label = ctk.CTkLabel(settings_frame, text="직접 키워드를 입력하거나, 카테고리에서 선택하세요", 
                                  font=ctk.CTkFont(family="맑은 고딕", size=12),
                                  text_color="#666666")
        guide_label.grid(row=2, column=0, sticky="w", padx=20, pady=(0, 5))
        
        # 키워드 입력 프레임
        keyword_frame = ctk.CTkFrame(settings_frame, fg_color="transparent")
        keyword_frame.grid(row=3, column=0, sticky="ew", padx=20, pady=(0, 8))
        
        self.keyword_var = tk.StringVar()
        self.keyword_entry = ctk.CTkEntry(keyword_frame, textvariable=self.keyword_var, width=300,
                                         font=ctk.CTkFont(family="맑은 고딕", size=12),
                                         placeholder_text="키워드를 입력하세요 (예: 다이어트, 투자, 여행)")
        self.keyword_entry.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        
        # 엔터 키 바인딩 추가 (더 안정적인 방식)
        def on_enter_key(event):
            """엔터 키 처리"""
            self.start_analysis()
            return "break"  # 이벤트 전파 중단
        
        self.keyword_entry.bind('<Return>', on_enter_key)
        self.keyword_entry.bind('<KP_Enter>', on_enter_key)  # 숫자패드 엔터도 지원
        
        # 카테고리별 트렌드 버튼
        trend_button = ctk.CTkButton(keyword_frame, text="📈 카테고리", width=120,
                                    font=ctk.CTkFont(family="맑은 고딕", size=12, weight="bold"),
                                    command=self.show_category_selection)
        trend_button.grid(row=0, column=1)
        
        keyword_frame.columnconfigure(0, weight=1)
        
        # 검색 설정
        search_title = ctk.CTkLabel(settings_frame, text="📊 검색 설정:", 
                                   font=ctk.CTkFont(family="맑은 고딕", size=14, weight="bold"))
        search_title.grid(row=4, column=0, sticky="w", padx=20, pady=(10, 5))
        
        # 분석할 블로그 개수
        count_label = ctk.CTkLabel(settings_frame, text="분석할 블로그 개수:",
                                  font=ctk.CTkFont(family="맑은 고딕", size=12))
        count_label.grid(row=5, column=0, sticky="w", padx=20, pady=(3, 2))
        
        self.search_count_var = tk.IntVar(value=50)
        search_count_scale = ctk.CTkSlider(settings_frame, from_=10, to=100, 
                                          variable=self.search_count_var, width=300,
                                          command=self.update_search_count_label)
        search_count_scale.grid(row=6, column=0, sticky="ew", padx=20, pady=(0, 2))
        
        self.search_count_label = ctk.CTkLabel(settings_frame, text="50개",
                                              font=ctk.CTkFont(family="맑은 고딕", size=12),
                                              text_color="#1f538d")
        self.search_count_label.grid(row=7, column=0, sticky="w", padx=20, pady=(0, 8))
        
        # 정렬 방식
        sort_label = ctk.CTkLabel(settings_frame, text="정렬 방식:",
                                 font=ctk.CTkFont(family="맑은 고딕", size=12))
        sort_label.grid(row=8, column=0, sticky="w", padx=20, pady=(3, 2))
        
        self.sort_var = tk.StringVar(value="date")
        sort_frame = ctk.CTkFrame(settings_frame, fg_color="transparent")
        sort_frame.grid(row=9, column=0, sticky="ew", padx=20, pady=(0, 10))
        
        date_radio = ctk.CTkRadioButton(sort_frame, text="날짜순", variable=self.sort_var, value="date",
                                       font=ctk.CTkFont(family="맑은 고딕", size=12))
        date_radio.grid(row=0, column=0, padx=(0, 20), sticky="w")
        
        sim_radio = ctk.CTkRadioButton(sort_frame, text="정확도순", variable=self.sort_var, value="sim",
                                      font=ctk.CTkFont(family="맑은 고딕", size=12))
        sim_radio.grid(row=0, column=1, sticky="w")
        
        # 분석 설정
        analysis_title = ctk.CTkLabel(settings_frame, text="🧠 분석 설정:", 
                                     font=ctk.CTkFont(family="맑은 고딕", size=14, weight="bold"))
        analysis_title.grid(row=10, column=0, sticky="w", padx=20, pady=(8, 5))
        
        analysis_type_label = ctk.CTkLabel(settings_frame, text="분석 유형:",
                                          font=ctk.CTkFont(family="맑은 고딕", size=12))
        analysis_type_label.grid(row=11, column=0, sticky="w", padx=20, pady=(3, 2))
        
        self.analysis_type_var = tk.StringVar()
        
        # 분석 유형 옵션 설정
        if PROMPTS_AVAILABLE:
            try:
                analysis_types = prompts.get_available_analysis_types()
                analysis_options = [f"{config['name']}" for config in analysis_types.values()]
                default_value = analysis_options[0] if analysis_options else "기본 분석"
            except:
                analysis_options = ["기본 분석"]
                default_value = "기본 분석"
        else:
            analysis_options = ["기본 분석"]
            default_value = "기본 분석"
        
        analysis_combo = ctk.CTkComboBox(settings_frame, variable=self.analysis_type_var, 
                                        values=analysis_options, state="readonly", width=300,
                                        font=ctk.CTkFont(family="맑은 고딕", size=12))
        analysis_combo.set(default_value)
        analysis_combo.grid(row=12, column=0, sticky="ew", padx=20, pady=(0, 10))
        
        # 제목 생성 설정
        title_gen_title = ctk.CTkLabel(settings_frame, text="✨ 제목 생성:", 
                                      font=ctk.CTkFont(family="맑은 고딕", size=14, weight="bold"))
        title_gen_title.grid(row=13, column=0, sticky="w", padx=20, pady=(8, 5))
        
        title_count_label = ctk.CTkLabel(settings_frame, text="생성할 제목 개수:",
                                        font=ctk.CTkFont(family="맑은 고딕", size=12))
        title_count_label.grid(row=14, column=0, sticky="w", padx=20, pady=(3, 2))
        
        self.title_count_var = tk.IntVar(value=10)
        title_count_scale = ctk.CTkSlider(settings_frame, from_=5, to=30, 
                                         variable=self.title_count_var, width=300,
                                         command=self.update_title_count_label)
        title_count_scale.grid(row=15, column=0, sticky="ew", padx=20, pady=(0, 2))
        
        self.title_count_label = ctk.CTkLabel(settings_frame, text="10개",
                                             font=ctk.CTkFont(family="맑은 고딕", size=12),
                                             text_color="#1f538d")
        self.title_count_label.grid(row=16, column=0, sticky="w", padx=20, pady=(0, 10))
        
        # 실행 버튼
        self.analyze_button = ctk.CTkButton(settings_frame, text="🚀 분석 시작", 
                                           font=ctk.CTkFont(family="맑은 고딕", size=14, weight="bold"),
                                           height=40, command=self.start_analysis)
        self.analyze_button.grid(row=17, column=0, sticky="ew", padx=20, pady=(10, 10))
        
        settings_frame.columnconfigure(0, weight=1)
    
    def create_results_panel(self, parent):
        """결과 패널 생성"""
        results_frame = ctk.CTkFrame(parent)
        results_frame.grid(row=2, column=1, columnspan=2, sticky="nsew", pady=(0, 20))
        
        # 결과 제목
        results_title = ctk.CTkLabel(results_frame, text="📋 분석 결과", 
                                    font=ctk.CTkFont(family="맑은 고딕", size=18, weight="bold"),
                                    text_color="#1f538d")
        results_title.grid(row=0, column=0, columnspan=2, padx=20, pady=(20, 15))
        
        # 탭 노트북 생성
        self.notebook = ctk.CTkTabview(results_frame, width=800, height=500)
        self.notebook.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=20, pady=(0, 15))
        
        # 탭 추가
        self.notebook.add("📝 수집된 제목")
        self.notebook.add("🧠 AI 분석")
        self.notebook.add("🎉 생성된 제목")
        self.notebook.add("📄 생성된 글")
        
        # 제목 목록 탭 내용
        titles_frame = self.notebook.tab("📝 수집된 제목")
        
        self.titles_text = ctk.CTkTextbox(titles_frame, wrap="word", height=400, width=700,
                                         font=ctk.CTkFont(family="맑은 고딕", size=11))
        self.titles_text.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        titles_frame.columnconfigure(0, weight=1)
        titles_frame.rowconfigure(0, weight=1)
        
        # 분석 결과 탭 내용
        analysis_frame = self.notebook.tab("🧠 AI 분석")
        
        self.analysis_text = ctk.CTkTextbox(analysis_frame, wrap="word", height=400, width=700,
                                           font=ctk.CTkFont(family="맑은 고딕", size=11))
        self.analysis_text.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        analysis_frame.columnconfigure(0, weight=1)
        analysis_frame.rowconfigure(0, weight=1)
        
        # 새 제목 탭 내용
        new_titles_frame = self.notebook.tab("🎉 생성된 제목")
        
        # 제목 리스트박스
        self.titles_listbox = tk.Listbox(new_titles_frame, height=12, selectmode=tk.SINGLE,
                                        font=('맑은 고딕', 11), bg='white', selectbackground='#0078d4')
        self.titles_listbox.grid(row=0, column=0, sticky="nsew", padx=10, pady=(10, 10))
        
        # 제목 선택 버튼 (초기에는 비활성화)
        self.select_title_button = ctk.CTkButton(new_titles_frame, text="📝 선택한 제목으로 글 생성", 
                                                font=ctk.CTkFont(family="맑은 고딕", size=12, weight="bold"),
                                                height=35)
        self.select_title_button.grid(row=1, column=0, padx=10, pady=(0, 10))
        
        new_titles_frame.columnconfigure(0, weight=1)
        new_titles_frame.rowconfigure(0, weight=1)
        
        # 블로그 글 생성 탭 내용
        blog_content_frame = self.notebook.tab("📄 생성된 글")
        
        # 버튼 프레임 (위쪽)
        blog_buttons_frame = ctk.CTkFrame(blog_content_frame, fg_color="transparent")
        blog_buttons_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 10))
        
        self.html_preview_button = ctk.CTkButton(blog_buttons_frame, text="🌐 HTML 미리보기", 
                                                font=ctk.CTkFont(family="맑은 고딕", size=12),
                                                width=130)
        self.html_preview_button.grid(row=0, column=0, padx=(0, 10))
        
        self.copy_content_button = ctk.CTkButton(blog_buttons_frame, text="📋 내용 복사", 
                                                font=ctk.CTkFont(family="맑은 고딕", size=12),
                                                width=100)
        self.copy_content_button.grid(row=0, column=1, padx=(0, 10))
        
        self.generate_images_button = ctk.CTkButton(blog_buttons_frame, text="🎨 이미지 생성", 
                                                   font=ctk.CTkFont(family="맑은 고딕", size=12),
                                                   width=110)
        self.generate_images_button.grid(row=0, column=2)
        
        self.blog_content_text = ctk.CTkTextbox(blog_content_frame, wrap="word", height=350, width=700,
                                               font=ctk.CTkFont(family="맑은 고딕", size=11))
        self.blog_content_text.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        blog_content_frame.columnconfigure(0, weight=1)
        blog_content_frame.rowconfigure(1, weight=1)
        
        # 버튼 프레임
        button_frame = ctk.CTkFrame(results_frame, fg_color="transparent")
        button_frame.grid(row=2, column=0, columnspan=2, sticky="ew", padx=20, pady=(0, 15))
        
        self.generate_button = ctk.CTkButton(button_frame, text="🎯 새로운 제목 생성", 
                                            font=ctk.CTkFont(family="맑은 고딕", size=12, weight="bold"),
                                            width=150)
        self.generate_button.grid(row=0, column=0, padx=(0, 10))
        
        self.quick_generate_button = ctk.CTkButton(button_frame, text="⚡ 저장된 설정으로 글 생성", 
                                                  font=ctk.CTkFont(family="맑은 고딕", size=12, weight="bold"),
                                                  width=180)
        self.quick_generate_button.grid(row=0, column=1, padx=(0, 10))
        
        self.save_button = ctk.CTkButton(button_frame, text="💾 결과 저장", 
                                        font=ctk.CTkFont(family="맑은 고딕", size=12, weight="bold"),
                                        width=100)
        self.save_button.grid(row=0, column=2)
        
        # 저장된 설정 표시
        self.settings_label = ctk.CTkLabel(button_frame, text="💾 저장된 설정: 없음", 
                                          font=ctk.CTkFont(family="맑은 고딕", size=11),
                                          text_color="#666666")
        self.settings_label.grid(row=0, column=3, padx=(20, 0), sticky="e")
        
        button_frame.columnconfigure(3, weight=1)
        
        # 설정 표시 업데이트
        self.update_settings_display()
        
        results_frame.columnconfigure(0, weight=1)
        results_frame.rowconfigure(0, weight=1)
    
    def create_status_bar(self, parent):
        """상태바 생성"""
        self.status_var = tk.StringVar()
        self.status_var.set("준비됨")
        
        status_frame = ctk.CTkFrame(parent, height=60)
        status_frame.grid(row=3, column=0, columnspan=3, sticky="ew", padx=20, pady=(10, 20))
        
        status_title = ctk.CTkLabel(status_frame, text="상태:", 
                                   font=ctk.CTkFont(family="맑은 고딕", size=12, weight="bold"))
        status_title.grid(row=0, column=0, padx=(15, 10), pady=15, sticky="w")
        
        self.status_label = ctk.CTkLabel(status_frame, textvariable=self.status_var,
                                        font=ctk.CTkFont(family="맑은 고딕", size=12),
                                        text_color="#1f538d")
        self.status_label.grid(row=0, column=1, padx=(0, 20), pady=15, sticky="w")
        
        # 진행률 바
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ctk.CTkProgressBar(status_frame, variable=self.progress_var, width=300)
        self.progress_bar.grid(row=0, column=2, padx=(20, 15), pady=15, sticky="e")
        
        status_frame.columnconfigure(1, weight=1)
    
    def update_search_count_label(self, value):
        """검색 개수 라벨 업데이트"""
        self.search_count_label.configure(text=f"{int(float(value))}개")
    
    def update_title_count_label(self, value):
        """제목 개수 라벨 업데이트"""
        self.title_count_label.configure(text=f"{int(float(value))}개")
    
    def update_status(self, message):
        """상태 업데이트"""
        self.status_var.set(message)
        self.root.update_idletasks()
    
    def update_progress(self, value):
        """진행률 업데이트"""
        self.progress_var.set(value)
        self.root.update_idletasks()
    
    def search_naver_blog(self, query, display=50, sort='date'):
        """네이버 블로그 검색"""
        if not self.client_id or not self.client_secret:
            raise Exception("네이버 API 키가 설정되지 않았습니다.")
        
        enc_text = urllib.parse.quote(query)
        url = f"https://openapi.naver.com/v1/search/blog.json?query={enc_text}&display={display}&sort={sort}"
        
        request = urllib.request.Request(url)
        request.add_header("X-Naver-Client-Id", str(self.client_id))
        request.add_header("X-Naver-Client-Secret", str(self.client_secret))
        
        try:
            response = urllib.request.urlopen(request)
            if response.getcode() == 200:
                response_body = response.read()
                return json.loads(response_body.decode('utf-8'))
            else:
                raise Exception(f"API 응답 오류: HTTP {response.getcode()}")
        except Exception as e:
            raise Exception(f"API 호출 중 오류 발생: {e}")
    
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
        """GPT로 블로그 제목 분석"""
        if not OPENAI_AVAILABLE:
            raise Exception("OpenAI 라이브러리가 설치되지 않았습니다.")
        
        if not self.openai_api_key:
            raise Exception("OpenAI API 키가 설정되지 않았습니다.")
        
        client = OpenAI(api_key=self.openai_api_key)
        
        # 분석 유형에서 키 찾기
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
                user_prompt = prompts.create_analysis_prompt(query, titles, analysis_key)
            except:
                # 기본 프롬프트 사용
                system_prompt = "당신은 블로그 제목 분석 전문가입니다."
                user_prompt = f"다음 키워드 '{query}'에 대한 블로그 제목들을 분석해주세요:\n" + "\n".join([f"{i+1}. {title}" for i, title in enumerate(titles)])
        else:
            # 기본 프롬프트 사용
            system_prompt = "당신은 블로그 제목 분석 전문가입니다."
            user_prompt = f"다음 키워드 '{query}'에 대한 블로그 제목들을 분석해주세요:\n" + "\n".join([f"{i+1}. {title}" for i, title in enumerate(titles)])
        
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
    
    def generate_titles_with_gpt(self, analysis_result, query, num_titles=10):
        """새로운 블로그 제목 생성"""
        if not OPENAI_AVAILABLE:
            raise Exception("OpenAI 라이브러리가 설치되지 않았습니다.")
        
        if not self.openai_api_key:
            raise Exception("OpenAI API 키가 설정되지 않았습니다.")
        
        client = OpenAI(api_key=self.openai_api_key)
        
        if PROMPTS_AVAILABLE:
            try:
                system_prompt = prompts.get_title_generation_system_prompt()
                user_prompt = prompts.create_title_generation_prompt(query, analysis_result, num_titles)
            except:
                # 기본 프롬프트 사용
                system_prompt = "당신은 매력적인 블로그 제목을 생성하는 전문가입니다."
                user_prompt = f"키워드 '{query}'에 대해 {num_titles}개의 매력적인 블로그 제목을 생성해주세요."
        else:
            # 기본 프롬프트 사용
            system_prompt = "당신은 매력적인 블로그 제목을 생성하는 전문가입니다."
            user_prompt = f"키워드 '{query}'에 대해 {num_titles}개의 매력적인 블로그 제목을 생성해주세요."
        
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
    

    
    def start_analysis(self):
        """분석 시작"""
        keyword = self.keyword_var.get().strip()
        
        if not keyword:
            messagebox.showwarning("경고", "키워드를 입력해주세요!")
            # 포커스를 키워드 입력 필드로 이동
            self.keyword_entry.focus()
            return
        
        # 중복 실행 방지 플래그 체크
        if hasattr(self, '_analysis_running') and self._analysis_running:
            return
        
        self._analysis_running = True
        
        # 진행률 초기화
        self.update_progress(0)
        
        # 백그라운드에서 분석 실행
        thread = threading.Thread(target=self.run_analysis, args=(keyword,))
        thread.daemon = True
        thread.start()
    
    def run_analysis(self, keyword):
        """분석 실행 (백그라운드)"""
        try:
            # 1. 네이버 블로그 검색
            self.update_status("네이버 블로그 검색 중...")
            self.update_progress(20)
            
            search_count = int(self.search_count_var.get())
            sort_value = self.sort_var.get()
            
            self.search_result = self.search_naver_blog(keyword, search_count, sort_value)
            
            if not self.search_result:
                raise Exception("검색 결과가 없습니다.")
            
            # 2. 데이터 추출
            self.update_status("데이터 추출 중...")
            self.update_progress(40)
            
            self.titles, self.descriptions = self.extract_blog_data(self.search_result)
            
            if not self.titles:
                raise Exception("추출된 제목이 없습니다.")
            
            # 3. 제목 목록 표시
            self.update_status("제목 목록 표시 중...")
            self.update_progress(60)
            
            titles_content = f"=== 검색 결과 ===\n"
            titles_content += f"총 검색 결과: {self.search_result.get('total', 0):,}개\n"
            titles_content += f"수집된 제목: {len(self.titles)}개\n"
            titles_content += f"평균 제목 길이: {sum(len(t) for t in self.titles)/len(self.titles):.1f}자\n\n"
            titles_content += "=== 수집된 제목 목록 ===\n"
            
            for i, title in enumerate(self.titles, 1):
                titles_content += f"{i:2d}. {title}\n"
            
            self.titles_text.delete(1.0, tk.END)
            self.titles_text.insert(1.0, titles_content)
            
            # 4. AI 분석
            self.update_status("AI 분석 중...")
            self.update_progress(80)
            
            analysis_type = self.analysis_type_var.get()
            self.analysis_result = self.analyze_with_gpt(self.titles, self.descriptions, keyword, analysis_type)
            
            self.analysis_text.delete(1.0, tk.END)
            if self.analysis_result:  # None 체크 추가
                self.analysis_text.insert(1.0, self.analysis_result)
            
            # 5. 완료
            self.update_status("분석 완료!")
            self.update_progress(100)
            
            # 플래그 해제
            self._analysis_running = False
            
            # 알림
            messagebox.showinfo("완료", "블로그 제목 분석이 완료되었습니다!")
            
        except Exception as e:
            self.update_status(f"오류: {str(e)}")
            self.update_progress(0)
            # 플래그 해제
            self._analysis_running = False
            messagebox.showerror("오류", f"분석 중 오류가 발생했습니다:\n{str(e)}")
    
    def generate_new_titles(self):
        """새로운 제목 생성"""
        if not self.analysis_result:
            messagebox.showwarning("경고", "먼저 분석을 실행해주세요!")
            return
        
        # 중복 실행 방지 플래그 체크
        if hasattr(self, '_title_generation_running') and self._title_generation_running:
            return
        
        self._title_generation_running = True
        
        def run_generation():
            try:
                self.update_status("새로운 제목 생성 중...")
                self.update_progress(50)
                
                keyword = self.keyword_var.get().strip()
                num_titles = int(self.title_count_var.get())
                
                generated_titles = self.generate_titles_with_gpt(self.analysis_result, keyword, num_titles)
                
                # 생성된 제목들을 파싱하여 리스트박스에 추가
                self.titles_listbox.delete(0, tk.END)
                
                if generated_titles:  # None 체크 추가
                    title_lines = [line.strip() for line in generated_titles.split('\n') if line.strip()]
                    
                    # 제목만 추출 (형식: **제목 N:** [제목내용])
                    extracted_titles = []
                    for line in title_lines:
                        if '**제목' in line and ':**' in line:
                            title_start = line.find(':**') + 3
                            title = line[title_start:].strip()
                            if title:
                                extracted_titles.append(title)
                                self.titles_listbox.insert(tk.END, title)
                    
                    # 제목이 추출되지 않은 경우 전체 텍스트를 줄별로 추가
                    if not extracted_titles:
                        for line in title_lines:
                            if line and not line.startswith('#') and not line.startswith('*'):
                                self.titles_listbox.insert(tk.END, line)
                
                # 제목 선택 버튼 활성화
                self.select_title_button.configure(command=self.open_blog_generation_window)
                
                # 새 제목 탭으로 이동
                self.notebook.set("🎉 생성된 제목")
                
                self.update_status("새로운 제목 생성 완료!")
                self.update_progress(100)
                
                # 플래그 해제
                self._title_generation_running = False
                
                messagebox.showinfo("완료", f"{num_titles}개의 새로운 제목이 생성되었습니다!")
                
            except Exception as e:
                self.update_status(f"오류: {str(e)}")
                self.update_progress(0)
                # 플래그 해제
                self._title_generation_running = False
                messagebox.showerror("오류", f"제목 생성 중 오류가 발생했습니다:\n{str(e)}")
        
        thread = threading.Thread(target=run_generation)
        thread.daemon = True
        thread.start()
    
    def open_blog_generation_window(self):
        """블로그 글 생성 설정 윈도우 열기"""
        selected_indices = self.titles_listbox.curselection()
        if not selected_indices:
            messagebox.showwarning("경고", "제목을 선택해주세요!")
            return
        
        selected_title = self.titles_listbox.get(selected_indices[0])
        
        # 새 윈도우 생성 (테마 적용)
        blog_window = self.create_themed_toplevel(self.root, "블로그 글 생성 설정", "700x600")
        blog_window.transient(self.root)
        blog_window.grab_set()
        
        # 선택된 제목 표시
        title_frame = ttk.LabelFrame(blog_window, text="선택된 제목", padding="10")
        title_frame.pack(fill=tk.X, padx=10, pady=10)
        
        title_label = ttk.Label(title_frame, text=selected_title, font=("", 12, "bold"), foreground="blue")
        title_label.pack()
        
        # 프롬프트 유형 선택
        prompt_frame = ttk.LabelFrame(blog_window, text="글 유형 선택", padding="10")
        prompt_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # 저장된 설정이 있으면 불러오기, 없으면 기본값 사용
        if self.last_blog_settings:
            default_prompt_type = self.last_blog_settings.get('prompt_type', 'informative')
            default_min_chars = str(self.last_blog_settings.get('min_chars', 4000))
            default_additional_prompt = self.last_blog_settings.get('additional_prompt', '')
        else:
            default_prompt_type = "informative"
            default_min_chars = "4000"
            default_additional_prompt = ""
        
        prompt_type_var = tk.StringVar(value=default_prompt_type)
        
        # 프롬프트 옵션들을 가져와서 라디오 버튼 생성
        import prompts
        prompt_configs = prompts.get_blog_content_prompts()
        
        for i, (key, config) in enumerate(prompt_configs.items()):
            radio = ttk.Radiobutton(
                prompt_frame, 
                text=f"{config['name']} - {config['description']}", 
                variable=prompt_type_var, 
                value=key
            )
            radio.grid(row=i, column=0, sticky=tk.W, pady=2)
        
        # 최소 글자수는 4000자로 고정 (UI 제거)
        
        # 추가 프롬프트 입력
        additional_frame = ttk.LabelFrame(blog_window, text="추가 요청사항 (선택사항)", padding="10")
        additional_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        additional_text = tk.Text(additional_frame, height=5, wrap=tk.WORD)
        additional_scrollbar = ttk.Scrollbar(additional_frame, orient=tk.VERTICAL, command=additional_text.yview)
        additional_text.configure(yscrollcommand=additional_scrollbar.set)
        
        additional_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        additional_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 플레이스홀더 텍스트
        placeholder_text = "예시:\n- 초보자도 이해하기 쉽게 작성해주세요\n- 실제 사례를 3개 이상 포함해주세요\n- 단계별 가이드 형식으로 작성해주세요"
        
        # 저장된 추가 프롬프트가 있으면 사용, 없으면 플레이스홀더 사용
        if default_additional_prompt:
            additional_text.insert(1.0, default_additional_prompt)
            # additional_text.configure(foreground="black")  # 색상 설정 제거
        else:
            additional_text.insert(1.0, placeholder_text)
            # additional_text.configure(foreground="gray")   # 색상 설정 제거
        
        def on_focus_in(event):
            if additional_text.get(1.0, tk.END).strip() == placeholder_text:
                additional_text.delete(1.0, tk.END)
                # additional_text.configure(foreground="black")  # 색상 설정 제거
        
        def on_focus_out(event):
            if not additional_text.get(1.0, tk.END).strip():
                additional_text.insert(1.0, placeholder_text)
                # additional_text.configure(foreground="gray")   # 색상 설정 제거
        
        additional_text.bind("<FocusIn>", on_focus_in)
        additional_text.bind("<FocusOut>", on_focus_out)
        
        # 버튼 프레임
        button_frame = ttk.Frame(blog_window)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        def generate_blog():
            # 추가 프롬프트 텍스트 가져오기
            additional_prompt = additional_text.get(1.0, tk.END).strip()
            if additional_prompt == placeholder_text:
                additional_prompt = ""
            
            # 최소 글자수는 4000자로 고정
            # min_chars = 4000 (prompts.py에서 자동 처리)
            
            blog_window.destroy()
            self.generate_blog_content(selected_title, prompt_type_var.get(), additional_prompt)
        
        def save_settings():
            # 설정 저장 함수
            try:
                additional_prompt = additional_text.get(1.0, tk.END).strip()
                if additional_prompt == placeholder_text:
                    additional_prompt = ""
                
                min_chars = 4000  # 고정값으로 변경
                prompt_type = prompt_type_var.get()
                
                # 설정 딕셔너리 생성
                settings = {
                    'prompt_type': prompt_type,
                    'min_chars': min_chars,
                    'additional_prompt': additional_prompt
                }
                
                # 클래스 변수에 저장
                self.last_blog_settings = settings
                
                # 파일로도 저장
                self.save_settings_to_file(settings)
                
                # 프롬프트 유형 이름 가져오기
                import prompts
                prompt_configs = prompts.get_blog_content_prompts()
                prompt_name = prompt_configs.get(prompt_type, {}).get('name', prompt_type)
                
                messagebox.showinfo("설정 저장 완료", 
                    f"블로그 글 생성 설정이 저장되었습니다!\n\n"
                    f"📝 글 유형: {prompt_name}\n"
                    f"📏 기본 글자수: 4000자 (고정)\n"
                    f"➕ 추가 요청사항: {'있음' if additional_prompt else '없음'}\n\n"
                    f"💾 설정 파일: blog_settings.json")
                blog_window.destroy()
                
                # 설정 표시 업데이트
                self.update_settings_display()
                
            except Exception as e:
                messagebox.showerror("저장 오류", f"설정 저장 중 오류가 발생했습니다:\n{str(e)}")
        
        def save_and_generate():
            # 설정 저장 후 바로 글 생성
            additional_prompt = additional_text.get(1.0, tk.END).strip()
            if additional_prompt == placeholder_text:
                additional_prompt = ""
            
            min_chars = 4000  # 고정값으로 변경
            prompt_type = prompt_type_var.get()
            
            # 설정을 클래스 변수에 저장
            self.last_blog_settings = {
                'prompt_type': prompt_type,
                'min_chars': min_chars,
                'additional_prompt': additional_prompt
            }
            
            blog_window.destroy()
            self.generate_blog_content(selected_title, prompt_type, additional_prompt)
        
        # 버튼들 배치 (4개)
        cancel_btn = ttk.Button(button_frame, text="취소", command=blog_window.destroy)
        cancel_btn.pack(side=tk.LEFT)
        
        save_btn = ttk.Button(button_frame, text="💾 설정 저장", command=save_settings)
        save_btn.pack(side=tk.LEFT, padx=(10, 0))
        
        save_and_generate_btn = ttk.Button(button_frame, text="💾 저장 후 글 생성", command=save_and_generate)
        save_and_generate_btn.pack(side=tk.LEFT, padx=(10, 0))
        
        generate_btn = ttk.Button(button_frame, text="📝 바로 글 생성", command=generate_blog)
        generate_btn.pack(side=tk.RIGHT)
    
    def generate_blog_content(self, title, prompt_type, additional_prompt=""):
        """블로그 글 생성"""
        def run_blog_generation():
            try:
                self.update_status("AI가 블로그 글을 생성하고 있습니다...")
                self.update_progress(0)
                
                # 프롬프트 생성
                import prompts
                keyword = self.keyword_var.get().strip()
                
                prompt_data = prompts.create_blog_content_prompt(
                    title=title,
                    keyword=keyword,
                    prompt_type=prompt_type,
                    additional_prompt=additional_prompt
                )
                
                self.update_progress(30)
                
                # OpenAI API 호출
                client = OpenAI(api_key=self.openai_api_key)
                
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": prompt_data['system_prompt']},
                        {"role": "user", "content": prompt_data['user_prompt']}
                    ],
                    max_tokens=12000,
                    temperature=0.7
                )
                
                self.update_progress(80)
                
                blog_content = response.choices[0].message.content
                
                # 결과 표시
                self.blog_content_text.delete(1.0, tk.END)
                self.blog_content_text.insert(1.0, f"제목: {title}\n\n{blog_content}")
                
                # 저장된 블로그 내용 (이미지 생성용)
                self.last_generated_blog = {
                    'title': title,
                    'content': blog_content,
                    'keyword': keyword
                }
                
                # 버튼들 활성화 (CustomTkinter 방식)
                self.html_preview_button.configure(command=self.show_html_preview)
                self.copy_content_button.configure(command=self.copy_blog_content)
                self.generate_images_button.configure(command=self.generate_blog_images)
                
                # 블로그 글 탭으로 이동
                self.notebook.set("📄 생성된 글")
                
                self.update_progress(100)
                self.update_status("블로그 글 생성이 완료되었습니다!")
                
                messagebox.showinfo("완료", "블로그 글이 성공적으로 생성되었습니다!\n\n🎨 이미지 생성은 '이미지 생성' 버튼을 눌러주세요.")
                
            except Exception as e:
                messagebox.showerror("오류", f"블로그 글 생성 중 오류가 발생했습니다: {str(e)}")
                self.update_status("블로그 글 생성 실패")
                self.update_progress(0)
        
        # 별도 스레드에서 실행
        thread = threading.Thread(target=run_blog_generation, daemon=True)
        thread.start()
    
    def quick_generate_blog(self):
        """저장된 설정으로 빠른 글 생성"""
        # 제목이 선택되어 있는지 확인
        selected_indices = self.titles_listbox.curselection()
        if not selected_indices:
            messagebox.showwarning("경고", "제목을 먼저 선택해주세요!")
            return
        
        # 저장된 설정이 있는지 확인
        if not self.last_blog_settings:
            messagebox.showwarning("설정 없음", "저장된 블로그 설정이 없습니다!\n\n'글 생성하기' 버튼을 눌러서 설정을 먼저 저장해주세요.")
            return
        
        selected_title = self.titles_listbox.get(selected_indices[0])
        
        # 저장된 설정으로 글 생성
        prompt_type = self.last_blog_settings['prompt_type']
        min_chars = self.last_blog_settings.get('min_chars', 4000)  # 호환성을 위해 유지
        additional_prompt = self.last_blog_settings['additional_prompt']
        
        self.update_status(f"저장된 설정으로 글을 생성하고 있습니다... (글 유형: {prompt_type}, 기본 4000자)")
        self.generate_blog_content(selected_title, prompt_type, additional_prompt)
    
    def save_settings_to_file(self, settings):
        """설정을 JSON 파일로 저장"""
        try:
            with open('blog_settings.json', 'w', encoding='utf-8') as f:
                json.dump(settings, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"설정 파일 저장 오류: {e}")
    
    def load_settings_from_file(self):
        """설정을 JSON 파일에서 불러오기"""
        try:
            if os.path.exists('blog_settings.json'):
                with open('blog_settings.json', 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                    self.last_blog_settings = settings
                    return settings
        except Exception as e:
            print(f"설정 파일 불러오기 오류: {e}")
        return None
    
    def update_settings_display(self):
        """저장된 설정 표시 업데이트"""
        if self.last_blog_settings:
            prompt_type = self.last_blog_settings.get('prompt_type', 'unknown')
            # min_chars는 항상 4000자로 고정 표시
            
            # 프롬프트 유형 이름 가져오기
            try:
                import prompts
                prompt_configs = prompts.get_blog_content_prompts()
                prompt_name = prompt_configs.get(prompt_type, {}).get('name', prompt_type)
                self.settings_label.configure(text=f"💾 저장된 설정: {prompt_name} (기본 4000자)", text_color="green")
            except:
                self.settings_label.configure(text=f"💾 저장된 설정: {prompt_type} (기본 4000자)", text_color="green")
        else:
            self.settings_label.configure(text="💾 저장된 설정: 없음", text_color="#666666")
    
    def save_results(self):
        """결과 저장"""
        if not self.analysis_result:
            messagebox.showwarning("경고", "저장할 결과가 없습니다!")
            return
        
        try:
            keyword = self.keyword_var.get().strip()
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            default_filename = f"blog_analysis_{keyword}_{timestamp}.txt"
            
            file_path = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("텍스트 파일", "*.txt"), ("모든 파일", "*.*")],
                initialfile=default_filename
            )
            
            if file_path:
                # 결과 내용 준비
                content = f"=== KeiaiLAB 블로그 제목 분석 및 생성 결과 ===\n"
                content += f"검색 키워드: {keyword}\n"
                content += f"분석 일시: {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
                content += f"분석 유형: {self.analysis_type_var.get()}\n\n"
                
                if self.search_result:
                    content += f"=== 검색 결과 요약 ===\n"
                    content += f"총 검색 결과: {self.search_result.get('total', 0):,}개\n"
                    content += f"수집된 제목: {len(self.titles)}개\n"
                    content += f"평균 제목 길이: {sum(len(t) for t in self.titles)/len(self.titles):.1f}자\n\n"
                
                content += f"=== 수집된 제목 목록 ===\n"
                for i, title in enumerate(self.titles, 1):
                    content += f"{i:2d}. {title}\n"
                
                content += f"\n=== AI 분석 결과 ===\n"
                content += self.analysis_result
                
                # 새 제목이 있다면 추가
                titles_count = self.titles_listbox.size()
                if titles_count > 0:
                    content += f"\n\n=== 생성된 새로운 제목들 ===\n"
                    for i in range(titles_count):
                        title = self.titles_listbox.get(i)
                        content += f"{i+1}. {title}\n"
                
                # 블로그 글이 있다면 추가
                blog_content = self.blog_content_text.get(1.0, tk.END).strip()
                if blog_content:
                    content += f"\n\n=== 생성된 블로그 글 ===\n"
                    content += blog_content
                
                # 파일 저장
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                messagebox.showinfo("완료", f"결과가 저장되었습니다:\n{file_path}")
                
        except Exception as e:
            messagebox.showerror("오류", f"파일 저장 중 오류가 발생했습니다:\n{str(e)}")

    def convert_to_html(self, content):
        """텍스트 내용을 HTML로 변환"""
        # 제목과 내용 분리
        lines = content.strip().split('\n')
        html_content = []
        
        html_content.append("""
        <!DOCTYPE html>
        <html lang="ko">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>블로그 글 미리보기</title>
            <style>
                body {
                    font-family: 'Malgun Gothic', Arial, sans-serif;
                    line-height: 1.8;
                    max-width: 800px;
                    margin: 40px auto;
                    padding: 20px;
                    background-color: #f9f9f9;
                }
                .container {
                    background: white;
                    padding: 40px;
                    border-radius: 10px;
                    box-shadow: 0 2px 20px rgba(0,0,0,0.1);
                }
                h1 {
                    color: #2c3e50;
                    border-bottom: 3px solid #3498db;
                    padding-bottom: 15px;
                    margin-bottom: 30px;
                    font-size: 28px;
                }
                h2 {
                    color: #34495e;
                    margin-top: 35px;
                    margin-bottom: 20px;
                    font-size: 22px;
                    border-left: 4px solid #3498db;
                    padding-left: 15px;
                }
                h3 {
                    color: #34495e;
                    margin-top: 30px;
                    margin-bottom: 15px;
                    font-size: 18px;
                }
                p {
                    margin-bottom: 20px;
                    color: #333;
                    text-align: justify;
                }
                .highlight {
                    background-color: #fff3cd;
                    padding: 20px;
                    border-left: 4px solid #ffc107;
                    margin: 20px 0;
                    border-radius: 5px;
                }
                .copy-button {
                    position: fixed;
                    top: 20px;
                    right: 20px;
                    background: #3498db;
                    color: white;
                    border: none;
                    padding: 10px 20px;
                    border-radius: 5px;
                    cursor: pointer;
                    font-size: 14px;
                }
                .copy-button:hover {
                    background: #2980b9;
                }
                ul, ol {
                    margin-bottom: 20px;
                    padding-left: 30px;
                }
                li {
                    margin-bottom: 8px;
                    color: #333;
                }
                strong {
                    color: #2c3e50;
                    font-weight: bold;
                }
                .meta {
                    color: #7f8c8d;
                    font-size: 14px;
                    text-align: center;
                    margin-top: 40px;
                    padding-top: 20px;
                    border-top: 1px solid #ecf0f1;
                }
            </style>
        </head>
        <body>
            <button class="copy-button" onclick="copyToClipboard()">📋 복사하기</button>
            <div class="container">
        """)
        
        in_paragraph = False
        current_paragraph = []
        
        for line in lines:
            line = line.strip()
            if not line:
                if in_paragraph and current_paragraph:
                    html_content.append(f"<p>{''.join(current_paragraph)}</p>")
                    current_paragraph = []
                    in_paragraph = False
                continue
            
            # 제목 처리
            if line.startswith('제목:'):
                title = line.replace('제목:', '').strip()
                html_content.append(f"<h1>{title}</h1>")
            elif line.startswith('# '):
                if in_paragraph and current_paragraph:
                    html_content.append(f"<p>{''.join(current_paragraph)}</p>")
                    current_paragraph = []
                    in_paragraph = False
                html_content.append(f"<h2>{line[2:].strip()}</h2>")
            elif line.startswith('## '):
                if in_paragraph and current_paragraph:
                    html_content.append(f"<p>{''.join(current_paragraph)}</p>")
                    current_paragraph = []
                    in_paragraph = False
                html_content.append(f"<h3>{line[3:].strip()}</h3>")
            elif line.startswith('- ') or line.startswith('* '):
                if in_paragraph and current_paragraph:
                    html_content.append(f"<p>{''.join(current_paragraph)}</p>")
                    current_paragraph = []
                    in_paragraph = False
                if not html_content[-1].startswith('<ul>'):
                    html_content.append('<ul>')
                html_content.append(f"<li>{line[2:].strip()}</li>")
            else:
                # 기존 ul 태그 닫기
                if html_content and html_content[-1].startswith('<li>'):
                    html_content.append('</ul>')
                
                # 일반 텍스트 처리
                if not in_paragraph:
                    in_paragraph = True
                    current_paragraph = []
                
                # 볼드 처리
                line = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', line)
                current_paragraph.append(line + ' ')
        
        # 마지막 문단 처리
        if in_paragraph and current_paragraph:
            html_content.append(f"<p>{''.join(current_paragraph)}</p>")
        
        # ul 태그가 열려있으면 닫기
        if html_content and html_content[-1].startswith('<li>'):
            html_content.append('</ul>')
        
        html_content.append("""
                <div class="meta">
                    📝 KeiaiLAB 블로그 글생성기 by 혁으로 생성된 글입니다.
                </div>
            </div>
            <script>
                function copyToClipboard() {
                    const content = document.querySelector('.container').innerText;
                    navigator.clipboard.writeText(content).then(function() {
                        alert('내용이 클립보드에 복사되었습니다!');
                    });
                }
            </script>
        </body>
        </html>
        """)
        
        return '\n'.join(html_content)

    def show_html_preview(self):
        """HTML 미리보기 창 열기"""
        if not self.last_generated_blog:
            messagebox.showwarning("경고", "생성된 블로그 내용이 없습니다!")
            return
        
        try:
            # 현재 내용 가져오기
            content = self.blog_content_text.get(1.0, tk.END).strip()
            
            # HTML로 변환
            html_content = self.convert_to_html(content)
            
            # 임시 HTML 파일 생성
            with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
                f.write(html_content)
                temp_html_path = f.name
            
            # 기본 브라우저로 열기
            webbrowser.open('file://' + os.path.abspath(temp_html_path))
            
            messagebox.showinfo("알림", "브라우저에서 HTML 미리보기가 열렸습니다!")
            
        except Exception as e:
            messagebox.showerror("오류", f"HTML 미리보기 생성 중 오류가 발생했습니다: {str(e)}")

    def copy_blog_content(self):
        """블로그 내용을 클립보드에 복사"""
        try:
            content = self.blog_content_text.get(1.0, tk.END).strip()
            if not content:
                messagebox.showwarning("경고", "복사할 내용이 없습니다!")
                return
            
            # 클립보드에 복사
            self.root.clipboard_clear()
            self.root.clipboard_append(content)
            self.root.update()  # 클립보드 업데이트 확실히 적용
            
            messagebox.showinfo("완료", "블로그 내용이 클립보드에 복사되었습니다!")
            
        except Exception as e:
            messagebox.showerror("오류", f"내용 복사 중 오류가 발생했습니다: {str(e)}")

    def create_image_prompts(self, title, content, keyword):
        """블로그 내용 기반으로 이미지 생성 프롬프트 생성"""
        try:
            # 국가 언급 확인
            countries = ['한국', '일본', '중국', '미국', '영국', '프랑스', '독일', '이탈리아', '스페인', 
                        '캐나다', '호주', '뉴질랜드', '태국', '베트남', '싱가포르', '말레이시아', 
                        'Korea', 'Japan', 'China', 'USA', 'America', 'UK', 'France', 'Germany', 
                        'Italy', 'Spain', 'Canada', 'Australia', 'Thailand', 'Vietnam', 'Singapore']
            
            mentioned_country = None
            content_lower = content.lower()
            title_lower = title.lower()
            
            for country in countries:
                if country.lower() in content_lower or country.lower() in title_lower:
                    mentioned_country = country
                    break
            
            # 블로그 내용을 문단별로 분석
            paragraphs = [p.strip() for p in content.split('\n\n') if p.strip() and not p.startswith('제목:')]
            
            # GPT로 이미지 프롬프트 생성
            client = OpenAI(api_key=self.openai_api_key)
            
            prompt_request = f"""
다음 블로그 글을 기반으로 3-4개의 DALL-E 이미지 생성 프롬프트를 만들어주세요.

제목: {title}
키워드: {keyword}
언급된 국가: {mentioned_country if mentioned_country else '없음'}

블로그 내용:
{content}

요구사항:
1. 각 프롬프트는 생성된 글의 문단의 핵심 내용 또는 장면을 시각화해야 합니다
2. 글에서 특정 국가가 언급되면, 해당 국가의 분위기와 스타일을 반영한 이미지로 구성해주세요
3. 글에 국가 언급이 없거나, 내용이 다른 국가의 내용이 아닐 시, 인물은 한국인 느낌으로 해주고 풍경, 도시, 자연 등을 반영한 한국적인 이미지 스타일로 구성해주세요
4. 인물에 대한 얘기가 나오고 그 인물을 그릴거라면 캐리커쳐처럼 묘사하고 최대한 사실적으로 그려주세요
5. 프롬프트는 간결한 영어로 작성하고, 스타일/배경/구성 요소가 잘 드러나게 해주세요

각 프롬프트를 다음 형식으로 작성해주세요:
1. [프롬프트]
2. [프롬프트]
3. [프롬프트]
4. [프롬프트]
"""
            
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "당신은 DALL-E 이미지 생성을 위한 전문 프롬프트 작성자입니다. 주어진 블로그 내용을 분석하여 시각적으로 매력적이고 내용과 관련된 이미지 프롬프트를 생성합니다."},
                    {"role": "user", "content": prompt_request}
                ],
                max_tokens=1000,
                temperature=0.7
            )
            
            prompts_text = response.choices[0].message.content
            
            # 프롬프트 파싱
            prompts = []
            if prompts_text:  # None 체크 추가
                for line in prompts_text.split('\n'):
                    line = line.strip()
                    if re.match(r'^\d+\.\s*', line):
                        prompt = re.sub(r'^\d+\.\s*', '', line).strip()
                        if prompt:
                            prompts.append(prompt)
            
            return prompts[:4]  # 최대 4개
            
        except Exception as e:
            print(f"이미지 프롬프트 생성 오류: {str(e)}")
            # 기본 프롬프트 반환
            if mentioned_country:
                style_suffix = f"with {mentioned_country} cultural aesthetic and style"
            else:
                style_suffix = "with Korean people, traditional and modern Korean aesthetic, Korean landscape"
            
            return [
                f"Beautiful Korean landscape scene related to {keyword}, {style_suffix}, high quality, photorealistic",
                f"Korean people enjoying activities related to {keyword}, caricature-like but realistic portrayal, {style_suffix}",
                f"Modern Korean city or interior design showcasing {keyword}, {style_suffix}, clean and elegant",
                f"Traditional Korean elements mixed with {keyword}, {style_suffix}, artistic composition"
            ]

    def create_blog_folder(self, title):
        """블로그 제목 기반으로 폴더 생성"""
        try:
            # blog_data 폴더 생성
            base_folder = "blog_data"
            if not os.path.exists(base_folder):
                os.makedirs(base_folder)
            
            # 제목 앞 5글자 추출 (특수문자 제거)
            safe_title = re.sub(r'[<>:"/\\|?*]', '', title[:5]).strip()
            if not safe_title:
                safe_title = "untitled"
            
            # 폴더명 생성 (날짜와 함께)
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            folder_name = f"{safe_title}_{timestamp}"
            blog_folder = os.path.join(base_folder, folder_name)
            
            if not os.path.exists(blog_folder):
                os.makedirs(blog_folder)
            
            return blog_folder
            
        except Exception as e:
            print(f"폴더 생성 오류: {str(e)}")
            return None

    def download_and_save_image(self, image_url, folder_path, index):
        """이미지를 다운로드하고 로컬에 저장"""
        try:
            # 이미지 다운로드
            response = urllib.request.urlopen(image_url)
            
            # 파일명 생성
            filename = f"image_{index}.png"
            file_path = os.path.join(folder_path, filename)
            
            # 파일 저장
            with open(file_path, 'wb') as f:
                f.write(response.read())
            
            return file_path
            
        except Exception as e:
            print(f"이미지 다운로드 오류: {str(e)}")
            return None

    def generate_dall_e_images(self, prompts):
        """DALL-E를 사용하여 이미지 생성 및 저장"""
        try:
            client = OpenAI(api_key=self.openai_api_key)
            generated_images = []
            
            # 블로그 폴더 생성
            if self.last_generated_blog:
                blog_folder = self.create_blog_folder(self.last_generated_blog['title'])
                
                # 블로그 글도 텍스트 파일로 저장
                if blog_folder:
                    blog_file_path = os.path.join(blog_folder, "blog_content.txt")
                    try:
                        with open(blog_file_path, 'w', encoding='utf-8') as f:
                            f.write(f"제목: {self.last_generated_blog['title']}\n\n")
                            f.write(self.last_generated_blog['content'])
                    except Exception as e:
                        print(f"블로그 글 저장 오류: {str(e)}")
            else:
                blog_folder = None
            
            for i, prompt in enumerate(prompts):
                self.update_status(f"이미지 {i+1}/{len(prompts)} 생성 중...")
                
                response = client.images.generate(
                    model="dall-e-3",
                    prompt=prompt,
                    size="1024x1024",
                    quality="standard",
                    n=1
                )
                
                if response and response.data and len(response.data) > 0:  # None 체크 추가
                    image_url = response.data[0].url
                else:
                    raise Exception("이미지 생성 응답이 유효하지 않습니다.")
                
                # 로컬에 이미지 저장
                local_path = None
                if blog_folder:
                    local_path = self.download_and_save_image(image_url, blog_folder, i+1)
                
                generated_images.append({
                    'prompt': prompt,
                    'url': image_url,
                    'local_path': local_path,
                    'index': i+1
                })
                
                time.sleep(1)  # API 호출 간격 조절
            
            # 생성 완료 알림에 폴더 경로 포함
            if blog_folder and generated_images:
                self.blog_folder_path = blog_folder
            
            return generated_images
            
        except Exception as e:
            print(f"DALL-E 이미지 생성 오류: {str(e)}")
            return []

    def show_generated_images_window(self, images):
        """생성된 이미지들을 보여주는 새 창 열기"""
        if not images:
            return
        
        # 새 창 생성 (테마 적용)
        images_window = self.create_themed_toplevel(self.root, "🎨 생성된 이미지", "1000x800")
        
        # 상단 정보 프레임
        info_frame = ttk.Frame(images_window)
        info_frame.pack(fill=tk.X, padx=10, pady=10)
        
        title_label = ttk.Label(info_frame, text="🎨 생성된 이미지", font=('Arial', 16, 'bold'))
        title_label.pack(side=tk.LEFT)
        
        # 폴더 경로 표시 및 열기 버튼
        if hasattr(self, 'blog_folder_path') and self.blog_folder_path:
            folder_frame = ttk.Frame(info_frame)
            folder_frame.pack(side=tk.RIGHT)
            
            folder_label = ttk.Label(folder_frame, text=f"💾 저장 위치: {self.blog_folder_path}", font=('Arial', 9))
            folder_label.pack(side=tk.LEFT, padx=(0, 10))
            
            def open_folder():
                if self.blog_folder_path and os.path.exists(self.blog_folder_path):
                    os.startfile(self.blog_folder_path)
            
            open_folder_btn = ttk.Button(folder_frame, text="📁 폴더 열기", command=open_folder)
            open_folder_btn.pack(side=tk.LEFT)
        
        # 안내 메시지 프레임
        info_frame_content = ttk.Frame(images_window)
        info_frame_content.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        info_label = ttk.Label(info_frame_content, text="💡 이미지가 로컬에 저장되었습니다. 폴더에서 확인하거나 URL을 복사해서 사용하세요!", 
                              font=('Arial', 10), foreground="blue")
        info_label.pack()
        
        # 스크롤 가능한 프레임
        canvas = tk.Canvas(images_window, bg='#f0f0f0')
        scrollbar = ttk.Scrollbar(images_window, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # 각 이미지 정보 표시
        for img in images:
            # 이미지 정보 프레임
            img_frame = ttk.LabelFrame(scrollable_frame, text=f"이미지 {img['index']}", padding="10")
            img_frame.pack(fill=tk.X, padx=20, pady=10)
            
            # 프롬프트 표시
            prompt_label = ttk.Label(img_frame, text=f"프롬프트: {img['prompt']}", wraplength=900, justify=tk.LEFT)
            prompt_label.pack(anchor=tk.W, pady=(0, 10))
            
            # 저장 경로 표시 (있을 경우)
            if img.get('local_path'):
                path_label = ttk.Label(img_frame, text=f"💾 저장 위치: {img['local_path']}", 
                                     font=('Arial', 8), foreground="green")
                path_label.pack(anchor=tk.W, pady=(0, 10))
            
            # URL 표시
            url_frame = ttk.Frame(img_frame)
            url_frame.pack(fill=tk.X, pady=(0, 10))
            
            url_label = ttk.Label(url_frame, text="🌐 이미지 URL:", font=('Arial', 9, 'bold'))
            url_label.pack(anchor=tk.W)
            
            url_text = tk.Text(url_frame, height=2, wrap=tk.WORD, font=('Arial', 8))
            url_text.insert(1.0, img['url'])
            url_text.configure(state=tk.DISABLED)
            url_text.pack(fill=tk.X, pady=(5, 5))
            
            # 버튼 프레임
            button_frame = ttk.Frame(img_frame)
            button_frame.pack(fill=tk.X)
            
            # URL 복사 버튼
            copy_url_btn = ttk.Button(button_frame, text="📋 URL 복사", 
                                    command=lambda url=img['url']: self.copy_to_clipboard(url, "이미지 URL"))
            copy_url_btn.pack(side=tk.LEFT, padx=(0, 10))
            
            # 브라우저에서 열기 버튼
            open_browser_btn = ttk.Button(button_frame, text="🌐 브라우저에서 열기", 
                                        command=lambda url=img['url']: webbrowser.open(url))
            open_browser_btn.pack(side=tk.LEFT)
        
        # 캔버스와 스크롤바 배치
        canvas.pack(side="left", fill="both", expand=True, padx=(10, 0), pady=(0, 10))
        scrollbar.pack(side="right", fill="y", padx=(0, 10), pady=(0, 10))
        
        # 마우스 휠 스크롤 바인딩
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind("<MouseWheel>", _on_mousewheel)

    def copy_to_clipboard(self, text, description="내용"):
        """텍스트를 클립보드에 복사"""
        try:
            self.root.clipboard_clear()
            self.root.clipboard_append(text)
            self.root.update()
            messagebox.showinfo("완료", f"{description}이(가) 클립보드에 복사되었습니다!")
        except Exception as e:
            messagebox.showerror("오류", f"복사 중 오류가 발생했습니다: {str(e)}")



    def auto_generate_blog_images(self):
        """블로그 생성 후 자동으로 이미지 생성"""
        def run_image_generation():
            try:
                if not self.last_generated_blog:
                    return
                
                # 이미지 프롬프트 생성
                prompts = self.create_image_prompts(
                    self.last_generated_blog['title'],
                    self.last_generated_blog['content'],
                    self.last_generated_blog['keyword']
                )
                
                if prompts:
                    # DALL-E로 이미지 생성
                    images = self.generate_dall_e_images(prompts)
                    
                    if images:
                        # 생성된 이미지 저장 (나중에 접근 가능하도록)
                        self.last_generated_images = images
                        
                        # 생성된 이미지 창 표시 (메인 스레드에서 실행)
                        self.root.after(0, lambda: self.show_generated_images_window(images))
                        self.root.after(0, lambda: self.update_status(f"이미지 생성이 완료되었습니다! ({len(images)}개 저장됨)"))
                        
                        # 폴더 경로가 있으면 알림에 포함하고 자동으로 폴더 열기
                        if hasattr(self, 'blog_folder_path') and self.blog_folder_path:
                            # 폴더 자동으로 열기
                            def open_folder_and_show_message():
                                try:
                                    folder_path = self.blog_folder_path
                                    if folder_path and os.path.exists(folder_path):
                                        os.startfile(folder_path)
                                except Exception as e:
                                    print(f"폴더 열기 오류: {str(e)}")
                                
                                messagebox.showinfo("이미지 생성 완료", 
                                    f"🎨 {len(images)}개의 이미지가 생성되었습니다!\n\n"
                                    f"💾 저장 위치: {self.blog_folder_path}\n\n"
                                    f"📁 폴더가 자동으로 열렸습니다!\n"
                                    f"URL은 이미지 창에서 복사할 수 있습니다.")
                            
                            self.root.after(0, open_folder_and_show_message)
                    else:
                        self.root.after(0, lambda: self.update_status("이미지 생성에 실패했습니다."))
                
            except Exception as e:
                print(f"자동 이미지 생성 오류: {str(e)}")
                self.root.after(0, lambda: self.update_status("이미지 생성 중 오류가 발생했습니다."))
        
        # 별도 스레드에서 실행
        thread = threading.Thread(target=run_image_generation, daemon=True)
        thread.start()

    def generate_blog_images(self):
        """수동으로 이미지 생성"""
        if not self.last_generated_blog:
            messagebox.showwarning("경고", "생성된 블로그 내용이 없습니다!")
            return
        
        # 이전에 생성된 이미지가 있으면 다시 표시
        if hasattr(self, 'last_generated_images') and self.last_generated_images:
            self.show_generated_images_window(self.last_generated_images)
        else:
            self.update_status("이미지 생성을 시작합니다...")
            self.auto_generate_blog_images()
    
    def get_trending_keywords(self):
        """실시간 인기검색어 가져오기 (안정적인 방식)"""
        try:
            # 네이버 실시간 검색어 시도
            naver_keywords = self.get_naver_realtime_keywords()
            if naver_keywords:
                return naver_keywords
            
            # 네이버 실패 시 카테고리별 인기 키워드 제공
            return self.get_category_trending_keywords()
            
        except Exception as e:
            # 모든 방법 실패 시 기본 키워드 제공
            print(f"트렌드 키워드 가져오기 실패: {e}")
            return self.get_category_trending_keywords()
    
    def get_naver_realtime_keywords(self):
        """네이버 데이터랩 방식으로 실시간 검색어 시도"""
        try:
            # 간단한 방식: 현재 시간대별 인기 키워드 시뮬레이션
            import datetime
            current_hour = datetime.datetime.now().hour
            
            # 시간대별 맞춤 키워드 (실제 트렌드를 반영한 키워드들)
            hourly_keywords = {
                range(6, 12): ["모닝루틴", "아침운동", "건강한아침", "출근길", "아침식단", "카페인", "요가", "명상", "독서", "뉴스"],
                range(12, 18): ["점심메뉴", "다이어트", "홈트레이닝", "부업", "투자", "주식", "코인", "부동산", "인테리어", "쇼핑"],
                range(18, 24): ["저녁요리", "넷플릭스", "유튜브", "게임", "독서", "영화추천", "맛집", "데이트", "여행", "취미"],
                range(0, 6): ["수면", "불면증", "야식", "심야영화", "독서", "명상", "ASMR", "힐링", "스트레스", "휴식"]
            }
            
            # 현재 시간에 맞는 키워드 찾기
            for time_range, keywords in hourly_keywords.items():
                if current_hour in time_range:
                    return keywords
            
            return hourly_keywords[range(12, 18)]  # 기본값
            
        except Exception as e:
            print(f"네이버 실시간 키워드 가져오기 실패: {e}")
            return None
    
    def get_category_trending_keywords(self):
        """카테고리별 실시간 인기 키워드"""
        trending_categories = {
            "🔥 HOT 키워드": ["ChatGPT", "인공지능", "메타버스", "NFT", "가상화폐", "전기차", "ESG", "구독경제"],
            "💰 재테크": ["주식", "부동산", "코인", "투자", "펀드", "적금", "연금", "재테크"],
            "🏃‍♀️ 건강": ["다이어트", "홈트레이닝", "요가", "필라테스", "러닝", "헬스", "단백질", "비타민"],
            "🍳 요리": ["에어프라이어", "홈쿡", "다이어트식단", "간편요리", "베이킹", "비건", "키토", "도시락"],
            "✈️ 여행": ["제주도", "부산", "강릉", "경주", "전주", "해외여행", "캠핑", "글램핑"],
            "🎮 취미": ["독서", "영화", "게임", "드라마", "웹툰", "음악", "그림", "사진"],
            "👔 비즈니스": ["창업", "부업", "마케팅", "브랜딩", "SNS", "유튜브", "블로그", "온라인쇼핑"],
            "🏠 라이프": ["인테리어", "정리정돈", "미니멀", "가드닝", "반려동물", "육아", "교육", "패션"]
        }
        
        # 모든 카테고리의 키워드를 합쳐서 섞어서 반환
        all_keywords = []
        for category, keywords in trending_categories.items():
            all_keywords.extend(keywords[:3])  # 각 카테고리에서 3개씩
        
        import random
        random.shuffle(all_keywords)
        return all_keywords[:10]  # 상위 10개 반환
    
    def show_trending_keywords(self):
        """실시간 인기검색어 선택 창 표시"""
        # 로딩 메시지 표시
        self.update_status("실시간 인기검색어를 가져오는 중...")
        
        def load_trends():
            keywords = self.get_trending_keywords()
            
            if not keywords:
                self.root.after(0, lambda: self.update_status("트렌드 데이터를 가져올 수 없습니다."))
                return
            
            # 메인 스레드에서 GUI 창 생성
            self.root.after(0, lambda: self.create_trend_selection_window(keywords))
        
        # 백그라운드에서 트렌드 데이터 로드
        threading.Thread(target=load_trends, daemon=True).start()
    
    def create_trend_selection_window(self, keywords):
        """트렌드 선택 창 생성"""
        self.update_status("실시간 인기검색어를 불러왔습니다.")
        
        # 새 창 생성 (테마 적용)
        trend_window = self.create_themed_toplevel(self.root, "📈 실시간 인기검색어", "400x500")
        trend_window.resizable(False, False)
        
        # 창을 부모 창 중앙에 위치
        trend_window.transient(self.root)
        trend_window.grab_set()
        
        # 메인 프레임
        main_frame = ttk.Frame(trend_window, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 제목
        title_label = ttk.Label(main_frame, text="📈 실시간 인기검색어 TOP 10", 
                               font=('맑은 고딕', 12, 'bold'),
                               foreground='#2c3e50')
        title_label.pack(pady=(0, 20))
        
        subtitle_label = ttk.Label(main_frame, text="클릭하여 키워드를 선택하세요 (시간대별 맞춤 키워드)",
                                  font=('맑은 고딕', 9),
                                  foreground='#34495e')
        subtitle_label.pack(pady=(0, 20))
        
        # 키워드 목록 프레임
        keywords_frame = ttk.Frame(main_frame)
        keywords_frame.pack(fill=tk.BOTH, expand=True)
        
        def select_keyword(keyword):
            """키워드 선택 시 실행되는 함수"""
            # 플레이스홀더 텍스트 제거 및 키워드 설정
            self.keyword_var.set(keyword)
            # CustomTkinter에서는 text_color 사용하지만 여기서는 불필요
            trend_window.destroy()
            
            # 네이버 검색으로 자동 분석 시작
            self.update_status(f"'{keyword}' 트렌드 키워드로 네이버 블로그 분석을 시작합니다...")
            
            # 별도 스레드에서 네이버 분석 실행
            def run_naver_analysis():
                try:
                    # 기존 start_analysis와 run_analysis 로직 활용
                    self.root.after(0, lambda: self.start_analysis())
                    
                    # 완료 후 분석 탭으로 이동
                    time.sleep(1)  # 분석 시작을 위한 짧은 대기
                    self.root.after(0, lambda: self.notebook.set("🧠 AI 분석"))
                    
                except Exception as e:
                    print(f"트렌드 키워드 분석 오류: {str(e)}")
                    self.root.after(0, lambda: messagebox.showerror("분석 오류", 
                        f"'{keyword}' 키워드 분석 중 오류가 발생했습니다.\n\n"
                        f"오류 내용: {str(e)}\n\n"
                        f"수동으로 '분석 시작' 버튼을 눌러보세요."))
                    self.root.after(0, lambda: self.update_status("분석 오류 발생"))
            
            thread = threading.Thread(target=run_naver_analysis, daemon=True)
            thread.start()
        
        # 키워드 버튼들 생성
        for i, keyword in enumerate(keywords, 1):
            # 키워드 버튼 프레임
            keyword_frame = ttk.Frame(keywords_frame)
            keyword_frame.pack(fill=tk.X, pady=2)
            
            # 순위 라벨
            rank_label = ttk.Label(keyword_frame, text=f"{i:2d}.", 
                                  font=('맑은 고딕', 10, 'bold'),
                                  foreground='#e74c3c', width=3)
            rank_label.pack(side=tk.LEFT, padx=(0, 10))
            
            # 키워드 버튼
            keyword_button = ttk.Button(keyword_frame, text=keyword,
                                       style='Secondary.TButton',
                                       command=lambda k=keyword: select_keyword(k))
            keyword_button.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # 닫기 버튼
        close_button = ttk.Button(main_frame, text="❌ 닫기", 
                                 style='Secondary.TButton',
                                 command=trend_window.destroy)
        close_button.pack(pady=(20, 0))

    def get_predefined_categories(self):
        """미리 정의된 카테고리들 반환"""
        return {
            "🔥 트렌드/핫이슈": {
                "keywords": ["ChatGPT", "인공지능", "메타버스", "NFT", "가상화폐", "전기차", "ESG", "구독경제", "MZ세대", "클린뷰티", "비건", "제로웨이스트"],
                "description": "최신 화제, 뉴스, 사회적 이슈"
            },
            "💰 재테크/투자": {
                "keywords": ["주식", "부동산", "가상화폐", "비트코인", "투자", "펀드", "적금", "연금", "세금", "절세", "파이어족", "경제독립"],
                "description": "주식, 부동산, 투자 관련 정보"
            },
            "🏃‍♀️ 건강/피트니스": {
                "keywords": ["다이어트", "홈트레이닝", "요가", "필라테스", "러닝", "헬스", "단백질", "비타민", "수면", "스트레칭", "마라톤", "크로스핏"],
                "description": "운동, 다이어트, 건강관리"
            },
            "🍳 요리/레시피": {
                "keywords": ["에어프라이어", "홈쿡", "다이어트식단", "간편요리", "베이킹", "비건요리", "키토식단", "도시락", "브런치", "디저트", "발효음식", "한식"],
                "description": "음식, 요리법, 맛집 정보"
            },
            "✈️ 여행/관광": {
                "keywords": ["제주도", "부산", "강릉", "경주", "전주", "해외여행", "캠핑", "글램핑", "호텔", "펜션", "배낭여행", "패키지여행"],
                "description": "국내외 여행, 명소, 숙박"
            },
            "🎮 취미/엔터": {
                "keywords": ["독서", "영화", "게임", "드라마", "웹툰", "음악", "그림", "사진", "넷플릭스", "유튜브", "스트리밍", "OTT"],
                "description": "게임, 영화, 드라마, 음악"
            },
            "👔 비즈니스/마케팅": {
                "keywords": ["창업", "부업", "마케팅", "브랜딩", "SNS마케팅", "유튜브", "블로그", "온라인쇼핑", "이커머스", "스타트업", "프리랜서", "사이드잡"],
                "description": "창업, 마케팅, 온라인 사업"
            },
            "🏠 라이프스타일": {
                "keywords": ["인테리어", "정리정돈", "미니멀라이프", "가드닝", "반려동물", "육아", "교육", "패션", "뷰티", "스킨케어", "홈데코", "살림"],
                "description": "인테리어, 패션, 일상"
            },
            "📚 교육/학습": {
                "keywords": ["영어공부", "자격증", "코딩", "프로그래밍", "온라인강의", "독학", "시험", "취업", "이직", "스킬업", "자기계발", "어학연수"],
                "description": "공부, 자격증, 스킬업"
            },
            "💻 IT/기술": {
                "keywords": ["프로그래밍", "코딩", "웹개발", "앱개발", "AI", "머신러닝", "블록체인", "클라우드", "사이버보안", "빅데이터", "IoT", "5G"],
                "description": "프로그래밍, AI, 최신 기술"
            }
        }
    
    def show_category_selection(self):
        """카테고리 선택 창 표시"""
        self.update_status("카테고리 선택창을 열고 있습니다...")
        
        # 새 창 생성 (테마 적용)
        category_window = self.create_themed_toplevel(self.root, "📈 카테고리별 트렌드 키워드", "800x600")
        category_window.resizable(True, True)
        
        # 창을 부모 창 중앙에 위치
        category_window.transient(self.root)
        category_window.grab_set()
        
        # 메인 프레임
        main_frame = ttk.Frame(category_window, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 제목
        title_label = ttk.Label(main_frame, text="📈 카테고리별 트렌드 키워드", 
                               font=('맑은 고딕', 14, 'bold'),
                               foreground='#2c3e50')
        title_label.pack(pady=(0, 10))
        
        subtitle_label = ttk.Label(main_frame, text="관심있는 카테고리를 선택하여 해당 분야의 인기 키워드를 확인하세요",
                                  font=('맑은 고딕', 10),
                                  foreground='#34495e')
        subtitle_label.pack(pady=(0, 20))
        
        # 스크롤 가능한 카테고리 프레임
        canvas = tk.Canvas(main_frame, bg='#fafafa')
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # 카테고리 버튼들 생성
        categories = self.get_predefined_categories()
        
        def select_category(category_name):
            """카테고리 선택 시 실행되는 함수"""
            category_window.destroy()
            self.show_category_keywords(category_name, categories[category_name])
        
        # 카테고리별로 버튼 생성 (2열 레이아웃)
        row = 0
        col = 0
        for category_name, category_data in categories.items():
            # 카테고리 프레임
            category_frame = ttk.LabelFrame(scrollable_frame, text=category_name, padding="15")
            category_frame.grid(row=row, column=col, sticky="ew", padx=10, pady=10)
            
            # 설명
            desc_label = ttk.Label(category_frame, text=category_data['description'], 
                                 font=('맑은 고딕', 9),
                                 foreground='#7f8c8d')
            desc_label.pack(pady=(0, 10))
            
            # 키워드 미리보기 (처음 4개만)
            preview_keywords = category_data['keywords'][:4]
            preview_text = ', '.join(preview_keywords) + f" 외 {len(category_data['keywords'])-4}개"
            
            preview_label = ttk.Label(category_frame, text=f"키워드: {preview_text}", 
                                    font=('맑은 고딕', 8),
                                    foreground='#95a5a6',
                                    wraplength=300)
            preview_label.pack(pady=(0, 10))
            
            # 선택 버튼
            select_btn = ttk.Button(category_frame, text="🔍 키워드 보기", 
                                  style='Category.TButton',
                                  command=lambda name=category_name: select_category(name))
            select_btn.pack()
            
            # 2열 레이아웃
            col += 1
            if col >= 2:
                col = 0
                row += 1
        
        # 그리드 가중치 설정
        for i in range(2):
            scrollable_frame.columnconfigure(i, weight=1)
        
        # 캔버스와 스크롤바 배치
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # 마우스 휠 스크롤 바인딩
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind("<MouseWheel>", _on_mousewheel)
        
        # 닫기 버튼
        close_button = ttk.Button(main_frame, text="❌ 닫기", 
                                 style='Secondary.TButton',
                                 command=category_window.destroy)
        close_button.pack(pady=(20, 0))
        
        self.update_status("카테고리를 선택해주세요.")
    
    def show_category_keywords(self, category_name, category_data):
        """선택된 카테고리의 키워드들 표시"""
        # 새 창 생성 (테마 적용)
        keywords_window = self.create_themed_toplevel(self.root, f"{category_name} - 트렌드 키워드", "500x700")
        keywords_window.resizable(False, True)
        
        # 창을 부모 창 중앙에 위치
        keywords_window.transient(self.root)
        keywords_window.grab_set()
        
        # 메인 프레임
        main_frame = ttk.Frame(keywords_window, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 제목
        title_label = ttk.Label(main_frame, text=category_name, 
                               font=('맑은 고딕', 14, 'bold'),
                               foreground='#2c3e50')
        title_label.pack(pady=(0, 10))
        
        # 설명
        desc_label = ttk.Label(main_frame, text=category_data['description'],
                              font=('맑은 고딕', 10),
                              foreground='#34495e')
        desc_label.pack(pady=(0, 20))
        
        # 안내 메시지
        info_label = ttk.Label(main_frame, text="🔍 키워드를 클릭하여 선택하세요",
                              font=('맑은 고딕', 9),
                              foreground='#e74c3c')
        info_label.pack(pady=(0, 15))
        
        def select_keyword(keyword):
            """키워드 선택 시 실행되는 함수"""
            # 플레이스홀더 텍스트 제거 및 키워드 설정
            self.keyword_var.set(keyword)
            # CustomTkinter에서는 text_color 사용하지만 여기서는 불필요
            keywords_window.destroy()
            
            # 네이버 검색으로 자동 분석 시작
            self.update_status(f"'{keyword}' 키워드로 네이버 블로그 분석을 시작합니다...")
            
            # 별도 스레드에서 네이버 분석 실행
            def run_naver_analysis():
                try:
                    # 기존 start_analysis와 run_analysis 로직 활용
                    self.root.after(0, lambda: self.start_analysis())
                    
                    # 완료 후 분석 탭으로 이동
                    time.sleep(1)  # 분석 시작을 위한 짧은 대기
                    self.root.after(0, lambda: self.notebook.set("🧠 AI 분석"))
                    
                except Exception as e:
                    print(f"카테고리 키워드 분석 오류: {str(e)}")
                    self.root.after(0, lambda: messagebox.showerror("분석 오류", 
                        f"'{keyword}' 키워드 분석 중 오류가 발생했습니다.\n\n"
                        f"카테고리: {category_name}\n"
                        f"오류 내용: {str(e)}\n\n"
                        f"수동으로 '분석 시작' 버튼을 눌러보세요."))
                    self.root.after(0, lambda: self.update_status("분석 오류 발생"))
            
            thread = threading.Thread(target=run_naver_analysis, daemon=True)
            thread.start()
        
        # 스크롤 가능한 키워드 프레임
        canvas = tk.Canvas(main_frame, bg='#fafafa')
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # 키워드 버튼들 생성
        keywords = category_data['keywords']
        import random
        random.shuffle(keywords)  # 랜덤하게 섞어서 표시
        
        for i, keyword in enumerate(keywords, 1):
            # 키워드 버튼 프레임
            keyword_frame = ttk.Frame(scrollable_frame)
            keyword_frame.pack(fill=tk.X, pady=3)
            
            # 순위 라벨
            rank_label = ttk.Label(keyword_frame, text=f"{i:2d}.", 
                                  font=('맑은 고딕', 10, 'bold'),
                                  foreground='#e74c3c', width=3)
            rank_label.pack(side=tk.LEFT, padx=(0, 10))
            
            # 키워드 버튼
            keyword_button = ttk.Button(keyword_frame, text=keyword,
                                       style='Secondary.TButton',
                                       command=lambda k=keyword: select_keyword(k))
            keyword_button.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # 캔버스와 스크롤바 배치
        canvas.pack(side="left", fill="both", expand=True, pady=(0, 20))
        scrollbar.pack(side="right", fill="y", pady=(0, 20))
        
        # 마우스 휠 스크롤 바인딩
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind("<MouseWheel>", _on_mousewheel)
        
        # 하단 버튼 프레임
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        # 뒤로가기 버튼
        back_button = ttk.Button(button_frame, text="⬅️ 카테고리 선택", 
                               style='Secondary.TButton',
                               command=lambda: [keywords_window.destroy(), self.show_category_selection()])
        back_button.pack(side=tk.LEFT)
        
        # 닫기 버튼
        close_button = ttk.Button(button_frame, text="❌ 닫기", 
                                 style='Secondary.TButton',
                                 command=keywords_window.destroy)
        close_button.pack(side=tk.RIGHT)
        
        self.update_status(f"{category_name} 카테고리의 {len(keywords)}개 키워드를 불러왔습니다.")

def main():
    root = ctk.CTk()
    app = BlogAnalyzerApp(root)
    root.mainloop()

if __name__ == "__main__":
    main() 