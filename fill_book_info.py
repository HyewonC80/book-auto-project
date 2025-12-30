# -*- coding: utf-8 -*-
"""
booklist_update_merge_click_first_with_note.py
- 입력: booklist_cleaned.csv (현재 폴더)
- 출력: booklist_update.csv (정해진 컬럼 순서)
- 규칙:
  * 검색 제목은 무조건 B열(두 번째 열)을 사용
  * 원본 CSV 값이 있으면 우선 사용, 비어 있으면 스크랩으로 보완
  * 검색 페이지: //*[...]/li/div/div[3]/div[2]/a (첫 항목) 클릭해 상세 진입
  * DOM 덤프 파일 생성 없음
"""

import os
import csv
import time
import re
import urllib.parse
import tkinter as tk
from tkinter import messagebox, simpledialog

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver import ActionChains
from selenium.common.exceptions import (
    TimeoutException, ElementClickInterceptedException,
    StaleElementReferenceException, NoSuchElementException
)
from webdriver_manager.chrome import ChromeDriverManager

# ----------------- 설정 -----------------
HEADLESS = False        # 실제 화면 보려면 False
PAGE_LOAD_WAIT = 12     # 대기 타임아웃(초)
SEARCH_URL_TMPL = "https://www.wendybook.com/search/result?term={q}"
# ---------------------------------------

# 검색 결과(목록)에서 '각 항목의 제목 a 태그' (첫 것 클릭)
RESULT_ITEM_XPATH = '//*[@id="ContentsAreaWrap"]//li//a[contains(@href, "/book/detail/")]'

# 상세 페이지 XPATH들 (우선순위 순서)
XPATH_TOPIC   = '//*[@id="container"]/div[2]/div[1]/div[2]/div[2]/div[13]/div[3]/div[2]/div[1]/a'
XPATH_SERIES  = '//*[@id="container"]/div[2]/div[1]/div[2]/div[2]/div[3]/div/a/span[1]'
XPATH_AUTHOR  = '//*[@id="container"]/div[2]/div[1]/div[2]/div[2]/div[12]/div[4]/div[2]/div[1]/a'
XPATH_PUB     = '//*[@id="container"]/div[2]/div[1]/div[2]/div[2]/div[11]/div[5]/div[2]/a'
XPATH_AR      = '//*[@id="container"]/div[2]/div[1]/div[2]/div[2]/div[13]/div[5]/div[2]/div/a'
XPATH_LEXILE  = '//*[@id="container"]/div[2]/div[1]/div[2]/div[2]/div[5]/div/div/a'
XPATH_FORMAT  = '//*[@id="container"]/div[2]/div[1]/div[2]/div[2]/div[11]/div[4]/div[2]'
XPATH_NOTE_1  = '//*[@id="container"]/div[2]/div[1]/div[2]/div[2]/div[13]/div[2]/div[2]/div[1]/a'
XPATH_NOTE_2  = '//*[@id="container"]/div[2]/div[1]/div[2]/div[2]/div[13]/div[2]/div[2]/div[2]/a'
XPATH_ISBN    = '//*[@id="container"]/div[2]/div[1]/div[2]/div[2]/div[11]/div[2]/div[2]'

# 대체 XPATH들 (두 번째 우선순위)
ALT_XPATH_TOPIC   = '//*[@id="container"]/div[2]/div[1]/div[2]/div[2]/div[3]/div/span'
ALT_XPATH_SERIES  = '//*[@id="container"]/div[2]/div[1]/div[2]/div[2]/div[3]/div/span'
ALT_XPATH_AUTHOR  = '//*[@id="container"]/div[2]/div[1]/div[2]/div[2]/div[12]/div[4]/div[2]/div/a'
ALT_XPATH_PUB     = '//*[@id="container"]/div[2]/div[1]/div[2]/div[2]/div[10]/div[5]/div[2]/a'
ALT_XPATH_AR      = '//*[@id="container"]/div[2]/div[1]/div[2]/div[2]/div[12]/div[5]/div[2]/div/a'
ALT_XPATH_LEXILE  = '//*[@id="container"]/div[2]/div[1]/div[2]/div[2]/div[12]/div[6]/div[2]/div/a'
ALT_XPATH_FORMAT  = '//*[@id="container"]/div[2]/div[1]/div[2]/div[2]/div[10]/div[4]/div[2]'
ALT_XPATH_NOTE_1  = '//*[@id="container"]/div[2]/div[1]/div[2]/div[2]/div[13]/div[2]/div[2]/div[1]/a'
ALT_XPATH_NOTE_2  = '//*[@id="container"]/div[2]/div[1]/div[2]/div[2]/div[13]/div[2]/div[2]/div[2]/a'
ALT_XPATH_ISBN    = '//*[@id="container"]/div[2]/div[1]/div[2]/div[2]/div[11]/div[2]/div[2]'

# 세 번째 우선순위 XPATH들
THIRD_XPATH_TOPIC   = '//*[@id="container"]/div[2]/div[1]/div[2]/div[2]/div[12]/div[3]/div[2]/div[1]/a'
THIRD_XPATH_SERIES  = '//*[@id="container"]/div[2]/div[1]/div[2]/div[2]/div[3]/div/span'
THIRD_XPATH_AUTHOR  = '//*[@id="container"]/div[2]/div[1]/div[2]/div[2]/div[12]/div[4]/div[2]/div[1]/a'
THIRD_XPATH_PUB     = '//*[@id="container"]/div[2]/div[1]/div[2]/div[2]/div[10]/div[5]/div[2]/a'
THIRD_XPATH_AR      = '//*[@id="container"]/div[2]/div[1]/div[2]/div[2]/div[12]/div[5]/div[2]/div/a'
THIRD_XPATH_LEXILE  = '//*[@id="container"]/div[2]/div[1]/div[2]/div[2]/div[12]/div[6]/div[2]/div/a'
THIRD_XPATH_FORMAT  = '//*[@id="container"]/div[2]/div[1]/div[2]/div[2]/div[10]/div[4]/div[2]'
THIRD_XPATH_NOTE_1  = '//*[@id="container"]/div[2]/div[1]/div[2]/div[2]/div[12]/div[2]/div[2]/div[1]/a'
THIRD_XPATH_NOTE_2  = '//*[@id="container"]/div[2]/div[1]/div[2]/div[2]/div[12]/div[2]/div[2]/div[2]/a'
THIRD_XPATH_ISBN    = '//*[@id="container"]/div[2]/div[1]/div[2]/div[2]/div[10]/div[2]/div[2]'

# 네 번째 우선순위 XPATH들 (절대 경로)
FOURTH_XPATH_TOPIC   = '/html/body/div[1]/div[2]/div[2]/div[1]/div[2]/div[2]/div[14]/div[3]/div[2]/div[1]/a'
FOURTH_XPATH_AUTHOR  = '/html/body/div[1]/div[2]/div[2]/div[1]/div[2]/div[2]/div[14]/div[4]/div[2]/div[1]/a'
FOURTH_XPATH_PUB     = '/html/body/div[1]/div[2]/div[2]/div[1]/div[2]/div[2]/div[12]/div[5]/div[2]/a'
FOURTH_XPATH_AR      = '/html/body/div[1]/div[2]/div[2]/div[1]/div[2]/div[2]/div[14]/div[5]/div[2]/div/a'
FOURTH_XPATH_LEXILE  = '/html/body/div[1]/div[2]/div[2]/div[1]/div[2]/div[2]/div[14]/div[6]/div[2]/div/a'
FOURTH_XPATH_FORMAT  = '/html/body/div[1]/div[2]/div[2]/div[1]/div[2]/div[2]/div[12]/div[4]/div[2]'
FOURTH_XPATH_NOTE_1  = '/html/body/div[1]/div[2]/div[2]/div[1]/div[2]/div[2]/div[14]/div[2]/div[2]/div[1]/a'
FOURTH_XPATH_NOTE_2  = '/html/body/div[1]/div[2]/div[2]/div[1]/div[2]/div[2]/div[14]/div[2]/div[2]/div[2]/a'
FOURTH_XPATH_ISBN    = '/html/body/div[1]/div[2]/div[2]/div[1]/div[2]/div[2]/div[12]/div[2]/div[2]'

# Dem Bones 전용 XPATH들 (실제 페이지 구조에 맞춤)
DEM_BONES_XPATHS = {
    "topic": [
        '//*[@id="container"]/div[2]/div[1]/div[2]/div[2]/div[13]/div[3]/div[2]/div[1]/a'
    ],
    "author": [
        '//*[@id="container"]/div[2]/div[1]/div[2]/div[2]/div[13]/div[4]/div[2]/div[1]/a'
    ],
    "publisher": [
        '//*[@id="container"]/div[2]/div[1]/div[2]/div[2]/div[11]/div[5]/div[2]/a'
    ],
    "ar": [
        '//*[@id="container"]/div[2]/div[1]/div[2]/div[2]/div[13]/div[5]/div[2]/div/a'
    ],
    "lexile": [
        '//*[@id="container"]/div[2]/div[1]/div[2]/div[2]/div[4]/div/div/a'
    ],
    "format": [
        '//*[@id="container"]/div[2]/div[1]/div[2]/div[2]/div[11]/div[4]/div[2]'
    ],
    "note": [
        '//*[@id="container"]/div[2]/div[1]/div[2]/div[2]/div[13]/div[2]/div[2]/div[1]/a',
        '//*[@id="container"]/div[2]/div[1]/div[2]/div[2]/div[13]/div[2]/div[2]/div[2]/a',
        '//*[@id="container"]/div[2]/div[1]/div[2]/div[2]/div[12]/div[6]/div[2]/div/a'
    ],
    "isbn": [
        '//*[@id="container"]/div[2]/div[1]/div[2]/div[2]/div[10]/div[2]/div[2]'
    ]
}


# 출력 헤더 (비고 포함)
OUT_HEADER = [
    "Number", "책 제목", "위치", "주제", "시리즈", "저자",
    "출판사", "AR", "Lexile (L)", "형태", "비고", "ISBN", "URL"
]

# 실패 리스트 헤더
FAILURE_HEADER = [
    "Number", "책 제목", "실패 원인", "상세 정보"
]

# ----------------- 유틸 -----------------
def get_range_input(total_items):
    """
    윈도우 입력창을 통해 처리할 범위를 입력받습니다.
    """
    result = [None, None]
    
    def on_ok():
        try:
            start = int(start_entry.get())
            end = int(end_entry.get())
            
            if start < 1 or start > total_items:
                messagebox.showerror("오류", f"시작번호는 1 ~ {total_items} 사이여야 합니다.")
                return
            
            if end < start or end > total_items:
                messagebox.showerror("오류", f"끝번호는 {start} ~ {total_items} 사이여야 합니다.")
                return
            
            result[0] = start
            result[1] = end
            root.destroy()
        except ValueError:
            messagebox.showerror("오류", "숫자를 입력해주세요.")
    
    def on_cancel():
        root.destroy()
    
    # 메인 윈도우 생성
    root = tk.Tk()
    root.title("처리 범위 설정")
    root.geometry("400x200")
    root.resizable(False, False)
    
    # 중앙 정렬
    root.update_idletasks()
    x = (root.winfo_screenwidth() // 2) - (400 // 2)
    y = (root.winfo_screenheight() // 2) - (200 // 2)
    root.geometry(f"400x200+{x}+{y}")
    
    # 제목
    title_label = tk.Label(root, text="책 정보 검색 범위 설정", font=("맑은 고딕", 14, "bold"))
    title_label.pack(pady=10)
    
    # 총 개수 표시
    total_label = tk.Label(root, text=f"총 {total_items}개의 책이 있습니다.", font=("맑은 고딕", 10))
    total_label.pack(pady=5)
    
    # 입력 프레임
    input_frame = tk.Frame(root)
    input_frame.pack(pady=20)
    
    # 시작번호 입력
    start_frame = tk.Frame(input_frame)
    start_frame.pack(pady=5)
    tk.Label(start_frame, text="시작번호:", font=("맑은 고딕", 10)).pack(side=tk.LEFT, padx=5)
    start_entry = tk.Entry(start_frame, font=("맑은 고딕", 10), width=10)
    start_entry.pack(side=tk.LEFT, padx=5)
    start_entry.insert(0, "1")
    
    # 끝번호 입력
    end_frame = tk.Frame(input_frame)
    end_frame.pack(pady=5)
    tk.Label(end_frame, text="끝번호:", font=("맑은 고딕", 10)).pack(side=tk.LEFT, padx=5)
    end_entry = tk.Entry(end_frame, font=("맑은 고딕", 10), width=10)
    end_entry.pack(side=tk.LEFT, padx=5)
    end_entry.insert(0, str(min(10, total_items)))
    
    # 버튼 프레임
    button_frame = tk.Frame(root)
    button_frame.pack(pady=20)
    
    # 확인 버튼
    ok_button = tk.Button(button_frame, text="확인", font=("맑은 고딕", 10), 
                         command=on_ok, bg="#4CAF50", fg="white", width=10)
    ok_button.pack(side=tk.LEFT, padx=10)
    
    # 취소 버튼
    cancel_button = tk.Button(button_frame, text="취소", font=("맑은 고딕", 10), 
                             command=on_cancel, bg="#f44336", fg="white", width=10)
    cancel_button.pack(side=tk.LEFT, padx=10)
    
    # 엔터키로 확인
    root.bind('<Return>', lambda e: on_ok())
    
    # 포커스 설정
    start_entry.focus()
    
    # 윈도우 실행
    root.mainloop()
    
    return result[0], result[1]

def build_driver(headless=True):
    opts = Options()
    if headless:
        opts.add_argument("--headless=new")
    opts.add_argument("--disable-blink-features=AutomationControlled")
    opts.add_experimental_option("excludeSwitches", ["enable-automation"])
    opts.add_experimental_option("useAutomationExtension", False)
    opts.add_argument("--window-size=1280,900")
    opts.add_argument("--lang=ko-KR")
    opts.add_argument("--accept-lang=ko-KR,ko;q=0.9,en;q=0.8")
    opts.add_argument("--disable-web-security")
    opts.add_argument("--disable-features=VizDisplayCompositor")
    opts.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36"
    )
    opts.page_load_strategy = "eager"
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=opts)
    driver.implicitly_wait(2)
    return driver

def safe_text(drv, xpath, debug_name="", alt_xpath="", third_xpath="", fourth_xpath="", additional_xpaths=None):
    # 메인 XPATH 시도
    try:
        element = drv.find_element(By.XPATH, xpath)
        text = element.text.strip()
        if debug_name and text:
            print(f"   ↳ {debug_name}: {text}")
        return text
    except Exception:
        pass
    
    # 대체 XPATH 시도
    if alt_xpath:
        try:
            element = drv.find_element(By.XPATH, alt_xpath)
            text = element.text.strip()
            if debug_name and text:
                print(f"   ↳ {debug_name} (대체): {text}")
            return text
        except Exception:
            pass
    
    # 세 번째 XPATH 시도
    if third_xpath:
        try:
            element = drv.find_element(By.XPATH, third_xpath)
            text = element.text.strip()
            if debug_name and text:
                print(f"   ↳ {debug_name} (세번째): {text}")
            return text
        except Exception:
            pass
    
    # 네 번째 XPATH 시도
    if fourth_xpath:
        try:
            element = drv.find_element(By.XPATH, fourth_xpath)
            text = element.text.strip()
            if debug_name and text:
                print(f"   ↳ {debug_name} (네번째): {text}")
            return text
        except Exception:
            pass
    
    # 추가 XPATH들 시도
    if additional_xpaths:
        for i, add_xpath in enumerate(additional_xpaths):
            try:
                element = drv.find_element(By.XPATH, add_xpath)
                text = element.text.strip()
                if debug_name and text:
                    print(f"   ↳ {debug_name} (추가{i+1}): {text}")
                return text
            except Exception:
                continue
    
    if debug_name:
        print(f"   ↳ {debug_name}: 찾을 수 없음")
    return ""

def try_close_overlays(drv):
    for sel in [
        "button.cookie-accept", ".cookie-accept", ".popClose", ".popup-close",
        ".modal .btn-close", ".layer .btn-close", ".btn_agree"
    ]:
        try:
            els = drv.find_elements(By.CSS_SELECTOR, sel)
            if els:
                els[0].click()
                time.sleep(0.15)
        except Exception:
            pass

def norm(s: str) -> str:
    if s is None:
        return ""
    return re.sub(r"[^\w가-힣]", "", s).lower()

def read_csv_flexible(path):
    # utf-8-sig 우선, 실패 시 cp949로 재시도
    try:
        with open(path, "r", encoding="utf-8-sig") as f:
            return list(csv.reader(f))
    except UnicodeDecodeError:
        with open(path, "r", encoding="cp949", errors="ignore") as f:
            return list(csv.reader(f))

def header_index_map(header):
    # 원본 CSV에서 사용할 수 있는 컬럼 인덱스 매핑
    lower = {h.strip().lower(): i for i, h in enumerate(header)}
    def get(*names):
        for n in names:
            k = n.strip().lower()
            if k in lower:
                return lower[k]
        return None
    return {
        "title":     get("책 제목", "제목", "title"),  # (검색은 아래에서 B열 고정 사용)
        "location":  get("위치", "location"),
        "topic":     get("주제", "topic"),
        "series":    get("시리즈", "series"),
        "author":    get("저자", "author"),
        "publisher": get("출판사", "publisher"),
        "ar":        get("ar"),
        "lexile":    get("lexile (l)", "lexile", "lexile(l)"),
        "format":    get("형태", "format"),
        "note":      get("비고", "note", "memo"),
        "isbn":      get("isbn"),
    }

def get_cell(row, idx):
    if idx is None or idx >= len(row):
        return ""
    return (row[idx] or "").strip()

# ----------------- 핵심: 첫 결과 클릭 -----------------
def click_first_result(driver, wait) -> tuple[bool, str]:
    """
    결과 목록의 첫 항목 a(RESULT_ITEM_XPATH)의 '첫 번째 요소'를 견고하게 클릭
    반환: (성공여부, URL)
    """
    try:
        # 존재/가시성 대기 → elements로 모아 첫 요소
        wait.until(EC.presence_of_all_elements_located((By.XPATH, RESULT_ITEM_XPATH)))
        elems = driver.find_elements(By.XPATH, RESULT_ITEM_XPATH)
        if not elems:
            print("❗ 결과 항목 a를 찾지 못했어요.")
            return False, ""
        elem = elems[0]
    except TimeoutException:
        print("❗ 결과 항목 a가 나타나지 않았어요.")
        return False, ""

    # 화면 중앙 정렬 & 오버레이 닫기
    try:
        driver.execute_script("arguments[0].scrollIntoView({block:'center', inline:'nearest'});", elem)
        time.sleep(0.15)
    except Exception:
        pass
    try_close_overlays(driver)

    for attempt in range(3):
        try:
            # 요소 다시 찾기
            elems = driver.find_elements(By.XPATH, RESULT_ITEM_XPATH)
            if not elems:
                time.sleep(0.3)
                continue
            elem = elems[0]
            
            # href 속성으로 직접 이동 (가장 확실한 방법)
            try:
                href = elem.get_attribute("href")
                if href:
                    print(f"   ↳ href로 직접 이동: {href}")
                    driver.get(href)
                    time.sleep(1)  # 페이지 로딩 대기
                    return True, href
            except Exception as e:
                print(f"   ↳ href 이동 실패: {e}")
            
            # 일반 클릭 시도
            try:
                # 스크롤해서 요소를 화면 중앙에 위치
                driver.execute_script("arguments[0].scrollIntoView({block:'center', inline:'nearest'});", elem)
                time.sleep(0.5)
                
                # 오버레이 닫기
                try_close_overlays(driver)
                
                # 클릭 가능 상태까지 대기
                elem = WebDriverWait(driver, 3).until(EC.element_to_be_clickable((By.XPATH, RESULT_ITEM_XPATH)))
                elem.click()
                time.sleep(1)  # 클릭 후 잠시 대기
                # 클릭 후 현재 URL 가져오기
                current_url = driver.current_url
                return True, current_url
            except Exception as e:
                print(f"   ↳ 일반 클릭 실패: {e}")

        except Exception as e:
            print(f"   ↳ 클릭 시도 {attempt+1} 실패: {type(e).__name__}")
            time.sleep(0.3)

    print("❗ 첫 결과 클릭에 실패했어요.")
    return False, ""

# ----------------- 검색 → 첫 결과 클릭 → 상세 이동 -----------------
def open_first_product(driver, wait, title: str) -> tuple[bool, str]:
    q = urllib.parse.quote(title, safe=", ")
    driver.get(SEARCH_URL_TMPL.format(q=q))
    time.sleep(0.25)
    try_close_overlays(driver)

    # 검색 결과 컨테이너 등장 대기
    try:
        wait.until(lambda d: d.find_elements(By.CSS_SELECTOR, "#ContentsAreaWrap"))
    except TimeoutException:
        print("❗ 검색 결과 컨테이너가 나타나지 않았어요.")
        return False

    success, url = click_first_result(driver, wait)
    if not success:
        # 지연로딩/뷰포트 이슈 대비: 스크롤 재조정 후 한 번 더
        try:
            driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(0.1)
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(0.2)
        except Exception:
            pass
        success, url = click_first_result(driver, wait)
        if not success:
            return False, ""

    # 상세 페이지 로딩 대기 (더 유연한 방법들 시도)
    detail_loaded = False
    
    # 여러 방법으로 상세 페이지 로딩 확인
    detail_selectors = [
        '//*[@id="container"]',  # 컨테이너 존재 확인
        '//h1',                  # 제목 태그
        '//h2',                  # 부제목 태그
        '//*[contains(@class, "book")]',  # 책 관련 클래스
        '//*[contains(@class, "detail")]', # 상세 관련 클래스
    ]
    
    for selector in detail_selectors:
        try:
            wait.until(EC.presence_of_element_located((By.XPATH, selector)))
            print(f"   ↳ 상세 페이지 로딩 확인됨: {selector}")
            detail_loaded = True
            break
        except TimeoutException:
            continue
    
    if not detail_loaded:
        # URL 변경 확인으로 대체
        time.sleep(2)  # 추가 대기
        current_url = driver.current_url
        if "/book/detail/" in current_url:
            print("   ↳ URL 변경으로 상세 페이지 확인됨")
            detail_loaded = True
    
    if not detail_loaded:
        print("❗ 상세 페이지 로딩이 확인되지 않았어요.")
        print(f"   현재 URL: {driver.current_url}")
        return False, ""
    
    return True, url

# ----------------- 메인 -----------------
def main():
    base = os.path.dirname(os.path.abspath(__file__))
    csv_in  = os.path.join(base, "booklist_cleaned.csv")

    if not os.path.exists(csv_in):
        print("입력 파일이 없습니다:", csv_in)
        return

    rows = read_csv_flexible(csv_in)
    if not rows or len(rows) < 2:
        print("입력 CSV에 데이터가 없습니다.")
        return

    header = rows[0]
    data   = rows[1:]
    idxmap = header_index_map(header)

    # 🔴 검색 제목은 무조건 B열(두 번째 열) 사용 (0-based index=1)
    TITLE_COL_INDEX = 1

    driver = build_driver(headless=HEADLESS)
    wait = WebDriverWait(driver, PAGE_LOAD_WAIT)

    out_rows = [OUT_HEADER]
    fail_rows = [FAILURE_HEADER]

    # 처리할 범위 입력받기
    total_items = len(data)
    print(f"총 {total_items}개의 책이 있습니다.")
    
    start_num, end_num = get_range_input(total_items)
    if start_num is None or end_num is None:
        print("사용자가 취소했습니다.")
        return
    
    print(f"처리 범위: {start_num}번 ~ {end_num}번 ({end_num - start_num + 1}개)")
    
    # 출력 파일명에 범위 표시
    csv_out = os.path.join(base, f"booklist_update({start_num}_{end_num}).csv")
    csv_fail = os.path.join(base, f"booklist_notfound({start_num}_{end_num}).csv")
    
    # 범위에 맞는 데이터만 선택 (0-based index로 변환)
    data_iter = data[start_num-1:end_num]

    try:
        for i, row in enumerate(data_iter):
            # 실제 번호 계산 (시작번호 + 인덱스)
            seq = start_num + i
            
            # 행 길이 보정
            if len(row) < len(header):
                row += [""] * (len(header) - len(row))

            # B열에서 제목 획득 (비면 스킵)
            title = get_cell(row, TITLE_COL_INDEX)
            if not title:
                print(f"▶ [{seq}] 제목이 비어 있어 건너뜀")
                continue

            # 원본 값(우선순위) 가져오기
            orig_location = get_cell(row, idxmap["location"])
            orig_topic    = get_cell(row, idxmap["topic"])
            orig_series   = get_cell(row, idxmap["series"])
            orig_author   = get_cell(row, idxmap["author"])
            orig_pub      = get_cell(row, idxmap["publisher"])
            orig_ar       = get_cell(row, idxmap["ar"])
            orig_lexile   = get_cell(row, idxmap["lexile"])
            orig_format   = get_cell(row, idxmap["format"])
            orig_note     = get_cell(row, idxmap["note"])
            orig_isbn     = str(get_cell(row, idxmap["isbn"]))

            print(f"▶ [{seq}] 검색: {title}")

            # 기본값은 원본
            topic = orig_topic
            series = orig_series
            author = orig_author
            publisher = orig_pub
            ar = orig_ar
            lexile = orig_lexile
            book_format = orig_format
            note = orig_note
            isbn = orig_isbn
            book_url = ""  # URL 초기화

            # 원본 값이 비어 있는 항목만 스크랩으로 보완
            need_scrape = any(v == "" for v in [topic, series, author, publisher, ar, lexile, book_format, note, isbn])
            scrape_success = True
            failure_reason = ""
            failure_detail = ""

            if need_scrape:
                try:
                    success, book_url = open_first_product(driver, wait, title)
                    if success:
                        time.sleep(0.5)  # 상세 로딩 대기 시간 증가
                        print("   ↳ 상세 페이지에서 데이터 추출 중...")
                        
                        # Dem Bones인 경우 특별 처리
                        if "Dem Bones" in title:
                            if topic == "":       topic       = safe_text(driver, XPATH_TOPIC, "주제", ALT_XPATH_TOPIC, DEM_BONES_XPATHS.get("topic", []))   or ""
                            if series == "":      series      = safe_text(driver, XPATH_SERIES, "시리즈", ALT_XPATH_SERIES)  or ""
                            if author == "":      author      = safe_text(driver, XPATH_AUTHOR, "저자", ALT_XPATH_AUTHOR, DEM_BONES_XPATHS.get("author", []))  or ""
                            if publisher == "":   publisher   = safe_text(driver, XPATH_PUB, "출판사", ALT_XPATH_PUB, DEM_BONES_XPATHS.get("publisher", []))     or ""
                            if ar == "":          ar          = safe_text(driver, XPATH_AR, "AR", ALT_XPATH_AR, DEM_BONES_XPATHS.get("ar", []))      or ""
                            if lexile == "":      lexile      = safe_text(driver, XPATH_LEXILE, "Lexile", ALT_XPATH_LEXILE, DEM_BONES_XPATHS.get("lexile", []))  or ""
                            if book_format == "": book_format = safe_text(driver, XPATH_FORMAT, "형태", ALT_XPATH_FORMAT, DEM_BONES_XPATHS.get("format", []))  or ""
                            if note == "":
                                note_parts = []
                                for note_xpath in DEM_BONES_XPATHS.get("note", []):
                                    note_text = safe_text(driver, note_xpath, f"비고{len(note_parts)+1}")
                                    if note_text:
                                        note_parts.append(note_text)
                                note = " ".join(note_parts)
                            if isbn == "":        isbn        = str(safe_text(driver, XPATH_ISBN, "ISBN", ALT_XPATH_ISBN, DEM_BONES_XPATHS.get("isbn", [])) or "")
                        else:
                            # 일반적인 경우
                            if topic == "":       topic       = safe_text(driver, XPATH_TOPIC, "주제", ALT_XPATH_TOPIC, THIRD_XPATH_TOPIC, FOURTH_XPATH_TOPIC)   or ""
                            if series == "":      series      = safe_text(driver, XPATH_SERIES, "시리즈", ALT_XPATH_SERIES, THIRD_XPATH_SERIES)  or ""
                            if author == "":      author      = safe_text(driver, XPATH_AUTHOR, "저자", ALT_XPATH_AUTHOR, THIRD_XPATH_AUTHOR, FOURTH_XPATH_AUTHOR)  or ""
                            if publisher == "":   publisher   = safe_text(driver, XPATH_PUB, "출판사", ALT_XPATH_PUB, THIRD_XPATH_PUB, FOURTH_XPATH_PUB)     or ""
                            if ar == "":          ar          = safe_text(driver, XPATH_AR, "AR", ALT_XPATH_AR, THIRD_XPATH_AR, FOURTH_XPATH_AR)      or ""
                            if lexile == "":      lexile      = safe_text(driver, XPATH_LEXILE, "Lexile", ALT_XPATH_LEXILE, THIRD_XPATH_LEXILE, FOURTH_XPATH_LEXILE)  or ""
                            if book_format == "": book_format = safe_text(driver, XPATH_FORMAT, "형태", ALT_XPATH_FORMAT, THIRD_XPATH_FORMAT, FOURTH_XPATH_FORMAT)  or ""
                            if note == "":
                                n1 = safe_text(driver, XPATH_NOTE_1, "비고1", ALT_XPATH_NOTE_1, THIRD_XPATH_NOTE_1, FOURTH_XPATH_NOTE_1)
                                n2 = safe_text(driver, XPATH_NOTE_2, "비고2", ALT_XPATH_NOTE_2, THIRD_XPATH_NOTE_2, FOURTH_XPATH_NOTE_2)
                                note = " ".join([t for t in [n1, n2] if t])
                            if isbn == "":        isbn        = str(safe_text(driver, XPATH_ISBN, "ISBN", ALT_XPATH_ISBN, THIRD_XPATH_ISBN, FOURTH_XPATH_ISBN) or "")
                    else:
                        print("   ↳ 검색 실패(스크랩 생략)")
                        scrape_success = False
                        failure_reason = "검색 결과 없음"
                        failure_detail = "검색 결과에서 첫 번째 항목을 클릭할 수 없음"
                except Exception as e:
                    print(f"   ↳ 상세 추출 중 예외: {type(e).__name__}")
                    scrape_success = False
                    failure_reason = "상세 페이지 접근 실패"
                    failure_detail = f"예외 발생: {type(e).__name__}"
            else:
                print("   ↳ 모든 정보가 있어 스크랩 생략")

            # ISBN을 문자열로 강제 변환 (CSV에서 숫자로 인식되지 않도록)
            isbn_str = f"'{isbn}" if isbn else ""
            
            # 출력 행 구성: 원본 우선, 비었으면 스크랩값
            out_rows.append([
                seq,               # Number
                title,             # 책 제목 (B열)
                orig_location,     # 위치 (원본 사용)
                topic,             # 주제
                series,            # 시리즈
                author,            # 저자
                publisher,         # 출판사
                ar,                # AR
                lexile,            # Lexile (L)
                book_format,       # 형태
                note,              # 비고
                isbn_str,          # ISBN (문자열로 강제 변환)
                book_url           # URL
            ])
            
            # 실패한 경우 실패 리스트에 추가
            if need_scrape and not scrape_success:
                fail_rows.append([
                    seq,               # Number
                    title,             # 책 제목
                    failure_reason,    # 실패 원인
                    failure_detail     # 상세 정보
                ])
                print(f"   ❌ 실패 리스트에 추가됨: {failure_reason}")
            
            time.sleep(0.2)  # 과도한 요청 방지
    finally:
        driver.quit()

    # 결과 저장 (엑셀 호환 위해 utf-8-sig 권장)
    with open(csv_out, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        for row in out_rows:
            # 한글 깨짐 방지를 위해 각 셀을 명시적으로 인코딩
            encoded_row = []
            for cell in row:
                if isinstance(cell, str):
                    encoded_row.append(cell)
                else:
                    encoded_row.append(str(cell))
            writer.writerow(encoded_row)

    # 실패 리스트 저장
    with open(csv_fail, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        for row in fail_rows:
            # 한글 깨짐 방지를 위해 각 셀을 명시적으로 인코딩
            encoded_row = []
            for cell in row:
                if isinstance(cell, str):
                    encoded_row.append(cell)
                else:
                    encoded_row.append(str(cell))
            writer.writerow(encoded_row)

    print(f"✅ 완료: {csv_out} (총 {len(out_rows)-1}건)")
    print(f"📋 실패 리스트: {csv_fail} (총 {len(fail_rows)-1}건)")

if __name__ == "__main__":
    main()
