"""
포지션 파일 업데이트 도구
매매 후 포지션 파일을 쉽게 업데이트할 수 있도록 도와주는 대화형 도구
"""
import json
import os
import sys


def load_positions(file_path):
    """포지션 파일 로드"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"포지션 파일을 찾을 수 없습니다: {file_path}")
        return {"cash": 0, "holdings": {}}
    except json.JSONDecodeError:
        print(f"포지션 파일 형식이 잘못되었습니다: {file_path}")
        return {"cash": 0, "holdings": {}}


def save_positions(file_path, positions):
    """포지션 파일 저장"""
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(positions, f, ensure_ascii=False, indent=2)
        print(f"\n✅ 포지션 파일이 저장되었습니다: {file_path}")
        return True
    except Exception as e:
        print(f"\n❌ 포지션 파일 저장 실패: {e}")
        return False


def print_current_positions(positions):
    """현재 포지션 출력"""
    print("\n" + "="*80)
    print("  현재 포지션")
    print("="*80)

    print(f"\n현금 잔고: {positions.get('cash', 0):,.0f}원")

    holdings = positions.get('holdings', {})

    if holdings:
        print("\n보유 종목:")
        print(f"  {'종목코드':10} {'종목명':15} {'수량':>10} {'평균단가':>15}")
        print("  " + "-"*60)

        for ticker, holding in holdings.items():
            name = holding.get('name', '-')
            quantity = holding.get('quantity', 0)
            avg_price = holding.get('avg_price', 0)

            print(f"  {ticker:10} {name:15} {quantity:>10,}주 {avg_price:>15,.0f}원")
    else:
        print("\n보유 종목이 없습니다.")

    print()


def update_cash(positions):
    """현금 잔고 업데이트"""
    current_cash = positions.get('cash', 0)
    print(f"\n현재 현금 잔고: {current_cash:,.0f}원")

    try:
        new_cash = float(input("새 현금 잔고 (원): ").replace(",", ""))
        positions['cash'] = new_cash
        print(f"✅ 현금 잔고가 {new_cash:,.0f}원으로 업데이트되었습니다.")
    except ValueError:
        print("❌ 잘못된 입력입니다.")


def add_or_update_holding(positions):
    """보유 종목 추가/수정"""
    ticker = input("\n종목코드 (예: 005930): ").strip()

    if not ticker:
        print("❌ 종목코드를 입력해주세요.")
        return

    holdings = positions.get('holdings', {})

    # 기존 보유 종목인지 확인
    if ticker in holdings:
        print(f"\n기존 보유 종목입니다:")
        print(f"  수량: {holdings[ticker]['quantity']:,}주")
        print(f"  평균단가: {holdings[ticker]['avg_price']:,.0f}원")

    name = input("종목명 (예: 삼성전자): ").strip()

    try:
        quantity = int(input("보유 수량 (주): ").replace(",", ""))
        avg_price = float(input("평균 단가 (원): ").replace(",", ""))

        holdings[ticker] = {
            "name": name,
            "quantity": quantity,
            "avg_price": avg_price
        }

        positions['holdings'] = holdings

        print(f"\n✅ {ticker} ({name}) 정보가 업데이트되었습니다:")
        print(f"   수량: {quantity:,}주")
        print(f"   평균단가: {avg_price:,.0f}원")

    except ValueError:
        print("❌ 잘못된 입력입니다.")


def remove_holding(positions):
    """보유 종목 삭제"""
    holdings = positions.get('holdings', {})

    if not holdings:
        print("\n보유 종목이 없습니다.")
        return

    ticker = input("\n삭제할 종목코드: ").strip()

    if ticker in holdings:
        name = holdings[ticker].get('name', '-')
        del holdings[ticker]
        positions['holdings'] = holdings
        print(f"\n✅ {ticker} ({name})이(가) 삭제되었습니다.")
    else:
        print(f"\n❌ {ticker}은(는) 보유하고 있지 않습니다.")


def record_trade(positions):
    """매매 기록 (간편 모드)"""
    print("\n매매 기록을 입력합니다.")

    trade_type = input("매수/매도 (B/S): ").strip().upper()

    if trade_type not in ['B', 'S']:
        print("❌ B(매수) 또는 S(매도)를 입력해주세요.")
        return

    ticker = input("종목코드: ").strip()

    try:
        quantity = int(input("수량 (주): ").replace(",", ""))
        price = float(input("체결가 (원): ").replace(",", ""))

        holdings = positions.get('holdings', {})

        if trade_type == 'B':
            # 매수
            if ticker in holdings:
                # 평균단가 재계산
                old_quantity = holdings[ticker]['quantity']
                old_avg_price = holdings[ticker]['avg_price']

                new_quantity = old_quantity + quantity
                new_avg_price = (old_quantity * old_avg_price + quantity * price) / new_quantity

                holdings[ticker]['quantity'] = new_quantity
                holdings[ticker]['avg_price'] = new_avg_price
            else:
                # 신규 매수
                name = input("종목명: ").strip()
                holdings[ticker] = {
                    "name": name,
                    "quantity": quantity,
                    "avg_price": price
                }

            # 현금 차감
            total_cost = quantity * price * 1.00015  # 수수료 0.015%
            positions['cash'] -= total_cost

            print(f"\n✅ 매수 기록 완료:")
            print(f"   종목: {ticker}")
            print(f"   수량: {quantity:,}주")
            print(f"   체결가: {price:,.0f}원")
            print(f"   총 비용: {total_cost:,.0f}원")

        else:
            # 매도
            if ticker not in holdings:
                print(f"❌ {ticker}은(는) 보유하고 있지 않습니다.")
                return

            if holdings[ticker]['quantity'] < quantity:
                print(f"❌ 보유 수량({holdings[ticker]['quantity']:,}주)보다 많이 매도할 수 없습니다.")
                return

            # 수량 차감
            holdings[ticker]['quantity'] -= quantity

            # 수량이 0이면 삭제
            if holdings[ticker]['quantity'] == 0:
                del holdings[ticker]

            # 현금 증가
            total_amount = quantity * price * (1 - 0.00015 - 0.0023)  # 수수료 + 세금
            positions['cash'] += total_amount

            print(f"\n✅ 매도 기록 완료:")
            print(f"   종목: {ticker}")
            print(f"   수량: {quantity:,}주")
            print(f"   체결가: {price:,.0f}원")
            print(f"   수령액: {total_amount:,.0f}원")

        positions['holdings'] = holdings

    except ValueError:
        print("❌ 잘못된 입력입니다.")


def main():
    print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                                                                            ║
║                     포지션 파일 업데이트 도구                                 ║
║                                                                            ║
╚════════════════════════════════════════════════════════════════════════════╝
    """)

    # 포지션 파일 경로
    file_path = "data/my_positions.json"

    if len(sys.argv) > 1:
        file_path = sys.argv[1]

    print(f"포지션 파일: {file_path}\n")

    # 포지션 로드
    positions = load_positions(file_path)

    while True:
        print_current_positions(positions)

        print("메뉴:")
        print("  1. 현금 잔고 업데이트")
        print("  2. 보유 종목 추가/수정")
        print("  3. 보유 종목 삭제")
        print("  4. 매매 기록 (간편 모드)")
        print("  5. 저장 및 종료")
        print("  6. 저장 없이 종료")

        choice = input("\n선택: ").strip()

        if choice == '1':
            update_cash(positions)
        elif choice == '2':
            add_or_update_holding(positions)
        elif choice == '3':
            remove_holding(positions)
        elif choice == '4':
            record_trade(positions)
        elif choice == '5':
            if save_positions(file_path, positions):
                print("\n프로그램을 종료합니다.")
                break
        elif choice == '6':
            print("\n저장하지 않고 종료합니다.")
            break
        else:
            print("\n❌ 잘못된 선택입니다.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n사용자가 중단했습니다.")
