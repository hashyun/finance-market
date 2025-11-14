"""
DART (금융감독원 전자공시) 클라이언트
기업 재무정보 및 공시정보 조회
"""
import os
from typing import Optional, Dict, List
import pandas as pd

try:
    import dart_fss as dart
    DART_AVAILABLE = True
except ImportError:
    DART_AVAILABLE = False
    dart = None


class DARTClient:
    """
    DART 공시정보 클라이언트
    기업 재무제표, 공시정보 조회
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Args:
            api_key: DART API 키 (환경변수에서 자동 로드 가능)
        """
        if not DART_AVAILABLE:
            raise ValueError(
                "dart-fss 패키지가 설치되지 않았습니다. "
                "pip install dart-fss 로 설치하세요."
            )

        self.api_key = api_key or os.getenv('DART_API_KEY')
        if not self.api_key:
            raise ValueError(
                "DART API 키가 필요합니다. "
                "https://opendart.fss.or.kr/ 에서 발급받으세요."
            )

        # DART API 초기화
        dart.set_api_key(self.api_key)

    def get_corp_code(self, corp_name: str) -> Optional[str]:
        """
        기업명으로 고유번호 조회

        Args:
            corp_name: 기업명

        Returns:
            DART 고유번호
        """
        try:
            corp_list = dart.get_corp_list()
            corp = corp_list.find_by_corp_name(corp_name, exactly=True)
            if corp:
                return corp[0].corp_code
        except Exception as e:
            print(f"기업코드 조회 실패: {e}")

        return None

    def get_financial_statement(
        self,
        corp_code: str,
        year: int,
        quarter: int = 4,
        report_type: str = 'consolidated'
    ) -> Dict[str, pd.DataFrame]:
        """
        재무제표 조회

        Args:
            corp_code: 기업 고유번호 또는 종목코드
            year: 연도
            quarter: 분기 (1, 2, 3, 4)
            report_type: 'consolidated' (연결) 또는 'separate' (개별)

        Returns:
            재무제표 데이터 (재무상태표, 손익계산서, 현금흐름표 등)
        """
        try:
            # 기업 객체 가져오기
            corp = dart.get_corp(corp_code)

            # 사업보고서 or 분기보고서
            if quarter == 4:
                reports = corp.search_filings(
                    bgn_de=f'{year}0101',
                    end_de=f'{year}1231',
                    pblntf_ty='A'  # 사업보고서
                )
            else:
                reports = corp.search_filings(
                    bgn_de=f'{year}0101',
                    end_de=f'{year}1231',
                    pblntf_ty='Q'  # 분기보고서
                )

            if not reports:
                return {}

            # 최신 보고서
            report = reports[0]

            # 재무제표 추출
            fs = report.get_financial_statement()

            result = {}
            if hasattr(fs, 'show'):
                # 재무상태표
                result['balance_sheet'] = fs.show('bs', report_type)
                # 손익계산서
                result['income_statement'] = fs.show('is', report_type)
                # 현금흐름표
                result['cash_flow'] = fs.show('cf', report_type)

            return result

        except Exception as e:
            print(f"재무제표 조회 실패: {e}")
            return {}

    def get_financial_ratios(
        self,
        corp_code: str,
        year: int
    ) -> Dict[str, float]:
        """
        주요 재무비율 계산

        Args:
            corp_code: 기업 고유번호
            year: 연도

        Returns:
            재무비율 딕셔너리
        """
        fs = self.get_financial_statement(corp_code, year)

        if not fs or 'balance_sheet' not in fs or 'income_statement' not in fs:
            return {}

        bs = fs['balance_sheet']
        income = fs['income_statement']

        ratios = {}

        try:
            # 부채비율 = 총부채 / 자기자본
            total_liabilities = bs.loc[bs['account_nm'] == '부채총계', 'thstrm_amount'].values
            total_equity = bs.loc[bs['account_nm'] == '자본총계', 'thstrm_amount'].values

            if len(total_liabilities) > 0 and len(total_equity) > 0:
                liabilities = float(total_liabilities[0])
                equity = float(total_equity[0])
                if equity != 0:
                    ratios['debt_to_equity'] = liabilities / equity

            # 유동비율 = 유동자산 / 유동부채
            current_assets = bs.loc[bs['account_nm'] == '유동자산', 'thstrm_amount'].values
            current_liabilities = bs.loc[bs['account_nm'] == '유동부채', 'thstrm_amount'].values

            if len(current_assets) > 0 and len(current_liabilities) > 0:
                assets = float(current_assets[0])
                liabilities = float(current_liabilities[0])
                if liabilities != 0:
                    ratios['current_ratio'] = assets / liabilities

            # ROE = 당기순이익 / 자기자본
            net_income = income.loc[income['account_nm'] == '당기순이익', 'thstrm_amount'].values
            if len(net_income) > 0 and len(total_equity) > 0:
                income_val = float(net_income[0])
                equity_val = float(total_equity[0])
                if equity_val != 0:
                    ratios['roe'] = income_val / equity_val

        except Exception as e:
            print(f"재무비율 계산 실패: {e}")

        return ratios

    def get_disclosure_list(
        self,
        corp_code: str,
        start_date: str,
        end_date: str,
        report_type: Optional[str] = None
    ) -> List[Dict]:
        """
        공시 목록 조회

        Args:
            corp_code: 기업 고유번호
            start_date: 시작일 (YYYYMMDD)
            end_date: 종료일 (YYYYMMDD)
            report_type: 공시유형 ('A': 정기, 'I': 주요사항, 'F': 기타 등)

        Returns:
            공시 목록
        """
        try:
            corp = dart.get_corp(corp_code)
            filings = corp.search_filings(
                bgn_de=start_date,
                end_de=end_date,
                pblntf_ty=report_type
            )

            results = []
            for filing in filings:
                results.append({
                    'report_nm': filing.report_nm,
                    'rcept_dt': filing.rcept_dt,
                    'rm': filing.rm
                })

            return results

        except Exception as e:
            print(f"공시 목록 조회 실패: {e}")
            return []

    def get_company_overview(self, corp_code: str) -> Dict:
        """
        기업 개요 조회

        Args:
            corp_code: 기업 고유번호

        Returns:
            기업 개요 정보
        """
        try:
            corp = dart.get_corp(corp_code)

            return {
                'corp_name': corp.corp_name,
                'corp_code': corp.corp_code,
                'stock_code': corp.stock_code,
                'ceo_nm': getattr(corp, 'ceo_nm', None),
                'corp_cls': getattr(corp, 'corp_cls', None),
                'jurir_no': getattr(corp, 'jurir_no', None),
                'bizr_no': getattr(corp, 'bizr_no', None),
                'adres': getattr(corp, 'adres', None),
                'hm_url': getattr(corp, 'hm_url', None),
                'ir_url': getattr(corp, 'ir_url', None),
                'phn_no': getattr(corp, 'phn_no', None),
            }

        except Exception as e:
            print(f"기업 개요 조회 실패: {e}")
            return {}

    def get_credit_rating(self, corp_code: str) -> Optional[str]:
        """
        신용등급 조회 (간접적 추정)

        Args:
            corp_code: 기업 고유번호

        Returns:
            추정 신용등급
        """
        # 재무비율로 간접 추정
        ratios = self.get_financial_ratios(corp_code, 2023)

        if not ratios:
            return None

        debt_ratio = ratios.get('debt_to_equity', 999)
        current_ratio = ratios.get('current_ratio', 0)
        roe = ratios.get('roe', 0)

        # 간단한 규칙 기반 추정
        if debt_ratio < 0.5 and current_ratio > 2.0 and roe > 0.15:
            return 'AA'
        elif debt_ratio < 1.0 and current_ratio > 1.5 and roe > 0.10:
            return 'A'
        elif debt_ratio < 2.0 and current_ratio > 1.0 and roe > 0.05:
            return 'BBB'
        elif debt_ratio < 3.0 and current_ratio > 0.8:
            return 'BB'
        else:
            return 'B'
