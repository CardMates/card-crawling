import time

import pandas as pd
import requests

# 1. 카드 내역 불러오기
card_history_df = pd.read_csv('카드내역2.csv')

# 2. 카카오 API 설정
headers = {"Authorization": "KakaoAK API-KEY"}
url = "https://dapi.kakao.com/v2/local/search/keyword.json"

# 3. 카테고리 코드 매핑
category_map = {
    "MT1": "대형마트", "CS2": "편의점", "PS3": "어린이집, 유치원", "SC4": "학교",
    "AC5": "학원", "PK6": "주차장", "OL7": "주유소, 충전소", "SW8": "지하철역",
    "BK9": "은행", "CT1": "문화시설", "AG2": "중개업소", "PO3": "공공기관",
    "AT4": "관광명소", "AD5": "숙박", "FD6": "음식점", "CE7": "카페",
    "HP8": "병원", "PM9": "약국"
}

# 4. 카테고리별 누적 정보 저장용 dict
category_stats = {}

# 5. 검색 및 수집
for idx, row in card_history_df.iterrows():
    store_name = row['가맹점명']
    try:
        amount = int(str(row['승인금액']).replace(",", "").replace("원", "").strip())
    except:
        amount = 0

    store_name = store_name.replace("( 주 )", "").replace("주식회사", "")
    params = {"query": store_name}

    try:
        response = requests.get(url, headers=headers, params=params)
        data = response.json()

        print(f"\n[{idx}] 가맹점명: {store_name} | 승인금액: {amount}원")
        if data.get("documents"):
            doc = data["documents"][0]
            category_code = doc.get("category_group_code", "")
            category_name = category_map.get(category_code, "기타")

            print(f"  • 이름: {doc['place_name']}")
            print(f"    카테고리: {category_name} ({category_code})")
            print(f"    ----------------------")

            if category_name not in category_stats:
                category_stats[category_name] = {"total_amount": 0, "count": 0}
            category_stats[category_name]["total_amount"] += amount
            category_stats[category_name]["count"] += 1
        else:
            print("  → 검색 결과 없음")

        time.sleep(0.3)

    except Exception as e:
        print(f"  오류 발생: {e}")

# 6. 카테고리별 총합과 평균 출력
print("\n카테고리별 총합 및 평균 금액:")
for category, stats in category_stats.items():
    total = stats["total_amount"]
    count = stats["count"]
    avg = total / count if count else 0
    print(f"  - {category}: 총 {total:,}원 / {count}회 / 평균 {avg:,.0f}원")
