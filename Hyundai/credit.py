import pandas as pd
import time
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import re

import json

with open('config.json', 'r') as f:
    config = json.load(f)

chrome_path = config.get("chrome_path")


'''
    신용 카드 리스트 조회
    hyundai_creditcardInfos.csv : card_name, card_url, card_img
'''
url = "https://www.hyundaicard.com/cpc/ma/CPCMA0101_01.hc?cardflag=ALL"

chrome_options = Options()

# Chrome 설치된 경로로 변경
chrome_options.binary_location = chrome_path  

chrome_options.add_argument('--headless')
chrome_options.add_argument('--disable-web-security')

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

driver.implicitly_wait(20)
print("======= [현대] 신용 카드 리스트 크롤링 =======")
print("웹 페이지에 접속 중...")
driver.get(url)
time.sleep(3)

html = driver.page_source

soup = BeautifulSoup(html, 'html.parser')

card_names = []
card_urls = []
card_imgs = []


# 카드 정보 추출 함수
def extract_card_info_from_url(list_url, card_url_prefix):
    driver.get(list_url)
    time.sleep(3)
    html = driver.page_source
    soup_deep1 = BeautifulSoup(html, 'html.parser')
    
    ul_class = soup_deep1.find_all('ul', class_='list05')
    
    for ul in ul_class:
        li_class = ul.find_all('li')
        if li_class:
            for li in li_class:
                name = li.find('span', class_='h4_b_lt')
                if name:
                    card_names.append(name.text.strip())
                
                # card_plt라는 class를 가진 div 안의 <a> 태그에서 카드 코드 추출
                card_div = li.find('div', class_='card_plt')
                if card_div:
                    a_tag = card_div.find('a')
                    if a_tag and 'onclick' in a_tag.attrs:
                        onclick_text = a_tag['onclick']  # 예: "javascript:goCardDetail('TRSCSTE2');"
                        match = re.search(r"goCardDetail\('([^']+)'\)", onclick_text)
                        if match:
                            card_code = match.group(1)
                            
                            card_imgs.append(f'https://img.hyundaicard.com/img/com/card/card_{card_code}_h.png')
                            card_urls.append(f'{card_url_prefix}{card_code}&eventCode=00000')


card_section = soup.find_all('ul', class_='list05')

for i in range(len(card_section)):
    list_elements = card_section[i].find_all('div', class_='card_plt')

    for element in list_elements:
        card_name_element = element.find('span', class_='h4_b_lt')
        card_name = card_name_element.text.strip()

        if card_name == "기아":
            extract_card_info_from_url('https://www.hyundaicard.com/cpc/cr/CPCCR0621_11.hc?cardflag=K#aTab_1', 
                                       'https://www.hyundaicard.com/cpc/cr/CPCCR0201_01.hc?cardflag=K&cardWcd=')
            continue

        if card_name == "현대자동차":
            extract_card_info_from_url('https://www.hyundaicard.com/cpc/cr/CPCCR0621_11.hc?cardflag=H',
                                       'https://www.hyundaicard.com/cpc/cr/CPCCR0201_01.hc?cardflag=H&cardWcd=')
            continue

        if card_name == "대한항공":
            extract_card_info_from_url('https://www.hyundaicard.com/cpc/cr/CPCCR0621_11.hc?cardflag=D', 
                                       'https://www.hyundaicard.com/cpc/cr/CPCCR0201_01.hc?cardflag=D&cardWcd=')
            continue

        if card_name == "American Express":
            extract_card_info_from_url('https://www.hyundaicard.com/cpc/ma/CPCMA0101_01.hc?cardflag=AX', 
                                       'https://www.hyundaicard.com/cpc/cr/CPCCR0201_01.hc?cardWcd=')
            continue

        if card_name == "이마트":
            extract_card_info_from_url('https://www.hyundaicard.com/cpc/cr/CPCCR0621_11.hc?cardflag=E',
                                       'https://www.hyundaicard.com/cpc/cr/CPCCR0201_01.hc?cardflag=E&cardWcd=')
            continue

        if card_name == "지마켓(스마일카드)":
            extract_card_info_from_url('https://www.hyundaicard.com/cpc/cr/CPCCR0621_11.hc?cardflag=S', 
                                       'https://www.hyundaicard.com/cpc/cr/CPCCR0201_01.hc?cardflag=S&cardWcd=')
            continue

        if card_name == "코스트코":
            extract_card_info_from_url('https://www.hyundaicard.com/cpc/cr/CPCCR0621_11.hc?cardflag=T', 
                                       'https://www.hyundaicard.com/cpc/cr/CPCCR0201_01.hc?cardflag=T&cardWcd=')
            continue

        if card_name == "미래에셋증권":
            extract_card_info_from_url('https://www.hyundaicard.com/cpc/cr/CPCCR0621_11.hc?cardflag=MA', 
                                       'https://www.hyundaicard.com/cpc/cr/CPCCR0201_01.hc?cardflag=MA&cardWcd=')
            continue

        if card_name == "넥슨":
            extract_card_info_from_url('https://www.hyundaicard.com/cpc/cr/CPCCR0621_11.hc?cardflag=N', 
                                       'https://www.hyundaicard.com/cpc/cr/CPCCR0201_01.hc?cardflag=MA&cardWcd=')
            continue

        if card_name == "KT":
            extract_card_info_from_url('https://www.hyundaicard.com/cpc/cr/CPCCR0621_11.hc?cardflag=J&ctgrCd=050401',
                                       'https://www.hyundaicard.com/cpc/cr/CPCCR0201_01.hc?cardflag=MA&cardWcd=')
            continue

        if card_name == "SKT":
            extract_card_info_from_url('https://www.hyundaicard.com/cpc/cr/CPCCR0621_11.hc?cardflag=J&ctgrCd=050403',
                                       'https://www.hyundaicard.com/cpc/cr/CPCCR0201_01.hc?cardflag=MA&cardWcd=')
            continue

        '''
        2024년 4월 1일부터 신규ㆍ교체ㆍ갱신 발급이 종료된 카드

        if card_name == "롯데면세점":
            extract_card_info_from_url('https://www.hyundaicard.com/cpc/cr/CPCCR0621_11.hc?cardflag=J&ctgrCd=050605')
            continue
        '''

        if card_name == "SC제일은행":
            extract_card_info_from_url('https://www.hyundaicard.com/cpc/cr/CPCCR0621_11.hc?cardflag=J&ctgrCd=050703',
                                       'https://www.hyundaicard.com/cpc/cr/CPCCR0201_01.hc?cardflag=MA&cardWcd=')
            continue

        if card_name == "경차":
            extract_card_info_from_url('https://www.hyundaicard.com/cpc/cr/CPCCR0621_11.hc?cardflag=J&ctgrCd=050802',
                                       'https://www.hyundaicard.com/cpc/cr/CPCCR0201_01.hc?cardflag=MA&cardWcd=')
            continue

        if card_name == "화물차":
            extract_card_info_from_url('https://www.hyundaicard.com/cpc/cr/CPCCR0621_11.hc?cardflag=J&ctgrCd=050803',
                                       'https://www.hyundaicard.com/cpc/cr/CPCCR0201_01.hc?cardflag=MA&cardWcd=')
            continue

        if card_name in ["쏘카", "제네시스", "야놀자ㆍ인터파크(NOL 카드)", "무신사", "SSG.COM", "네이버", "배달의민족", 
                         "스타벅스", "GS칼텍스", "LG U+", "기타", "현대홈쇼핑", "예스24", "하이마트", "The CJ", 
                         "coway-현대카드M Edition3", "LG전자-현대카드M Edition3", "햇살론", "인플카 현대카드"]:
            card_names.append(card_name_element.text.strip())

            card_img_element = element.find('img').get('src')
            card_imgs.append(card_img_element)

            # card_img_element의 "card_" 다음과 "_h.png" 이전 문자열 추출
            card_url_code = card_img_element.split('card_')[1].replace('_h.png', '')
            print('코드' + card_url_code)
            card_urls.append('https://www.hyundaicard.com/cpc/cr/CPCCR0201_01.hc?cardWcd=' + card_url_code)
            continue


        if card_name == "체크카드" or card_name == "Gift카드" or card_name == "후불하이패스카드":
            continue

        card_names.append(card_name_element.text.strip())

        card_img_element = element.find('img').get('src')
        card_imgs.append(card_img_element)

        card_code_a = element.find('a')
        card_code = card_code_a.get('onclick')
        if card_code:
            start_index = card_code.find("'") + 1
            end_index = card_code.find("'", start_index)
            card_url_code = card_code[start_index:end_index]

        if card_name in ["MY BUSINESS M Food&Drink", "MY BUSINESS M Retail&Service", "MY BUSINESS M Online Seller", 
                         "MY BUSINESS X Food&Drink", "MY BUSINESS X Retail&Service", "MY BUSINESS X Online Seller", 
                         "MY BUSINESS ZERO Food&Drink", "MY BUSINESS ZERO Retail&Service", "MY BUSINESS ZERO Online Seller"]:
            card_code2 = card_code_a.get('href')
            start_index = card_code2.find("'") + 1
            end_index = card_code2.find("'", start_index)
            card_url_code = card_code2[start_index:end_index]

        card_urls.append('https://www.hyundaicard.com/cpc/cr/CPCCR0201_01.hc?cardWcd=' + card_url_code)

print("작업을 완료했습니다.")
driver.quit()

data = {"card_name" : card_names, "card_url" : card_urls, "card_img": card_imgs}
df = pd.DataFrame(data)

df.to_csv("./hyundai_creditcardInfos.csv", encoding = "utf-8-sig")

'''
    신용 카드 혜택 크롤링
    credit_benefit.csv : card_company_id, name, img_url, benefits, created_at, type
'''
card_infos = pd.read_csv('./hyundai_creditcardInfos.csv')

card_urls = card_infos['card_url'].tolist()
name = card_infos['card_name'].tolist()
img_url = card_infos['card_img'].tolist()

card_company_id = [2] * len(card_urls)
benefits = []

created_at = []
type = ["CreditCard"] * len(card_urls)

print("======= [현대] 전체 카드 혜택 정보 크롤링 =======")
for i in range(len(card_urls)):
#for i in range(1,2):
    chrome_options = Options()

    # Chrome 설치된 경로로 변경
    chrome_options.binary_location = chrome_path  
        
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-web-security')

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

    driver.implicitly_wait(20)
    now = datetime.now()
    created_at.append(now)
    print(f"{now} --- 웹 페이지에 접속 중... ({i+1}/{len(card_urls)})")

    driver.get(card_urls[i])
    time.sleep(3)

    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')

    # 상세 혜택 =============================================
    popup_containers = soup.find_all('div', class_='modal_pop')
    
    exclude_ids = {
        'popup_call_reservation',
        'cardApplyPop',
        'popCardSelect',
        'popCardUse',
        'footerFamilySite',
        'popDisSS',
        'popQrCode',
        'popMemberFee'
        }
    
    texts = []
    
    for container in popup_containers:
        container_id = container.get('id')

        if container_id in exclude_ids:
            continue
        
        print(f"출력중인 MODAL의 id: {container_id}")
        elements = []
        text_tags = ['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p']
        all_tags = text_tags + ['li']

        for el in container.find_all(all_tags):
            if el.name == 'li':
                if el.find(text_tags) is None:
                    elements.append(el)
            else:
                elements.append(el)


        for el in elements:
            # print(el.get_text(strip=True))
            texts.append(el.get_text(strip=True))

    benefits.append(texts)

print("작업을 완료했습니다.")
driver.quit()

'''
    신용 카드 혜택 크롤링
    credit_benefit.csv : card_company_id, name, img_url, benefits, created_at, type
'''

data = {"card_company_id": card_company_id, "name": name, "img_url": img_url, "benefits" : benefits, "created_at": created_at, "type": type}
df = pd.DataFrame(data)

df.to_csv("./credit_benefit.csv", encoding = "utf-8-sig", index=False)
