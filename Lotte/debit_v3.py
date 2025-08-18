import pandas as pd
import time
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import re
from urllib.request import urlopen
from urllib.error import HTTPError, URLError

import json

with open('config.json', 'r') as f:
    config = json.load(f)

chrome_path = config.get("chrome_path")



# 체크카드 목록 크롤링 함수
def cardList(associate):
    is_associate_card = '일반'
    if associate:
        is_associate_card = '제휴'

    url = 'https://www.lottecard.co.kr/app/LPCDAEA_V100.lc'

    chrome_options = Options()

    # Chrome 설치된 경로로 변경
    chrome_options.binary_location = chrome_path  

    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-web-security')
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    
    driver.implicitly_wait(20)
    print("======= [롯데] 신용 카드 리스트 크롤링 (" + is_associate_card + ")=======")
    print("웹 페이지에 접속 중...")
    driver.get(url)    # 웹 페이지 로드
    time.sleep(3)

    if(associate):
        # 제휴 카드 클릭
        link = driver.find_element(By.LINK_TEXT,"제휴")
        link.click()
        time.sleep(5)

    # Selenium으로 페이지 스크랩
    rendered_html = driver.page_source

    # BeautifulSoup을 사용하여 HTML 파싱
    soup = BeautifulSoup(rendered_html, 'html.parser')

    # 더보기 버튼 끝까지 누르기
    while True:
        new_render_html = driver.page_source
        soup = BeautifulSoup(new_render_html, 'html.parser')
        if soup.find('button',{'id':'btnMore'}) is None: break
        driver.find_element(By.ID, "btnMore").click()
        time.sleep(3)

    li_list = soup.find('ul', {'id':'ajaxCardList'}).find_all('li')

    
    for li in li_list:
        a_tag = li.find('a')
        if not a_tag:
          continue

        # 카드 코드 추출
        onclick_attr = a_tag.get('onclick', '')
        match = re.search(r"GoDet\('([^']+)'\)", onclick_attr)
        if match:
            card_code = match.group(1)
            card_codes.append(card_code)
            card_urls.append('https://www.lottecard.co.kr/app/LPCDADB_V100.lc?vtCdKndC=' + card_code)
            card_imgs.append('//image.lottecard.co.kr/UploadFiles/ecenterPath/cdInfo/ecenterCdInfo' + card_code +'_nm1.png')
        
        # 카드 이름 추출
        title_tag = a_tag.find('b', class_='tit')
        if title_tag:
            card_name = title_tag.get_text(strip=True)
            card_names.append(card_name)
        
    print("카드 리스트 추출을 완료했습니다.")
    driver.quit()

    
# 페이지 크롤링 함수
def cardCrawling (cardurl):
    benefits=""
    
    try:
        cardhtml = urlopen(cardurl)
        cardbs = BeautifulSoup(cardhtml, 'html.parser')
    except (HTTPError, URLError) as e:
        return "존재하지 않는 카드입니다"

    # 유효한 페이지인지 검증 - 핵심 요소가 없으면 존재하지 않는 카드로 판단
    if not cardbs.find('div', {'class': 'bnfDtList'}) and not cardbs.find('ul', {'class': 'toggleList'}):
        return "존재하지 않는 카드입니다"
    
    # benefits
    benes = cardbs.findAll('div',{'class','bnfCont'})
    if len(benes) == 0:
        beneLists = cardbs.find('ul',{'class','toggleList'}).findAll('li',recursive=False)
        for beneList in beneLists:
            titlebene = beneList.find('a').text.replace('\t','').replace('\r','').replace('\n','').replace(' ','')
            if titlebene=="L.POINT" or titlebene=="가족카드" or titlebene== "가족카드안내" or titlebene== "연회비": continue
            benefits+="<"+titlebene+"> "
            details = beneList.find('div',{'class','toggleCont'}).findAll(recursive=False)
            for detail in details:
                if str(detail)[1:6]=="table": 
                    benefits+=str(detail).replace('\n','')
                elif str(detail)[1:3]=="h3": 
                    benefits+="["+detail.text+"]"
                elif str(detail)[1:3]=="h4": 
                    benefits+="/"+detail.text+": "
                elif str(detail)[1:6]=="style": 
                    continue
                else:
                    benefits+=detail.text.replace("\n","").replace('\r','').replace('\t','')
            benefits.replace('\n','').replace('\r','').replace('\t','')
            benefits+="\n"
    else:
        for bene in benes:
            titlebene=bene.find('h3').text
            if titlebene=="L.POINT" or titlebene=="가족카드" or titlebene== "가족카드 안내" or titlebene== "연회비" or titlebene== "혜택 모아보기": continue
            benefits+="<"+titlebene+">"
            sections = bene.findAll('div',{'class','toggle'})
            for section in sections:
                beneNames=section.find('h4')
                beneNameText=beneNames.text
                benefits+="["+beneNameText+"] "
                details = section.find('div',{'class','toggleCont'}).findAll(recursive=False)

                for detail in details:
                    if str(detail)[1:6]=="table": 
                        benefits+=str(detail).replace('\n','')
                    elif str(detail)[1:3]=="h3": 
                        benefits+="["+detail.text+"]"
                    elif str(detail)[1:3]=="h4": 
                        benefits+="/"+detail.text+": "
                    elif str(detail)[1:6]=="style": 
                        continue
                    else:
                        benefits+=detail.text.replace("\n","").replace('\r','').replace('\t','')
                benefits.replace('\n','').replace('\r','').replace('\t','')
            benefits+="\n"
            benefits=benefits.replace("'","")
            
    return benefits 



'''
    체크 카드 리스트 조회
    lotte_creditcardInfos.csv : card_name, card_url, card_img
'''

card_names = []
card_codes = []
card_urls = []
card_imgs = []


cardList(False)
cardList(True)

print("CSV 파일 생성 중...")

data = list(zip(card_names, card_codes, card_urls, card_imgs))
df = pd.DataFrame(data, columns=['card_name', 'card_code', 'card_url', 'card_img'])

df.to_csv("./lotte_debitcardInfos.csv", encoding = "utf-8-sig")

print("lotte_debitcardInfos.csv가 생성되었습니다.")


'''
    신용 카드 혜택 크롤링
    credit_benefit.csv : card_company_id, name, img_url, benefits, created_at, type
'''

card_infos = pd.read_csv('./lotte_debitcardInfos.csv')

card_urls = card_infos['card_url'].tolist()
name = card_infos['card_name'].tolist()
img_url = card_infos['card_img'].tolist()

card_company_id = [5] * len(card_urls)
benefits = []

created_at = []
type = ["DebitCard"] * len(card_urls)

print("======= [롯데] 전체 카드 혜택 정보 크롤링 (전체) =======")
for i in range(len(card_urls)):

    chrome_options = Options()

    # Chrome 설치된 경로로 변경
    chrome_options.binary_location = chrome_path  
        
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-web-security')

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

    driver.implicitly_wait(20)
    now = datetime.now()
    created_at.append(now)
    print(f"{now} [{card_names[i]}] --- 웹 페이지에 접속 중... ({i+1}/{len(card_urls)})")

    driver.get(card_urls[i])
    time.sleep(3)

    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')

    # 상세 혜택
    benefit = cardCrawling(card_urls[i])
    benefits.append(benefit)

print("CSV 파일 생성 중...")

data = {"card_company_id":card_company_id, "name" : name, "img_url" : img_url, "benefits": benefits, "created_at": created_at,"type":type}
df = pd.DataFrame(data)

df.to_csv("./Lotte/debit_benefit.csv", encoding = "utf-8-sig", index=False)
print("debit_benefit.csv가 생성되었습니다.")






'''    popup_containers = soup.find_all('div', class_='modal_pop')

    benefit_title = []
    benefit = ''

    for i in range(len(popup_containers)):
        title = popup_containers[i].find('div', class_='layer_head')
        if title and (title.text.strip()[-2:] == "적립" or title.text.strip()[-2:] == "사용"
                      or title.text.strip()[-2:] == "할인" or title.text.strip()[-5:] == "업그레이드"
                      or title.text.strip()[-3:] == "보너스" or title.text.strip()[-3:] == "서비스"
                      or title.text.strip()[-3:] == "트래블" or title.text.strip()[-3:] == "리워드"
                      or title.text.strip()[-2:] == "절감"  or title.text.strip()[-2:] == "지원"):
            benefit += f'###{title.text.strip()}'
            item_list = popup_containers[i].find('div', class_='layer_body')
            benefit += item_list.text.strip()

    benefits.append(benefit)

print("작업을 완료했습니다.")
driver.quit()


    신용 카드 혜택 크롤링
    credit_benefit.csv : card_company_id, name, img_url, benefits, created_at, type

data = {"card_company_id": card_company_id, "name": name, "img_url": img_url, "benefits" : benefits, "created_at": created_at, "type": type}
df = pd.DataFrame(data)

df.to_csv("./credit_benefit.csv", encoding = "utf-8-sig", index=False)
'''