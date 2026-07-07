# Book Info Crawling Project

Wendybook 검색 결과를 기반으로 도서 정보를 자동 수집하고 CSV로 저장하는 Python Selenium 프로젝트입니다.

## 주요 기능
- `booklist_cleaned.csv`의 책 제목을 기준으로 검색
- 검색 결과 첫 번째 도서 상세 페이지 접속
- 주제, 시리즈, 저자, 출판사, AR, Lexile, 형태, ISBN, URL 수집
- 결과 CSV 및 실패 목록 CSV 생성
- 처리 범위 선택 GUI 제공

## 사용 기술
- Python
- Selenium
- webdriver-manager
- tkinter
- csv

## 실행 방법

```bash
pip install -r requirements.txt
python fill_book_info.py
