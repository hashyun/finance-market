# API 설정 가이드

## DART API 키 설정 (선택사항)

DART API는 기업 재무 정보를 조회하는데 사용됩니다. (선택사항이며, 없어도 시스템은 정상 작동합니다)

### 1. DART API 키 발급

1. DART 홈페이지 접속: https://opendart.fss.or.kr/
2. 회원가입 및 로그인
3. 인증키 신청/관리 메뉴에서 API 키 발급 (무료)
4. 발급받은 API 키 복사

### 2. API 키 설정 방법

#### 방법 1: .env 파일 사용 (추천)

1. 프로젝트 루트에 `.env` 파일 생성:
```bash
cp .env.example .env
```

2. `.env` 파일 편집:
```bash
vi .env
```

3. DART API 키 입력:
```
DART_API_KEY=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
```

4. 저장하고 종료

**주의:** `.env` 파일은 `.gitignore`에 포함되어 Git에 커밋되지 않습니다.

#### 방법 2: 환경변수로 설정

```bash
export DART_API_KEY=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
```

#### 방법 3: 코드에서 직접 설정

```python
from src.api.krx_client import KRXAPIClient

api_client = KRXAPIClient(
    position_file="data/my_positions.json",
    dart_api_key="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
)
```

**주의:** 코드에 직접 입력하면 Git에 커밋될 수 있으니 주의하세요.

## KRX API

KRX API는 별도 인증이 필요 없으며, 공개 API로 누구나 사용할 수 있습니다.

- 시세 정보
- 투자자별 매매 동향
- 등등

## API 우선순위

시스템은 다음 순서로 API 키를 찾습니다:

1. 코드에서 직접 전달한 값 (`dart_api_key` 파라미터)
2. 환경변수 (`DART_API_KEY`)
3. `.env` 파일의 값

## 확인 방법

```bash
python examples/manual_trading_example.py
```

출력:
- DART API 키가 설정되었으면: 아무 메시지 없음
- DART API 키가 없으면: "ℹ️ DART API 키가 설정되지 않았습니다. (선택사항)"

## 문제 해결

### API 키가 인식되지 않을 때

1. `.env` 파일 위치 확인:
```bash
ls -la .env
```

2. `.env` 파일 내용 확인:
```bash
cat .env
```

3. 형식 확인:
   - `DART_API_KEY=` 뒤에 공백 없이 키 입력
   - 줄바꿈 없이 한 줄로 입력

### DART API 오류

```
DART 기업 정보 조회 오류: ...
```

- API 키가 올바른지 확인
- 네트워크 연결 확인
- DART 서비스 점검 여부 확인

## 더 보기

- KRX API 문서: http://data.krx.co.kr
- DART API 문서: https://opendart.fss.or.kr/guide/main.do
