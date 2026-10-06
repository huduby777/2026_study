# Ctrl + Shift + P → Developer: Reload Window 실행
import requests
import streamlit as st
from datetime import datetime
import pandas as pd
import math

import json
import serial
import time
from threading import Lock

st.set_page_config(page_title="버스 정류소 UI")
st.header("📢 범박동 행정복지센터",text_alignment="center")
# 요청에 필요한 값
params = {
    "serviceKey": st.secrets["TAGO"]["API_KEY"],
    "cityCode": st.secrets["TAGO"]["CITY_CODE"],
    "nodeId": st.secrets["TAGO"]["NODE_ID"],
    "_type": "json",
    "pageNo": 1,
    "numOfRows": 100,
}

# Streamlit이 재실행되어도 연결을 재사용
@st.cache_resource # 디버깅할 동안만
def connect_arduino():
    connection = serial.Serial(
        port="COM3",
        baudrate=9600,
        timeout=1,
        write_timeout=1
    )
    time.sleep(2)
    connection.reset_input_buffer()
    return connection, Lock()

if 'font_mode' not in st.session_state:
    st.session_state['font_mode'] = "small"

flag = 0
def send_arduino(df):
    global flag
    try:
        arduino, serial_lock = connect_arduino()
    except serial.SerialException as er:
        st.error(f"아두이노 연결 실패: {er}")
        st.stop()

    # TOP 2개만 아두이노에 전송 .
    bus_list = df[["routeno","arrtime","arrprevstationcnt"]].head(2)
    bus_list["routeno"] = bus_list["routeno"].replace("부천똑버스","DDOK")
    bus_list_dict = bus_list.to_dict(orient="records")

    msg = json.dumps(bus_list_dict, ensure_ascii=False) + "\n"
    with serial_lock:
        arduino.write(msg.encode("utf-8"))
        # while True:
        # reply = arduino.readline().decode("utf-8", errors="replace").strip()
        # print(reply)
        st.write("전송완료")
        # arduino.flush()  # 전송 버퍼의 데이터가 전송될 때까지 기다림
        # arduino.close()  # 디버깅할 동안만     
        # st.write("포트닫기")
        # flag = 1
    

def btn_list():
    font, voice  = st.columns([1,1])
    if st.session_state["font_mode"] == "small":
        if font.button(
            "🔎 큰 글자모드",
            key="font_bigger",
            type="primary",
            use_container_width=True,
        ):
            st.session_state["font_mode"] = "big"
            st.rerun()
    else:
        if font.button(
            "🔎 작은 글자모드",
            key="font_small",
            type="primary",
            use_container_width=True,
        ):
            st.session_state["font_mode"] = "small"
            st.rerun()
    voice.button(
        "🔊 음성 안내",
        key="list_voice",
        type="primary",
        use_container_width=True,
    )
    # phone.button(
    #     "📲 휴대폰 안내 QR",
    #     key="phone_qr",
    #     type="primary",
    #     use_container_width=True,
    # )

@st.fragment(run_every="30s")
def bus_list():
    try:
        # API 요청
        response = requests.get(st.secrets["TAGO"]["URL"], params=params, timeout=10)
        # HTTP 오류 확인
        response.raise_for_status()
    except requests.exceptions.RequestException:
        st.error(f"Requests 오류 : [{response.status_code}]")
    else:
        # JSON 응답을 파이썬 딕셔너리로 변환
        data = response.json()
        # 응답 확인
        result = data["response"]
        # print(result["body"]["totalCount"])

        # print("body 값:", result["body"])
        # print("body 자료형:", type(result["body"]).__name__)

        if isinstance(result["body"], str):
            df = pd.DataFrame()
        else:
            items = result["body"].get("items")
            item = items.get("item")

            if isinstance(item, dict): # 데이터가 1개인 경우
                item = [item] # 시리즈 -> [] 해서 dataframe형태로 바꿀 수 있도록
            
            df = pd.DataFrame(item)
            
        if df.empty:
            st.info("버스 정보가 없습니다.")
        else:
            df["arrtime"] = pd.to_numeric(df["arrtime"], errors="coerce")
            df = df.dropna(subset=["arrtime"]).reset_index(drop=True)
            df["vehicle"] = df["vehicletp"].fillna("")
            result = df.loc[df.groupby("routeno")["arrtime"].idxmin()].sort_values(by="arrtime").reset_index(drop=True)

            # print(result)
            # 아두이노에 데이터 전송
            if flag == 0:
                send_arduino(result)

            arrival_soon = ""
            with st.container(height=300, border=True):
                title, status = st.columns([3, 1])
                title.write("부천범박힐스테이트 3.4단지 방향")
                status.caption(f"갱신 시각 {datetime.now():%H:%M:%S}")
                for idx in range(len(result)):
                    buses = result.loc[idx]
                    arrtime = buses["arrtime"]
                    vehicle = buses["vehicletp"].strip()

                    color = "primary"
                    bg_color = "#252830"
                    font_color = "#A5A6A9"
                    if vehicle == "":
                        color = "yellow"
                        vehicle = "차량유형 확인 불가"
                        bg_color = "#3E2912"
                        font_color = "#FFBD45"
                    elif vehicle == "저상버스":
                        color = "violet"
                        bg_color = "#B27EFF"
                        font_color = "#2A2145"
                    elif vehicle == "일반버스":
                        color = "blue"
                        bg_color = "#172D43"
                        font_color = "#3D9DF3"

                    if arrtime <= 120:
                        arrival_soon += str(buses['routeno']) + "번&nbsp;&nbsp;"

                    if st.session_state["font_mode"] == "small":
                        if idx % 2 == 0:
                            columns = st.columns(2)

                        with columns[idx % 2]:
                            with st.container(border=True):
                                cols = st.columns([1.5,1.5,1])
                                cols[0].write(f"{ buses['routeno']}번")
                                cols[1].badge(label=vehicle,color=color)
                                cols[2].text(f"약 { math.ceil(float(arrtime) / 60) }분")
                    else:
                        with st.container(border=True):
                            str_html = f"""<table style="width:100%;text-align:center;border:none;border-collapse:collapse;">
            <tr style="border:none;">
                <td style="width:33.3%; padding:20px; font-size:40px; font-weight:bold;border:none;">{buses['routeno']}번</td>
                <td style="width:33.3%; padding:20px;border:none;">
                    <span style="
                        color:{font_color};
                        background-color:{bg_color};
                        font-size:35px;
                        font-weight:bold;
                        padding:2px 6px;border:none;">{vehicle}</span>
                </td>
                <td style="width:33.3%; padding:20px; font-size:40px; font-weight:bold;border:none;">
                    약 { math.ceil(float(arrtime) / 60) }분
                </td>
            </tr>
        </table>
        """
                            st.markdown(str_html, unsafe_allow_html=True)
            st.error(f"#### 곧 도착&nbsp;:&nbsp;&nbsp;{arrival_soon}")
        btn_list()
bus_list()