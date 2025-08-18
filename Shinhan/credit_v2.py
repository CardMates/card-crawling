import pandas as pd
import time
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options 
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

import json

with open('config.json', 'r') as f:
    config = json.load(f)

chrome_path = config.get("chrome_path")

'''
    카드 정보 조회
    shinhan_cardInfos.csv : card_name, card_url, card_img
'''
url = "https://www.shinhancard.com/pconts/html/card/credit/MOBFM281/MOBFM281R11.html"

chrome_options = Options()

# Chrome 설치된 경로로 변경
chrome_options.binary_location = chrome_path  

chrome_options.add_argument('--headless')  

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

driver.implicitly_wait(20)
print("======= [신한] 신용 카드 정보 크롤링 =======")
print("웹 페이지에 접속 중...")
driver.get(url)
time.sleep(3)

html = driver.page_source

soup = BeautifulSoup(html, 'html.parser')

card_names = []
card_urls = []
card_imgs = []

div_tag = soup.find('div', {'data-plugin-view': 'cmmCardList'})
ul_tag = div_tag.find('ul', {'class': 'card_thumb_list_wrap'})

list_elements = ul_tag.find_all('li')
    
for idx, element in enumerate(list_elements, 1):
    card_name_element = element.find('a', class_='card_name')

    card_names.append(card_name_element.text.strip())

a_tag = ul_tag.find_all('a')

for i in range(len(a_tag)):
    card_urls.append(a_tag[i].get('href').split('/')[-1])

card_urls = list(dict.fromkeys(card_urls)) # 중복 제거

for i in range(0, len(a_tag), 3):
    card_imgs.append('https://www.shinhancard.com' + a_tag[i].find('img')['src'])

print("작업을 완료했습니다.")
driver.quit()

data = {"card_name" : card_names, "card_url" : card_urls, "card_img": card_imgs}
df = pd.DataFrame(data)

df.to_csv("./shinhan_cardInfos.csv", encoding = "utf-8-sig")

'''
    전체 카드 혜택 크롤링
    credit_benefit.csv : card_company_id, name, img_url, benefits, created_at, type
'''
card_infos = pd.read_csv('./shinhan_cardInfos.csv')


card_urls = card_infos['card_url'].tolist()
name = card_infos['card_name'].tolist()
img_url = card_infos['card_img'].tolist()

card_company_id = [4] * len(card_urls) # 신한카드
benefits = []

created_at = []
type = ["CreditCard"] * len(card_urls)

print("======= [신한] 전체 카드 혜택 정보 크롤링 =======")
for i in range(len(card_urls)):
    url = f'https://www.shinhancard.com/pconts/html/card/apply/credit/{card_urls[i]}'

    chrome_options = Options()

    # Chrome 설치된 경로로 변경
    chrome_options.binary_location = chrome_path  

    chrome_options.add_argument('--headless')  

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

    driver.implicitly_wait(20)
    now = datetime.now()
    created_at.append(now)
    print(f"{now} [{card_names[i]}] --- 웹 페이지에 접속 중... ({i+1}/{len(card_urls)})")

    driver.get(url)
    time.sleep(3)

    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')

    # 상세 혜택 =============================================            
    tap_wrap = soup.find('div', {'class':'tab_wrap'})
    hidden_tap = tap_wrap.find_all('li', {'aria-hidden':'true'})

    benefit_title = [] # 탭 제목들 (혜택 제목)
    benefit = ''
    for i in range(len(hidden_tap)):
        benefit_title.append(hidden_tap[i].find('h2', {'class':'hidden-text'}).text.strip())

    for i in range(len(hidden_tap)):
        benefit += f'###{benefit_title[i]}'
        tit_dep2 = hidden_tap[i].find_all(class_="tit_dep2")

        for title in tit_dep2:
            benefit += f'[{title.text.strip()}]'
            next_sibling = title.find_next_sibling()
            while next_sibling:
                if next_sibling.name == 'div' and 'table_wrap' in next_sibling.get('class', []):
                    table = next_sibling.select_one('table')
                    # 표가 있을 때만 출력
                    if table:
                        benefit += str(table)
                            
                elif next_sibling.name == 'p':
                    class_list = next_sibling.get('class', [])
                    if ('marker_dot' in class_list) or ('marker_refer' in class_list):
                        benefit += next_sibling.text.strip()
                elif next_sibling.name == 'ul':
                    class_list = next_sibling.get('class', [])
                    if ('marker_dot' in class_list) or ('marker_refer' in class_list) or ('marker_hyphen' in class_list):
                        li_list = next_sibling.find_all('li', recursive=False)
                        for li in li_list:
                            benefit += li.text.strip()

                # 다음 형제 요소 찾을 때 특정 조건을 만족하면 루프 종료
                if 'tit_dep2' in next_sibling.get('class', []) or ('h4' in next_sibling.name and 'tit_dep3' in next_sibling.get('class', [])):
                    break
                
                next_sibling = next_sibling.find_next_sibling()
        
        tit_dep3 = hidden_tap[i].find_all('h4', class_="tit_dep3")
        if tit_dep3:
            for title in tit_dep3:
                benefit += f'[{title.text.strip()}]'
                next_sibling = title.find_next_sibling()
                while next_sibling:
                    if next_sibling.name == 'div' and 'table_wrap' in next_sibling.get('class', []):
                        table = next_sibling.select_one('table')
                        # 표가 있을 때만 출력
                        if table:
                            benefit += str(table)

                    elif next_sibling.name == 'p':
                        class_list = next_sibling.get('class', [])
                        if ('marker_dot' in class_list) or ('marker_refer' in class_list):
                            benefit += next_sibling.text.strip()
                            
                    elif next_sibling.name == 'ul':
                        class_list = next_sibling.get('class', [])
                        if ('marker_dot' in class_list) or ('marker_refer' in class_list) or ('marker_hyphen' in class_list):
                            li_list = next_sibling.find_all('li', recursive=False)
                            for li in li_list:
                                benefit += li.text.strip()

                    # 다음 형제 요소 찾을 때 특정 조건을 만족하면 루프 종료
                    if 'tit_dep3' in next_sibling.get('class', []):
                        break
                    
                    next_sibling = next_sibling.find_next_sibling()
                    
    benefits.append(benefit)

print("작업을 완료했습니다.")
driver.quit()

'''
    전체 카드 혜택 크롤링
    credit_benefit.csv : card_company_id, name, img_url, benefits, created_at, type
'''

data = {"card_company_id": card_company_id, "name": name, "img_url": img_url, "benefits" : benefits, "created_at": created_at, "type": type}
df = pd.DataFrame(data)

df.to_csv("./credit_benefit.csv", encoding = "utf-8-sig", index=False)