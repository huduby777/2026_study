import requests
import streamlit as st

# 도시코드 읽어오기
# https://apis.data.go.kr/1613000/ArvlInfoInqireService/getCtyCodeList?serviceKey=...&_type=json

# 1. API 요청 주소
url = "https://apis.data.go.kr/1613000/ArvlInfoInqireService/getSttnAcctoArvlPrearngeInfoList"

# 2. 요청에 필요한 값
params = {
    "serviceKey": st.secrets["TAGO"]["API_KEY"],
    "cityCode": st.secrets["TAGO"]["CITY_CODE"],
    "nodeId": st.secrets["TAGO"]["NODE_ID"],
    "_type": "json",
    "pageNo": 1,
    "numOfRows": 100,
}

# 3. API 요청
response = requests.get(url, params=params, timeout=10)
# 4. HTTP 오류 확인
response.raise_for_status()

# 5. JSON 응답을 파이썬 딕셔너리로 변환
data = response.json()

# 6. 응답 확인
st.write(data["response"])