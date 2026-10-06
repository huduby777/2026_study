# OpenAPI 사용 방법 — TAGO 버스도착정보

> 상세 기술 문서의 기존 「OpenAPI 사용 방법」 부분을 아래 내용으로 교체한다. 조회 주기, 내부 필드명, 오류 대응은 프로젝트용 권장안이며 아직 확정되지 않았다.

## 1. 사용할 API와 준비 사항

- **서비스:** 국토교통부_(TAGO)_버스도착정보
- **공식 안내:** https://www.data.go.kr/data/15098530/openapi.do
- **조회 기능:** 정류소별 도착예정정보 목록 조회

공공데이터포털에서 활용신청 후 인증키를 발급받는다. 서비스의 「도시코드 목록 조회」에서 대상 지역의 `cityCode`를 확인하고, 별도 「국토교통부_(TAGO)_버스정류소정보」에서 집 근처 정류소의 `nodeId`를 찾는다. 정류소 이름뿐 아니라 위치와 운행 방향도 확인한다. 표지판 번호를 `nodeId`로 그대로 사용하지 않는다.

대상 지역과 정류소의 실제 응답을 먼저 확인한다. 키를 발급받았다고 모든 정류소에 도착정보가 제공되는 것은 아니다. 지역·정류소는 아직 정하지 않았으므로 이 문서에 고정값을 넣지 않는다.

## 2. 요청 주소와 설정

```text
https://apis.data.go.kr/1613000/ArvlInfoInqireService/getSttnAcctoArvlPrearngeInfoList
```

| 요청 변수 | 설정 |
|---|---|
| `serviceKey` | 필수. 발급받은 인증키 |
| `cityCode` | 필수. 대상 도시코드 |
| `nodeId` | 필수. 대상 TAGO 정류소 ID |
| `_type` | `json` 지정 |
| `pageNo` | 조회할 페이지, 시작값 `1` |
| `numOfRows` | 페이지 크기, 프로젝트 제안값 `100` |

Python `requests`의 `params`에는 **Decoding 인증키**를 전달하여 URL 인코딩을 맡긴다. 이미 인코딩된 키를 다시 인코딩하지 않는다. 인증키는 환경변수로 관리하고 소스, 휴대폰 페이지, 로그에 노출하지 않는다.

프로젝트 환경변수:

```text
TAGO_API_KEY=발급받은_Decoding_인증키
TAGO_CITY_CODE=선택한_도시코드
TAGO_NODE_ID=선택한_정류소ID
```

실제 값은 각자 설정한다. 환경변수를 읽는 아래 예제는 `.env` 파일을 자동으로 불러오지는 않는다.

## 3. 응답과 내부 데이터 연결

정상 응답은 `response.header.resultCode`가 `00`인지 확인한다. 결과 목록은 `response.body.items.item`, 전체 건수는 `response.body.totalCount`에서 읽는다.

| TAGO 응답 항목 | 의미 | 프로젝트 내부 필드 제안 |
|---|---|---|
| `nodeid` | 정류소 ID | `station_id` |
| `nodenm` | 정류소명 | `station_name` |
| `routeid` | 노선 ID | `route_id` |
| `routeno` | 노선번호 | `route_name` |
| `routetp` | 노선유형 | `route_type` |
| `arrtime` | 도착예상시간, **초** | `eta_seconds` |
| `arrprevstationcnt` | 남은 정류장 수 | `remaining_stops` |
| `vehicletp` | 차량유형 | `vehicle_type` |

요청은 `nodeId`, 응답은 `nodeid`로 대소문자가 다르다. 노선번호와 ID는 문자열로 보관한다. 화면 표시용 분은 `(eta_seconds + 59) // 60`으로 올림하고, 원본 초 값도 유지한다. 예를 들어 125초는 화면에서 약 3분으로 표시한다.

`vehicletp`가 `저상버스`일 때 저상버스로 표시한다. 값이 없거나 해석할 수 없으면 「차량유형 확인 불가」로 처리한다. 저상버스 여부로 휠체어 탑승 가능 여부나 기사 지원을 보장하지 않는다.

**기존 API 예제와의 차이:** TAGO에서는 `predictTime1`, `lowPlate1`, `vehId1` 등을 사용하지 않는다. 이 기능의 공식 응답 목록에는 차량 ID가 없으므로 내부 `vehicle_id`는 `None`으로 둔다. 동일 차량 추적과 차량 ID 기반 중복 알림은 이 API만으로 구현할 수 없다. 대체 알림 기준은 추후 별도 결정한다.

## 4. Python 조회 예제

설치: `pip install requests`

아래는 모든 페이지를 조회해 원본 항목 목록을 반환하는 최소 예제다. 실제 인증키로 실행 검증한 코드는 아니며, 대상 정류소를 정한 후 응답을 확인해야 한다.

```python
import os
import requests

URL = (
    "https://apis.data.go.kr/1613000/ArvlInfoInqireService/"
    "getSttnAcctoArvlPrearngeInfoList"
)


def fetch_arrivals():
    params = {
        "serviceKey": os.environ["TAGO_API_KEY"],
        "cityCode": os.environ["TAGO_CITY_CODE"],
        "nodeId": os.environ["TAGO_NODE_ID"],
        "_type": "json",
        "numOfRows": 100,
        "pageNo": 1,
    }
    rows = []
    with requests.Session() as session:
        while True:
            try:
                response = session.get(URL, params=params, timeout=(3, 10))
                response.raise_for_status()
            except requests.RequestException:
                # 원본 예외/요청 URL에는 인증키가 포함될 수 있다.
                raise RuntimeError("TAGO 연결 또는 HTTP 오류") from None
            try:
                payload = response.json()["response"]
                header = payload["header"]
                code = str(header["resultCode"]).zfill(2)
                if code != "00":
                    raise RuntimeError(f"TAGO 서비스 오류 코드: {code}")
                body = payload["body"]
                total = int(body["totalCount"])
                size = int(body["numOfRows"])
                container = body.get("items")
                if container in (None, ""):
                    items = []
                elif isinstance(container, dict):
                    items = container.get("item", [])
                else:
                    raise ValueError("잘못된 items 형식")
                if items in (None, ""):
                    items = []
                if isinstance(items, dict):
                    items = [items]
                if not isinstance(items, list) or not all(
                    isinstance(item, dict) for item in items
                ):
                    raise ValueError("잘못된 item 형식")
            except (ValueError, KeyError, TypeError):
                # JSON을 요청해도 XML 오류 응답 등이 올 수 있다.
                raise RuntimeError("TAGO 응답 형식 오류") from None
            rows.extend(items)
            if size <= 0:
                raise RuntimeError("TAGO 페이지 크기 오류")
            if params["pageNo"] * size >= total:
                return rows
            if not items:
                raise RuntimeError("TAGO 페이지 결과 누락")
            params["pageNo"] += 1
```

정상적으로 `[]`가 반환되면 「현재 제공되는 도착정보 없음」으로 처리한다. 예외가 발생하면 「정보 갱신 실패」로 구분한다. 결과가 없다는 이유만으로 운행 종료라고 단정하지 않는다.

수신 항목을 내부 데이터로 변환할 때 숫자 필드의 누락·변환 실패·음수는 `None`으로 처리한다. 잘못된 값을 0초로 바꾸면 도착임박 알림이 잘못 발생할 수 있다. 정상 항목과 오류 항목을 분리해 처리하고, 조회 시각도 함께 저장한다.

## 5. 프로젝트 적용 권장안

| 항목 | 권장 처리 |
|---|---|
| 조회 주기 | 우선 30초 간격으로 시작하고 실제 응답과 허용량을 보고 조정 |
| 호출량 | 한 페이지를 24시간 조회하면 하루 2,880회. 추가 페이지·재시도는 별도 가산 |
| 관심버스 | 한 정류소의 조회 결과에서 선택한 `routeid`를 필터링 |
| 여러 도착정보 | 같은 노선의 항목을 유효한 `arrtime` 순으로 정렬. 항상 두 대가 온다고 가정하지 않음 |
| 도착임박 | 예: 120초 이하. 기준은 추후 확정하고 오래된 정보에는 적용하지 않음 |
| 공유 화면 | Python이 조회한 결과를 정류소 화면·아두이노·휴대폰 페이지에서 공유 |
| 마지막 성공 시각 | 화면에 표시하고, 갱신 실패 시 기존 정보가 오래된 정보임을 표시 |

휴대폰 접속자마다 TAGO를 직접 호출하지 않는다. API 키와 호출 제한 관리는 Python에서 맡긴다. 페이지별 조회 중에는 실시간 값이 바뀔 수 있으므로 여러 페이지를 하나의 정확히 같은 시각 데이터라고 보장하지 않는다.

## 6. 오류 대응 및 확인 항목

- **HTTP 성공과 API 성공을 따로 확인:** HTTP 200이어도 `resultCode`가 오류일 수 있다.
- **인증·요청 오류:** 키, 승인 상태, 도시코드, 정류소 ID를 확인한다. 잘못된 설정은 반복 재시도하지 않는다.
- **일시적 연결 오류:** 즉시 연속 호출하지 않고 다음 주기에 재시도한다. 실패가 반복되면 대기 시간을 늘린다.
- **호출 한도 오류:** 조회 간격·페이지 수·재시도 횟수를 확인하고 자동 호출을 줄인다. 실제 한도는 본인의 활용신청 내역에서 확인한다.
- **미확정 항목:** 지원 정류소 여부, 차량유형 실제 값, 도착임박 기준, 정보 유효시간, 중복 알림 해제 조건을 현장 데이터로 결정한다.

**적용 전 확인:** 정상 결과, 빈 결과, 한 건 결과, 여러 페이지, 인증 오류, 네트워크 실패를 각각 확인한다. 사용자 흐름과 전체 프로그램 처리 흐름은 이 교체 문서에서 확정하지 않는다.

---

출처: [공공데이터포털 — 국토교통부_(TAGO)_버스도착정보](https://www.data.go.kr/data/15098530/openapi.do), 요청·응답 항목 확인일: 2026-10-04. API 명세가 변경되면 공식 안내와 활용가이드를 기준으로 갱신한다.
