import json
from copy import deepcopy

import pandas as pd
import requests


def parse_amount(val):
    try:
        return float(val)
    except:
        return 0.0


def estimate_from_percent(percent, base_amount=5533):
    try:
        return base_amount * (float(percent) / 100.0)
    except:
        return 0.0


# Kakao API 세팅
url = "https://dapi.kakao.com/v2/local/search/keyword.json"
headers = {
    "Authorization": "KakaoAK API-KEY"
}

# CSV 파일 불러오기
df = pd.read_csv('credit_benefit_json.csv')

# 카드내역.xlsx 파일 불러오기
card_history_df = pd.read_csv('카드내역.csv')

target_card_names = [
    "#MY WAY(샵 마이웨이) 카드",
    "하나멤버스 1Q(원큐) 카드 ALL in",
    "JADE Classic",
    "하나증권 캐시백 투자 카드"
]

# 1. 카드별 카페 '대상' 수집 및 카드별 혜택도 같이 저장
cafe_targets_set = set()
card_cafe_benefits = {}  # 카드명 -> 대상 리스트, 혜택

for idx, row in df.iterrows():
    if row['name'] in target_card_names:
        try:
            benefits = json.loads(row['benefits'])
            cafe_info = benefits.get("카페", {})
            targets = cafe_info.get("대상", [])
            혜택 = cafe_info.get("혜택", {})

            print(f"[{row['name']}] 카페 대상: {targets}")
            card_cafe_benefits[row['name']] = {
                "대상": targets,
                "혜택": deepcopy(혜택)  # 원본 보호를 위해 깊은 복사
            }
            cafe_targets_set.update(targets)
        except Exception as e:
            print(f"Error processing {row['name']}: {e}")

# 중복 없는 카페 리스트
cafe_targets_list = list(cafe_targets_set)
print(f"중복 제거된 카페 리스트: {cafe_targets_list}")

# 카페명별 언급 횟수 계산 (부분 일치)
cafe_mention_counts = {cafe: 0 for cafe in cafe_targets_list}
for cafe in cafe_targets_list:
    # 상호명에서 해당 카페명이 포함된 경우 카운트
    cafe_mention_counts[cafe] = card_history_df['내역'].str.contains(cafe, case=False, na=False).sum()

print("카페명별 언급 횟수:", cafe_mention_counts)

# 2. 각 카페 브랜드별로 장소 검색 후 결과 저장
x_coord = "126.94"
y_coord = "37.55"

results = []

for cafe in cafe_targets_list:
    params = {
        "query": cafe,
        "x": x_coord,
        "y": y_coord,
        "radius": 1000,
        "size": 5
    }
    response = requests.get(url, headers=headers, params=params)
    if response.status_code != 200:
        print(f"{cafe} 검색 실패: {response.status_code}")
        continue

    places = response.json().get("documents", [])

    for place in places:
        place_info = {
            "place_name": place.get("place_name"),
            "road_address_name": place.get("road_address_name"),
            "x": place.get("x"),
            "y": place.get("y"),
            "카페명": cafe,
            "거리": int(place.get("distance", "0")),  # 문자열을 정수로 변환
            "카드별_혜택": {}
        }

        # 3. 이 place의 카페명으로 어떤 카드에서 혜택 있는지 확인 후 혜택 첨부
        for card_name, info in card_cafe_benefits.items():
            if cafe in info["대상"]:
                place_info["카드별_혜택"][card_name] = deepcopy(info["혜택"])  # 깊은 복사
        results.append(place_info)

# 4. 각 매장의 최고 혜택 스코어 추출하여 저장
for place in results:
    max_score = 0.0
    거리 = place["거리"]
    카페명 = place["카페명"]
    # 카페명 언급 횟수 가져오기 (없으면 0)
    mention_count = cafe_mention_counts.get(카페명, 0)
    plus = mention_count * 100
    print(f"\n{place['place_name']} (거리: {거리}m, 카페명: {카페명}, 언급 횟수: {mention_count}, 가산점: {plus})")

    for card_name, 혜택 in place["카드별_혜택"].items():
        total_discount = 0.0
        total_point = 0.0
        total_cashback = 0.0

        # 할인 계산
        할인목록 = 혜택.get("할인", [])
        if isinstance(할인목록, list):
            for 할인 in 할인목록:
                if 할인.get("금액(원)") is not None:
                    total_discount += parse_amount(할인.get("금액(원)"))
                elif 할인.get("할인율(%)") is not None:
                    total_discount += estimate_from_percent(할인.get("할인율(%)"))

        # 적립 계산
        적립 = 혜택.get("적립", {})
        if 적립:
            if 적립.get("금액(원)") is not None:
                total_point += parse_amount(적립.get("금액(원)"))
            elif 적립.get("적립율(%)") is not None:
                total_point += estimate_from_percent(적립.get("적립율(%)"))

        # 캐시백 계산
        캐시백 = 혜택.get("캐시백", {})
        if 캐시백:
            if 캐시백.get("금액(원)") is not None:
                total_cashback += parse_amount(캐시백.get("금액(원)"))
            elif 캐시백.get("캐시백 비율(%)") is not None:
                total_cashback += estimate_from_percent(캐시백.get("캐시백 비율(%)"))

        # 혜택 스코어 계산
        raw_score = 1.0 * total_discount + 0.7 * total_point + 1.5 * total_cashback
        score = (raw_score - 거리) + plus  # 언급 횟수 반영
        print(f"[{card_name}] Raw Score: {raw_score}, 거리: {거리}, 가산점: {plus}, 최종 Score: {score}")

        # 결과 저장
        place["카드별_혜택"][card_name]["혜택스코어"] = round(score, 2)

        # 최고 혜택 스코어 갱신
        max_score = max(max_score, score)

    place["최고혜택스코어"] = round(max_score, 2)

# 5. 스코어 기준으로 정렬 (높은 순)
results = sorted(results, key=lambda x: x["최고혜택스코어"], reverse=True)

# 6. 정렬된 결과 출력
print("\n최종 결과:")
print(json.dumps(results, indent=2, ensure_ascii=False))
