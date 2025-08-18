import json
import pandas as pd
import time
from selenium import webdriver
from bs4 import BeautifulSoup
from urllib.request import urlopen
from datetime import datetime


# 이벤트 목록 크롤링 함수
def eventList(is_brand_sale):

    url = ""

    if is_brand_sale:
        print("======= [국민] 브랜드 할인 정보 리스트업 =======")
        url = "https://card.kbcard.com/BON/DVIEW/HBBMCXCRVNEC0002"
    else:
        print("======= [국민] KB 이벤트 정보 리스트업 =======")
        url = "https://card.kbcard.com/BON/DVIEW/HBBMCXCRVNEC0001"

    event_codes = []
    event_images = []
    event_stores = []  # is_brand_sale
    event_subjects = []
    event_start = []
    event_end = []
    event_categories = []

    html = urlopen(url)
    soup1 = BeautifulSoup(html, "html.parser")

    # 총 페이지 수 찾기
    paging_div = soup1.find("div", class_="paging")
    if paging_div:
        page_links = paging_div.find_all("a", href=True)
    else:  # is_brand_sale
        page_links = [1]

    driver = webdriver.Chrome()
    driver.get(url)

    for page in range(1, len(page_links) + 1):

        if is_brand_sale:
            print(f"{datetime.now()} --- 웹 페이지에 접속 중...")
        else:
            # is_brand_sale == false 인 경우 각 페이지별로 파싱
            print(
                f"{datetime.now()} [{page}/{len(page_links)}] --- 웹 페이지에 접속 중..."
            )

            # JavaScript 함수 호출
            driver.execute_script(f'doSearchSpider("HBBMCXCRVNEC0001", "{page}")')
            time.sleep(2)  # 페이지 로딩 대기

        soup2 = BeautifulSoup(driver.page_source, "html.parser")

        # 이벤트 항목 찾기
        event_list = soup2.find("ul", {"class": "eventList"})
        if event_list:
            event_items = event_list.find_all("li", recursive=False)

            for item in event_items:
                a_tag = item.find("a")
                if not a_tag:
                    continue

                # 이벤트 고유 코드 추출
                href = a_tag.get("href", "")
                if "goDetail(" not in href:
                    continue
                try:
                    code = href.split("goDetail('")[1].split("'")[0]
                except IndexError:
                    code = ""
                event_codes.append(code)

                # 이미지 URL
                img_tag = item.find("img")
                img_src = img_tag["src"] if img_tag else ""
                event_images.append(img_src)

                # 브랜드 (store)
                store = ""
                if is_brand_sale:
                    store_tag = item.find("span", {"class": "store"})
                    store = (
                        store_tag.get_text(separator=" ", strip=True)
                        if store_tag
                        else ""
                    )
                event_stores.append(store)

                # 제목
                subject_tag = item.find("span", {"class": "subject"})
                subject = (
                    subject_tag.get_text(separator=" ", strip=True)
                    if subject_tag
                    else ""
                )
                event_subjects.append(subject)

                # 날짜 → start_date / end_date
                start_date, end_date = "", ""
                date_tag = item.find("span", {"class": "date"})
                if date_tag:
                    date_text = date_tag.text.strip().replace(" ", "")
                    try:
                        start_str, end_str = date_text.split("~")
                        start_date = datetime.strptime(start_str, "%Y.%m.%d").strftime(
                            "%Y-%m-%d"
                        )
                        end_date = datetime.strptime(end_str, "%Y.%m.%d").strftime(
                            "%Y-%m-%d"
                        )
                    except ValueError:
                        pass
                event_start.append(start_date)
                event_end.append(end_date)

                # 카테고리 (여러 개일 수 있음)
                category_box = item.find("span", {"class": "category"})
                categories = []
                if category_box:
                    for em in category_box.find_all("em"):
                        categories.append(em.text.strip())
                event_categories.append(json.dumps(categories, ensure_ascii=False))

        else:
            print("❌ <ul class='eventList'>를 찾을 수 없습니다.")

    # 결과 저장
    if is_brand_sale:
        data = {
            "event_code": event_codes,
            "event_store": event_stores,
            "event_subject": event_subjects,
            "event_image": event_images,
            "event_start": event_start,
            "event_end": event_end,
        }
        df = pd.DataFrame(data)
        df.to_csv("./Kookmin_BrandSale_list.csv", encoding="utf-8-sig")
        print("✅ 이벤트 정보를 Kookmin_BrandSale_list.csv로 저장 완료.")
    else:
        data = {
            "event_code": event_codes,
            "event_subject": event_subjects,
            "event_image": event_images,
            "event_start": event_start,
            "event_end": event_end,
            "event_categories": event_categories,
        }
        df = pd.DataFrame(data)
        df.to_csv("./Kookmin_KBevent_list.csv", encoding="utf-8-sig")
        print("✅ 이벤트 정보를 Kookmin_KBevent_list.csv로 저장 완료.")


eventList(True)  # 브랜드 할인 목록 크롤링
eventList(False)  # KB 이벤트 목록 크롤링


# 이벤트 상세 정보 크롤링 함수
def eventDetail(is_brand_sale):

    event_infos = None
    event_subjects = []

    if is_brand_sale:
        event_infos = pd.read_csv("./Kookmin_BrandSale_list.csv")
        event_subjects = (
            event_infos["event_store"] + " " + event_infos["event_subject"]
        ).to_list()
        print("======= [국민] 브랜드 할인 상세 정보 크롤링 =======")

    else:
        event_infos = pd.read_csv("./Kookmin_KBevent_list.csv")
        event_subjects = event_infos["event_subject"].to_list()
        print("======= [국민] KB 이벤트 상세 정보 크롤링 =======")

    event_urls = []
    event_images = event_infos["event_image"].to_list()
    event_details = []
    event_codes = event_infos["event_code"].to_list()
    created_at = []

    for i in range(len(event_codes)):
        event_url = None

        if is_brand_sale:
            event_url = (
                "https://card.kbcard.com/BON/DVIEW/HBBMCXCRVNEC0002?mainCC=a&eventNum="
                + str(event_codes[i])
            )
        else:
            event_url = (
                "https://card.kbcard.com/BON/DVIEW/HBBMCXCRVNEC0001?mainCC=a&eventNum="
                + str(event_codes[i])
            )

        html = urlopen(event_url)
        soup = BeautifulSoup(html, "html.parser")

        event_urls.append(event_url)
        created_at.append(datetime.now())

        print(
            f"{datetime.now} [{event_subjects[i]}] --- 웹 페이지에 접속 중... ({i+1}/{len(event_codes)})"
        )

        event_body = soup.find("div", {"id": "eventBodyRE"})
        if event_body:
            detail_elements = event_body.find_all(
                ["p", "li", "h1", "h2", "h3", "h4", "h5", "h6", "dt", "dd"]
            )
            detail = ", ".join(elem.get_text(strip=True) for elem in detail_elements)
            event_details.append(detail)

    data = {
        "event_subject": event_subjects,
        "event_url": event_urls,
        "event_image": event_images,
        "event_detail": event_details,
        "event_code": event_codes,
        "created_at": created_at,
    }
    df = pd.DataFrame(data)

    if is_brand_sale:
        df.to_csv("./Event/Kookmin_BrandSale_detail.csv", encoding="utf-8-sig")
        print("Kookmin_events_detail.csv가 생성되었습니다.")
    else:
        df.to_csv("./Event/Kookmin_KBevent_detail.csv", encoding="utf-8-sig")
        print("Kookmin_KBevent_detail.csv가 생성되었습니다.")


eventDetail(True)  # 브랜드 할인 상세 정보 추출
eventDetail(False)  # KB 이벤트 상세 정보 추출
