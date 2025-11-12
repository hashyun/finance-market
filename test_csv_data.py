"""
CSV 데이터 조회 테스트
"""
from src.api.krx_client import KRXAPIClient

print("="*80)
print("CSV 데이터 조회 테스트")
print("="*80)

# API 클라이언트 초기화
api_client = KRXAPIClient(position_file="data/my_positions.json")
api_client.connect()

print("\n삼성전자 시세 조회...")
market_data = api_client.get_market_data('005930')

if market_data:
    print(f"✅ 성공!")
    print(f"  종목: {market_data.ticker}")
    print(f"  현재가: {market_data.price:,.0f}원")
    print(f"  거래량: {market_data.volume:,}주")
else:
    print("❌ 실패")

print("\n" + "="*80)
print("여러 종목 일괄 조회")
print("="*80)

tickers = ['005930', '000660', '035420']
market_data_batch = api_client.get_market_data_batch(tickers)

print(f"\n조회 성공: {len(market_data_batch)}개 / {len(tickers)}개")

print("\n" + "="*80)
print("계좌 현황")
print("="*80)

account = api_client.get_account_balance()
print(f"\n현금 잔고: {account['cash_balance']:,.0f}원")
print(f"주식 평가액: {account['stock_value']:,.0f}원")
print(f"총 자산: {account['total_value']:,.0f}원")
print(f"손익: {account['profit_loss']:,.0f}원 ({account['profit_loss_pct']:+.2f}%)")

print("\n" + "="*80)
print("보유 종목")
print("="*80)

holdings = api_client.get_holdings()

for ticker, holding in holdings.items():
    print(f"\n{ticker}:")
    print(f"  수량: {holding['quantity']:,}주")
    print(f"  평균단가: {holding['avg_price']:,.0f}원")
    print(f"  현재가: {holding['current_price']:,.0f}원")
    print(f"  평가손익: {holding['profit_loss']:,.0f}원 ({holding['profit_loss_pct']:+.2f}%)")

print("\n" + "="*80)
print("테스트 완료!")
print("="*80)
