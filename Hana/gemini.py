import google.generativeai as genai
import pandas as pd

genai.configure(api_key="API-KEY")

model = genai.GenerativeModel('gemini-2.0-flash')

csv_path = "credit_benefit.csv"

df = pd.read_csv(csv_path)

updated_benefits = []

for _, card in df.iterrows():
    benefit_text = card["benefits"]

    prompt = (
        f"{benefit_text}\n\n"
        "주유, 마트, 편의점, 교육, 영화, 쇼핑, 여행, 카페, 약국/병원, 식당, 놀이공원 카테고리만 있는데 "
        "이 카테고리들에 해당하는 혜택들만 모아서 보고싶어"
        "아래 내용을 이 카테고리에 맞춰서 카테고리 안에 대상, 혜택, 조건, 한도 만으로 정리하는데"
        "주어진 카테고리와 주어진 대상, 혜택, 조건, 한도만 찾아야해"
        "할인, 적립, 캐시백이 여러개라면 그 안에"
        "대상은 장소 상호명으로 string list형태로 출력하고"
        "할인, 적립, 캐시백이 여러개라면 그 안에 배열로 알려주고"
        "혜택에는 금액 또는 할인율을 숫자 또는 null로 알려주고 둘 중 하나는 꼭 알려줘"
        "조건과 한도는 string 형태로 알려줘"
        """
        {
    "주유":{
        "대상":["SK에너지","GS칼텍스","현대오일뱅크"],
        "혜택":{
            "할인":[
                {
                "금액(원)":1000,
                "할인율(%)":null,
                "조건":"10,000원 이상 구매시",
                "한도":"최대 1000원 할인"
                },
                {
                "금액(원)":3000,
                "할인율(%)":null,
                "조건":"지난달 실적 30만원 이상 시 우대 10,000원 이상 구매시",
                "한도":"최대 3000원 할인"
                },
            ]
            "적립":{
                "포인트명":"하나머니",
                "금액(원)":null,
                "적립율(%)":5,
                "조건":"지난달 실적 30만원 이상 시",
                "한도": "통합 월 최대 2만 하나머니"
            },
            "캐시백":{
                "금액(원)":null,
                "캐시백 비율(%)":5,
                "조건":"지난달 실적 30만원 이상 시",
                "한도": "통합 월 최대 10만원"
            }
        }
    },
    ...
}
        """
        "이게 예시인데 형식을 지켜서 JSON으로 출력해줘."
        "오로지 json 값만 출력해"
    )

    try:
        response = model.generate_content(prompt)
        json_response = response.text.strip().replace("```json", "").replace("```", "")
        updated_benefits.append(json_response)
        print(json_response)
    except Exception as e:
        print(f"Error processing card {card['name']}: {e}")
        updated_benefits.append("")

df["benefits"] = updated_benefits

output_path = "credit_benefit_json.csv"
df.to_csv(output_path, index=False)

print("변환된 CSV 저장 완료")
