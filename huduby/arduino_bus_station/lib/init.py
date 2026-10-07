import streamlit as st
html_css = """
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/galmuri/dist/galmuri.css">
<style>
.stMainBlockContainer {
max-width:1000px;
}
.bus-board {
font-family: 'Galmuri11 Condensed', sans-serif;
display: grid;
grid-template-columns: 0.5fr 1fr 0.7fr 2fr;
align-items: center;
color: #ffcc00;
text-shadow: 0 0 5px #ffcc0066;
}
.bus-board .smallsize {
color: #66ff66;
font-size: 30px;
text-shadow: 0 0 5px #66ff66;
}
.bus-board .bigsize {
font-size: 60px;
color: #66ff66;
text-shadow: 0 0 5px #66ff66;
}
</style>
"""
# 요청에 필요한 값
params = {
    "serviceKey": st.secrets["TAGO"]["API_KEY"],
    "cityCode": st.secrets["TAGO"]["CITY_CODE"],
    "nodeId": st.secrets["TAGO"]["NODE_ID"],
    "_type": "json",
    "pageNo": 1,
    "numOfRows": 100,
}