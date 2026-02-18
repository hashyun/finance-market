# 한국시장 탑다운/투자주체별 분석 가이드

이 문서는 한국 주식을 **외국인·기관·개인** 관점에서 탑다운으로 해석하고, 이를 종합해 추천 종목을 도출하는 방법을 설명합니다.

## 1) 분석 프레임

1. **거시 환경 입력 (Top-Down)**
   - 위험선호(`risk_on_score`): 높을수록 성장/고베타 선호
   - 원달러 추세(`usdkrw_trend`): `down`이면 외국인 유입 우호적
   - 정책금리 방향(`policy_rate_direction`): `down`이면 기관 리스크자산 선호 강화 가능
   - 수출 사이클(`export_cycle_score`): 반도체/IT/자동차 등 수출주 우호성

2. **투자주체 관점 해석**
   - 외국인: 환율·수출·대형주 선호
   - 기관: 금리·밸류·퀄리티(재무건전성) 선호
   - 개인: 모멘텀·테마·변동성 반응 빠름

3. **종목 스코어링**
   - 기존 수급 분석(`InvestorFlowAnalyzer`) + 재무/시총/모멘텀/변동성 반영
   - 주체별 점수를 거시 국면 신뢰도로 가중 합산하여 `total_score` 계산

## 2) 코드 사용 예시

```python
from src.analysis import (
    MarketContext,
    TopDownParticipantRecommender,
)
from src.models.korean_stock import KoreanStock

context = MarketContext(
    risk_on_score=68,
    usdkrw_trend="down",
    policy_rate_direction="hold",
    export_cycle_score=72,
)

# stocks: List[KoreanStock]
views = TopDownParticipantRecommender.analyze_participant_views(context)
recs = TopDownParticipantRecommender.recommend_stocks(stocks, context, top_n=5)

for key, view in views.items():
    print(key, view.stance, view.confidence)

for rec in recs:
    print(rec.ticker, rec.name, rec.total_score)
    print(rec.reasons)
```

## 3) 해석 팁

- 외국인/기관이 동시에 강한 매수 점수이면 중기 추세 지속 가능성이 상대적으로 높습니다.
- 개인 점수만 높고 외국인·기관이 약한 경우 단기 과열 가능성을 반드시 점검하세요.
- 추천 결과는 리밸런싱 우선순위 신호로 활용하고, 실제 매매 전 실적/공시/밸류 검증을 병행하세요.
