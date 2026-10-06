"""실행: streamlit run bus_ui.py
Streamlit 기본 위젯 + 색상/크기 조정용 CSS로 구성한 두 화면.
API, Arduino, 실제 음성, QR 생성은 아직 연결하지 않은 UI 예제입니다.
"""
import streamlit as st

st.set_page_config(page_title="스마트 버스 정류소", page_icon="🚌", layout="centered")

# TAGO 연결 시 이 목록을 API 응답에서 만든 데이터로 교체하세요.
# routeid로 선택 상태를 보관하며, routeno는 화면 표시용입니다.
BUSES = [
    {"routeid": "demo_12", "routeno": "12", "arrtime": 300,
     "arrprevstationcnt": 3, "vehicletp": "저상버스"},
    {"routeid": "demo_34", "routeno": "34", "arrtime": 480,
     "arrprevstationcnt": 5, "vehicletp": None},
]
STATION_NAME = "우리동네 정류소"
DIRECTION = "시청 방향"

# 레이아웃과 상호작용은 Streamlit. CSS는 기본 위젯의 외형만 조정합니다.
st.markdown("""
<style>
.stApp {background: #ffffff; color: #111827;}
.st-key-stop_panel {border: 5px solid #20272c !important;
    border-radius: 14px !important; padding: 18px !important;}
.st-key-stop_header {background: #e8eef4; border-radius: 5px; padding: 6px 12px;}
.st-key-stop_header p {margin: 0; color: #172334;}
.st-key-arrival_box {background: #e4f2ff; border-radius: 12px; padding: 20px 12px;}
.st-key-arrival_box h1, .st-key-arrival_box h3,
.st-key-arrival_box p {text-align: center; color: #102d61;}
.st-key-route_0 button, .st-key-route_1 button {
    min-height: 90px; border: 2px solid #c6d1df; border-radius: 10px;
    background: white; color: #111827;}
.st-key-route_0 button:hover, .st-key-route_1 button:hover {
    background: #e4f2ff; border-color: #102d61; color: #102d61;}
.st-key-route_0 button p, .st-key-route_1 button p {font-size: 24px;}
button[kind="primary"] {background: #102d61; border-color: #102d61; color: white;}
.st-key-clear_selection button {border: 2px solid #102d61; color: #102d61;}
.stButton button {min-height: 50px; border-radius: 8px;}
.stButton button p {font-weight: 700;}
</style>
""", unsafe_allow_html=True)

if "selected_route_id" not in st.session_state:
    st.session_state.selected_route_id = None
if "voice_message" not in st.session_state:
    st.session_state.voice_message = ""


def select_bus(route_id):
    st.session_state.selected_route_id = route_id
    st.session_state.voice_message = ""


def clear_selection():
    st.session_state.selected_route_id = None
    st.session_state.voice_message = ""


def minutes(bus):
    return (bus["arrtime"] + 59) // 60


def vehicle_label(bus):
    return bus["vehicletp"] or "차량유형 확인 불가"


def request_voice():
    """실제 PC 음성 재생을 연결할 위치. 현재는 안내 문장만 표시합니다."""
    selected = next((b for b in BUSES
                     if b["routeid"] == st.session_state.selected_route_id), None)
    targets = [selected] if selected else BUSES
    st.session_state.voice_message = " ".join(
        f"{b['routeno']}번 버스가 약 {minutes(b)}분 후 도착 예정입니다. "
        f"{vehicle_label(b)}."
        for b in targets
    )


selected = next((b for b in BUSES
                 if b["routeid"] == st.session_state.selected_route_id), None)

with st.container(border=True, key="stop_panel"):
    with st.container(key="stop_header"):
        title_col, status_col = st.columns([4, 1])
        title_col.markdown(f"**{STATION_NAME} · {DIRECTION}**")
        status_col.caption("예시 데이터")

    if selected is None:
        # 화면 1: 목록. 각 카드 전체가 실제 Streamlit 버튼입니다.
        for index, bus in enumerate(BUSES):
            with st.container(key=f"route_{index}"):
                st.button(
                    f"{bus['routeno']}번　 |　 약 {minutes(bus)}분　 ·　 {vehicle_label(bus)}",
                    key=f"select_{bus['routeid']}",
                    use_container_width=True,
                    on_click=select_bus,
                    args=(bus["routeid"],),
                )
        voice_col, phone_col = st.columns([3, 2])
        with voice_col:
            st.button("🔊 음성 안내", key="voice_list", type="primary",
                      use_container_width=True, on_click=request_voice)
        with phone_col:
            # 실제 접속 주소를 정한 뒤 QR 이미지를 st.image로 배치할 자리입니다.
            st.caption("휴대폰 안내 QR")
            st.caption("접속 주소 설정 후 추가")
    else:
        # 화면 2: 관심버스. session_state에 저장한 노선 ID로 선택합니다.
        st.markdown(f"### 관심버스 :blue[{selected['routeno']}번]")
        with st.container(key="arrival_box"):
            st.markdown(f"# 약 {minutes(selected)}분 후 도착 예정")
            st.markdown(
                f"**남은 정류장 {selected['arrprevstationcnt']}개 · "
                f"{vehicle_label(selected)}**"
            )
        clear_col, voice_col = st.columns(2)
        with clear_col:
            with st.container(key="clear_selection"):
                st.button("선택 해제", key="clear", use_container_width=True,
                          on_click=clear_selection)
        with voice_col:
            st.button("🔊 음성 안내", key="voice_detail", type="primary",
                      use_container_width=True, on_click=request_voice)

    if st.session_state.voice_message:
        st.info("안내 문장 미리보기: " + st.session_state.voice_message)

st.caption("UI 시연용 · 실제 API 조회와 음성 재생은 연결 전입니다.")
