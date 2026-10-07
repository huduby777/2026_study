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

from gtts import gTTS
from io import BytesIO

import lib.init as init

st.set_page_config(page_title="버스 정류소 UI", layout="centered")

st.header("📢 범박동 행정복지센터",text_alignment="center")
st.markdown(init.html_css, unsafe_allow_html=True)

if 'font_mode' not in st.session_state:
    st.session_state['font_mode'] = "small"

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

def send_arduino(df):
    try:
        arduino, serial_lock = connect_arduino()
    except serial.SerialException as er:
        st.error(f"아두이노 연결 실패: {er}")
        st.stop()

    # TOP 2개만 아두이노에 전송 .
    bus_list = df[["routeno","arrtime","arrprevstationcnt"]].head(2)
    bus_list["routeno"] = bus_list["routeno"].str.replace("부천똑버스","DDOK")
    bus_list_dict = bus_list.to_dict(orient="records")

    msg = json.dumps(bus_list_dict, ensure_ascii=False) + "\n"
    try:
        with serial_lock:
            arduino.write(msg.encode("utf-8"))
            st.write("전송완료")
        # arduino.flush()  # 전송 버퍼의 데이터가 전송될 때까지 기다림
        # arduino.close()  # 디버깅할 동안만     
        # st.write("포트닫기")
        # flag = 1
    except serial.SerialException as er:
        with serial_lock:
            try:
                arduino.close()
            except serial.SerialException:
                pass
        connect_arduino.clear()
        st.error("전송 실패: {er}")
        st.info("USB연결과 COM포트를 확인해 주세요.")

# 음성안내
def voice_guide(txt):
    if txt == "":
        txt = "곧 도착하는 버스가 없습니다."
    else:
        txt = txt.str.replace("-","다시")
        txt += " 버스가 곧 도착합니다."

    audio = BytesIO()
    gTTS(text=txt, lang="ko").write_to_fp(audio)
    st.audio(
        audio.getvalue(),
        format="audio/mp3",
        autoplay=True,
    )    

# 버튼 목록
def btn_list(voice_txt):
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
    if voice.button(
        "🔊 음성 안내",
        key="list_voice",
        type="primary",
        use_container_width=True,
    ):
        voice_guide(voice_txt)

# 30초 마다 재실행
@st.fragment(run_every="30s")
def bus_list():
    try:
        # API 요청
        response = requests.get(st.secrets["TAGO"]["URL"], params=init.params, timeout=10)
        # HTTP 오류 확인
        response.raise_for_status()
    except requests.exceptions.RequestException:
        st.error(f"Requests 오류")
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
            df["routeno"] = df["routeno"].str.replace("부천똑버스","DDOK")
            
            result = df.loc[df.groupby("routeno")["arrtime"].idxmin()].sort_values(by="arrtime").reset_index(drop=True)

            # print(result)
            send_arduino(result)

            arrival_soon = ""
            voice_txt = ""
            with st.container(height=300,border=True):
                title, status = st.columns([3, 1])
                title.subheader("🚎 부천범박힐스테이트 3.4단지 방향")
                status.text(f"갱신 시각 {datetime.now():%H:%M:%S}")
                for idx in range(len(result)):
                    buses = result.loc[idx]
                    arrtime = buses["arrtime"]
                    vehicle = buses["vehicletp"].strip()

                    emoji = " "
                    if vehicle == "저상버스":
                        emoji = "👨‍🦽"
                    
                    if arrtime <= 120:
                        arrival_soon += str(buses['routeno']) + "번&nbsp;&nbsp;"
                        voice_txt += str(buses['routeno']) + "번 "
     
                    if st.session_state["font_mode"] == "small":
                        if idx % 2 == 0:
                            columns = st.columns(2)
                        with columns[idx % 2]:
                            with st.container():
                                st.markdown(f"""<div class='bus-board' style="text-align:center">
                                <span class="smallsize" style="text-align:right">{emoji}</span>
                                <span class="smallsize">{buses['routeno']}</span>
                                <span class="smallsize">{buses['arrprevstationcnt']}전</span>
                                <span class="smallsize">{math.ceil(float(arrtime) / 60)}분 후 도착</span>""", unsafe_allow_html=True)        
                    else:
                        with st.container():
                            st.markdown(f"""<div class='bus-board' style="text-align:center">
                            <span class="bigsize" style="text-align:right">{emoji}</span>
                            <span class="bigsize">{buses['routeno']}</span>
                            <span class="bigsize">{buses['arrprevstationcnt']}전</span>
                            <span class="bigsize">{math.ceil(float(arrtime) / 60)}분 후 도착</span>""", unsafe_allow_html=True)  
                    st.markdown("</div>",unsafe_allow_html=True)        
            st.error(f"#### 곧 도착&nbsp;:&nbsp;&nbsp;{arrival_soon}")
        btn_list(voice_txt)
bus_list()