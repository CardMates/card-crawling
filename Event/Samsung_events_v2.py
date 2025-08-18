import json
import pandas as pd
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
from urllib.request import urlopen
from datetime import datetime


with open("config.json", "r") as f:
    config = json.load(f)

chrome_path = config.get("chrome_path")


# 이벤트 목록 크롤링 함수
def eventList():
    print("======= [삼성] 진행중인 이벤트 정보 리스트업 =======")

    event_codes = []
    event_images = []
    event_subjects = []
    event_start = []
    event_end = []

    options = webdriver.ChromeOptions()  # Chrome 드라이버 설정
    options.binary_location = chrome_path  # Chrome 설치된 경로로 변경
    options.add_argument("--headless")  # 브라우저 창 없이 실행 (필요시 제거)
    driver = webdriver.Chrome(service=Service(), options=options)

    # 페이지 열기
    url = "https://www.samsungcard.com/personal/event/ing/UHPPBE1401M0.jsp"
    driver.get(url)

    # li 요소가 로드될 때까지 대기
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located(
                (By.CSS_SELECTOR, "ul#board_append > li")
            )
        )

        # <li> 목록 수집
        event_items = driver.find_elements(By.CSS_SELECTOR, "ul#board_append > li")

        for item in event_items:
            # 이벤트 고유 코드
            code = item.get_attribute("id")
            if code:
                event_codes.append(code)

            # 이미지 URL
            try:
                img_tag = item.find_element(By.CSS_SELECTOR, "img.m_display")
                img_src = img_tag.get_attribute("src")
            except:
                img_src = ""
            event_images.append(img_src)

            # 제목
            try:
                subject = item.find_element(By.CSS_SELECTOR, "p.tit").text.strip()
            except:
                subject = ""
            event_subjects.append(subject)

            # 날짜 → start_date / end_date
            start_date, end_date = "", ""
            try:
                date_text = item.find_element(By.CSS_SELECTOR, "span.date").text.strip()
                if "~" in date_text:
                    start_str, end_str = date_text.split("~")
                    start_date = datetime.strptime(start_str, "%Y.%m.%d").strftime(
                        "%Y-%m-%d"
                    )
                    end_date = datetime.strptime(end_str, "%Y.%m.%d").strftime(
                        "%Y-%m-%d"
                    )
            except:
                pass
            event_start.append(start_date)
            event_end.append(end_date)

    finally:
        driver.quit()

    # 결과 저장
    data = {
        "event_code": event_codes,
        "event_subject": event_subjects,
        "event_image": event_images,
        "event_start": event_start,
        "event_end": event_end,
    }
    df = pd.DataFrame(data)
    df.to_csv("./Samsung_event_list.csv", encoding="utf-8-sig")
    print("✅ 이벤트 정보를 Samsung_event_list.csv로 저장 완료.")


eventList()


def eventDetail():
    print("======= [삼성] 진행중인 이벤트 상세 정보 크롤링 =======")
    event_infos = pd.read_csv("./Samsung_event_list.csv")

    event_subjects = event_infos["event_subject"].to_list()
    event_urls = []
    event_images = event_infos["event_image"].to_list()
    event_details = []
    event_codes = event_infos["event_code"].to_list()
    created_at = []

    options = webdriver.ChromeOptions()  # Chrome 드라이버 설정
    options.binary_location = chrome_path  # Chrome 설치된 경로로 변경
    options.add_argument("--headless")  # 브라우저 창 없이 실행 (필요시 제거)
    driver = webdriver.Chrome(service=Service(), options=options)

    for i in range(len(event_codes)):
        event_url = (
            "https://www.samsungcard.com/personal/event/ing/UHPPBE1403M0.jsp?cms_id="
            + str(event_codes[i])
        )

        print(
            f"{datetime.now} [{event_subjects[i]}] --- 웹 페이지에 접속 중... ({i+1}/{len(event_codes)})"
        )

        driver.get(event_url)

        event_urls.append(event_url)
        created_at.append(datetime.now())

        try:
            # dl.new_dl 요소가 로딩될 때까지 대기
            event_body = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "dl.new_dl"))
            )

            # 내부 모든 텍스트 요소 수집
            detail_elements = event_body.find_elements(
                By.CSS_SELECTOR, "dt, dd, p, li, div, span"
            )
            detail = ", ".join(
                elem.text.strip() for elem in detail_elements if elem.text.strip()
            )
            event_details.append(detail)

        except:
            print("Event_Body가 없습니다.")
            event_details.append("")

    data = {
        "event_subject": event_subjects,
        "event_url": event_urls,
        "event_image": event_images,
        "event_detail": event_details,
        "event_code": event_codes,
        "created_at": created_at,
    }
    df = pd.DataFrame(data)

    df.to_csv("./Event/Samsung_events_detail.csv", encoding="utf-8-sig")
    print("Samsung_events_detail.csv가 생성되었습니다.")


eventDetail()
