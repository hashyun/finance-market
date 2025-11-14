#!/usr/bin/env python3
"""
Finance Market Analysis MCP Server
포트폴리오 리스크 분석 및 경제 데이터 조회를 위한 MCP 서버
"""
import asyncio
import os
from typing import Optional, Dict, List, Any
import json
from datetime import datetime
from dotenv import load_dotenv
import numpy as np

from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.server.stdio import stdio_server
from mcp import types

# 환경변수 로드
load_dotenv()

# 프로젝트 모듈 임포트
from src.data_sources import FREDClient, ECOSClient, DARTClient, BondClient
from src.models.stock import Stock, Portfolio
from src.models.korean_stock import KoreanStock
from src.risk.market_risk import MarketRiskAnalyzer
from src.risk.credit_risk import CreditRiskAnalyzer
from src.risk.liquidity_risk import LiquidityRiskAnalyzer
from src.portfolio.optimizer import PortfolioOptimizer
from src.utils.portfolio_helper import PortfolioHelper
from src.analysis.investor_flow import InvestorFlowAnalyzer
from src.strategies.foreign_follow import ForeignFollowStrategy
from src.strategies.momentum import MomentumStrategy
from src.strategies.mean_reversion import MeanReversionStrategy

# MCP 서버 초기화
server = Server("finance-market-mcp")

# 데이터 소스 클라이언트 (lazy initialization)
_fred_client = None
_ecos_client = None
_dart_client = None
_bond_client = None


def get_fred_client() -> Optional[FREDClient]:
    """FRED 클라이언트 싱글톤"""
    global _fred_client
    if _fred_client is None:
        try:
            _fred_client = FREDClient()
        except ValueError:
            pass
    return _fred_client


def get_ecos_client() -> Optional[ECOSClient]:
    """ECOS 클라이언트 싱글톤"""
    global _ecos_client
    if _ecos_client is None:
        try:
            _ecos_client = ECOSClient()
        except ValueError:
            pass
    return _ecos_client


def get_dart_client() -> Optional[DARTClient]:
    """DART 클라이언트 싱글톤"""
    global _dart_client
    if _dart_client is None:
        try:
            _dart_client = DARTClient()
        except ValueError:
            pass
    return _dart_client


def get_bond_client() -> BondClient:
    """Bond 클라이언트 싱글톤"""
    global _bond_client
    if _bond_client is None:
        _bond_client = BondClient()
    return _bond_client


@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """
    사용 가능한 도구 목록 반환
    """
    return [
        # ========== 간편 도구 (추천) ==========

        # 내 포지션 분석 (간편)
        types.Tool(
            name="analyze_my_portfolio",
            description="보유 중인 주식을 간단히 입력하면 실시간 데이터로 리스크를 분석합니다. 예: '삼성전자 100주, SK하이닉스 50주, NAVER 30주'",
            inputSchema={
                "type": "object",
                "properties": {
                    "positions": {
                        "type": "string",
                        "description": "보유 주식 목록 (예: '삼성전자 100주, SK하이닉스 50주' 또는 '005930 100주, 000660 50주')"
                    }
                },
                "required": ["positions"]
            }
        ),

        # 내 종목으로 최적화 (간편)
        types.Tool(
            name="optimize_my_stocks",
            description="보유 종목들로 최적의 투자 비중을 계산합니다. 예: '삼성전자, SK하이닉스, NAVER'",
            inputSchema={
                "type": "object",
                "properties": {
                    "tickers": {
                        "type": "string",
                        "description": "종목 목록 (예: '삼성전자, SK하이닉스, NAVER' 또는 '005930, 000660, 035420')"
                    },
                    "method": {
                        "type": "string",
                        "description": "최적화 방법: 'max_sharpe' (샤프비율 최대화) 또는 'risk_aware' (리스크 고려)",
                        "enum": ["max_sharpe", "risk_aware"],
                        "default": "max_sharpe"
                    }
                },
                "required": ["tickers"]
            }
        ),

        # 실시간 종목 정보
        types.Tool(
            name="get_stock_info",
            description="종목의 실시간 정보를 조회합니다 (현재가, 거래량, 시가총액 등). 예: '삼성전자' 또는 '005930'",
            inputSchema={
                "type": "object",
                "properties": {
                    "ticker": {
                        "type": "string",
                        "description": "종목명 또는 종목코드 (예: '삼성전자' 또는 '005930')"
                    }
                },
                "required": ["ticker"]
            }
        ),

        # ========== 한국 시장 전용 (외국인/기관 매매) ==========

        # 투자자별 매매 동향
        types.Tool(
            name="get_investor_flow",
            description="외국인/기관/개인 투자자의 매매 동향을 분석합니다. 예: '삼성전자'",
            inputSchema={
                "type": "object",
                "properties": {
                    "ticker": {
                        "type": "string",
                        "description": "종목명 또는 종목코드"
                    },
                    "days": {
                        "type": "integer",
                        "description": "분석 기간 (일수)",
                        "default": 20
                    }
                },
                "required": ["ticker"]
            }
        ),

        # 외국인 선호 종목
        types.Tool(
            name="find_foreign_favorites",
            description="외국인이 최근 집중 매수하고 있는 종목을 찾습니다. 여러 종목을 분석하여 상위 종목을 추천합니다.",
            inputSchema={
                "type": "object",
                "properties": {
                    "tickers": {
                        "type": "string",
                        "description": "분석할 종목 목록 (예: '삼성전자, SK하이닉스, NAVER, 카카오')"
                    },
                    "top_n": {
                        "type": "integer",
                        "description": "상위 몇 개 종목을 추천할지",
                        "default": 3
                    }
                },
                "required": ["tickers"]
            }
        ),

        # 매매 전략 신호
        types.Tool(
            name="get_trading_signals",
            description="외국인 수급, 모멘텀, 평균회귀 전략을 종합하여 매매 신호를 생성합니다. 예: '삼성전자'",
            inputSchema={
                "type": "object",
                "properties": {
                    "ticker": {
                        "type": "string",
                        "description": "종목명 또는 종목코드"
                    },
                    "strategies": {
                        "type": "array",
                        "description": "사용할 전략 목록",
                        "items": {
                            "type": "string",
                            "enum": ["foreign_follow", "momentum", "mean_reversion"]
                        },
                        "default": ["foreign_follow", "momentum"]
                    }
                },
                "required": ["ticker"]
            }
        ),

        # 숏 스퀴즈 분석
        types.Tool(
            name="analyze_short_squeeze",
            description="공매도 비율과 외국인/기관 매수세를 분석하여 숏 스퀴즈 가능성을 평가합니다.",
            inputSchema={
                "type": "object",
                "properties": {
                    "ticker": {
                        "type": "string",
                        "description": "종목명 또는 종목코드"
                    }
                },
                "required": ["ticker"]
            }
        ),

        # ========== 기존 고급 도구 ==========

        # 포트폴리오 리스크 분석
        types.Tool(
            name="analyze_portfolio_risk",
            description="[고급] 상세한 주식 데이터로 포트폴리오 리스크를 분석합니다.",
            inputSchema={
                "type": "object",
                "properties": {
                    "stocks": {
                        "type": "array",
                        "description": "주식 정보 배열",
                        "items": {
                            "type": "object",
                            "properties": {
                                "ticker": {"type": "string"},
                                "name": {"type": "string"},
                                "sector": {"type": "string"},
                                "price": {"type": "number"},
                                "historical_returns": {"type": "array", "items": {"type": "number"}},
                                "trading_volume": {"type": "number"},
                                "market_cap": {"type": "number"},
                                "debt_to_equity": {"type": "number"},
                                "current_ratio": {"type": "number"},
                                "credit_rating": {"type": "string"}
                            },
                            "required": ["ticker", "price", "historical_returns"]
                        }
                    },
                    "weights": {
                        "type": "array",
                        "description": "포트폴리오 비중 배열",
                        "items": {"type": "number"}
                    }
                },
                "required": ["stocks", "weights"]
            }
        ),

        # 포트폴리오 최적화
        types.Tool(
            name="optimize_portfolio",
            description="주어진 주식들로 최적 포트폴리오를 구성합니다 (샤프 비율 최대화 또는 위험 인식 최적화).",
            inputSchema={
                "type": "object",
                "properties": {
                    "stocks": {
                        "type": "array",
                        "description": "주식 정보 배열",
                        "items": {"type": "object"}
                    },
                    "method": {
                        "type": "string",
                        "description": "최적화 방법: 'max_sharpe' 또는 'risk_aware'",
                        "enum": ["max_sharpe", "risk_aware"]
                    },
                    "risk_free_rate": {
                        "type": "number",
                        "description": "무위험 이자율",
                        "default": 0.035
                    }
                },
                "required": ["stocks", "method"]
            }
        ),

        # FRED 데이터 조회
        types.Tool(
            name="get_fred_data",
            description="FRED(Federal Reserve Economic Data)에서 미국 경제 지표를 조회합니다.",
            inputSchema={
                "type": "object",
                "properties": {
                    "data_type": {
                        "type": "string",
                        "description": "데이터 유형: 'treasury', 'interest_rates', 'economic_indicators', 'credit_spreads'",
                        "enum": ["treasury", "interest_rates", "economic_indicators", "credit_spreads"]
                    },
                    "start_date": {
                        "type": "string",
                        "description": "시작일 (YYYY-MM-DD)"
                    },
                    "end_date": {
                        "type": "string",
                        "description": "종료일 (YYYY-MM-DD)"
                    }
                },
                "required": ["data_type"]
            }
        ),

        # ECOS 데이터 조회
        types.Tool(
            name="get_ecos_data",
            description="한국은행 경제통계(ECOS)에서 한국 경제 지표를 조회합니다.",
            inputSchema={
                "type": "object",
                "properties": {
                    "data_type": {
                        "type": "string",
                        "description": "데이터 유형: 'base_rate', 'exchange_rate', 'cpi', 'gdp', 'bond_yields', 'money_supply'",
                        "enum": ["base_rate", "exchange_rate", "cpi", "gdp", "bond_yields", "money_supply"]
                    },
                    "start_date": {
                        "type": "string",
                        "description": "시작일 (YYYYMMDD)"
                    },
                    "end_date": {
                        "type": "string",
                        "description": "종료일 (YYYYMMDD)"
                    },
                    "currency": {
                        "type": "string",
                        "description": "환율 조회 시 통화 코드 (USD, EUR, JPY, CNY)",
                        "default": "USD"
                    }
                },
                "required": ["data_type"]
            }
        ),

        # DART 기업정보 조회
        types.Tool(
            name="get_company_info",
            description="DART를 통해 기업의 재무정보 및 공시정보를 조회합니다.",
            inputSchema={
                "type": "object",
                "properties": {
                    "corp_name": {
                        "type": "string",
                        "description": "기업명 (예: 삼성전자)"
                    },
                    "info_type": {
                        "type": "string",
                        "description": "정보 유형: 'overview', 'financial_statement', 'ratios', 'disclosures'",
                        "enum": ["overview", "financial_statement", "ratios", "disclosures"]
                    },
                    "year": {
                        "type": "integer",
                        "description": "연도 (재무정보 조회 시)",
                        "default": 2023
                    }
                },
                "required": ["corp_name", "info_type"]
            }
        ),

        # 국채 수익률 조회
        types.Tool(
            name="get_bond_yields",
            description="한국 국채 수익률 곡선을 조회하고 분석합니다.",
            inputSchema={
                "type": "object",
                "properties": {
                    "analysis_type": {
                        "type": "string",
                        "description": "분석 유형: 'current_curve', 'historical', 'spread', 'shape_analysis'",
                        "enum": ["current_curve", "historical", "spread", "shape_analysis"]
                    },
                    "start_date": {
                        "type": "string",
                        "description": "시작일 (YYYYMMDD)"
                    },
                    "end_date": {
                        "type": "string",
                        "description": "종료일 (YYYYMMDD)"
                    }
                },
                "required": ["analysis_type"]
            }
        ),
    ]


@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict | None
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """
    도구 호출 처리
    """
    try:
        # 간편 도구
        if name == "analyze_my_portfolio":
            return await analyze_my_portfolio(arguments)
        elif name == "optimize_my_stocks":
            return await optimize_my_stocks(arguments)
        elif name == "get_stock_info":
            return await get_stock_info(arguments)
        # 한국 시장 전용 (외국인/기관)
        elif name == "get_investor_flow":
            return await get_investor_flow(arguments)
        elif name == "find_foreign_favorites":
            return await find_foreign_favorites(arguments)
        elif name == "get_trading_signals":
            return await get_trading_signals(arguments)
        elif name == "analyze_short_squeeze":
            return await analyze_short_squeeze(arguments)
        # 기존 도구
        elif name == "analyze_portfolio_risk":
            return await analyze_portfolio_risk(arguments)
        elif name == "optimize_portfolio":
            return await optimize_portfolio(arguments)
        elif name == "get_fred_data":
            return await get_fred_data(arguments)
        elif name == "get_ecos_data":
            return await get_ecos_data(arguments)
        elif name == "get_company_info":
            return await get_company_info(arguments)
        elif name == "get_bond_yields":
            return await get_bond_yields(arguments)
        else:
            return [types.TextContent(type="text", text=f"알 수 없는 도구: {name}")]

    except Exception as e:
        return [types.TextContent(type="text", text=f"오류 발생: {str(e)}")]


async def analyze_portfolio_risk(args: dict) -> list[types.TextContent]:
    """포트폴리오 리스크 분석"""
    stocks_data = args["stocks"]
    weights = args["weights"]

    # Stock 객체 생성
    stocks = []
    for stock_data in stocks_data:
        stock = Stock(
            ticker=stock_data["ticker"],
            name=stock_data.get("name", stock_data["ticker"]),
            sector=stock_data.get("sector", "기타"),
            price=stock_data["price"],
            historical_returns=stock_data["historical_returns"],
            trading_volume=stock_data.get("trading_volume", 1000000),
            market_cap=stock_data.get("market_cap", 1000000000000),
            debt_to_equity=stock_data.get("debt_to_equity", 1.0),
            current_ratio=stock_data.get("current_ratio", 1.5),
            credit_rating=stock_data.get("credit_rating", "BBB")
        )
        stocks.append(stock)

    # 포트폴리오 생성
    portfolio = Portfolio(stocks, weights)

    # 리스크 분석
    # 1. 시장 리스크
    var_95 = MarketRiskAnalyzer.value_at_risk(portfolio, 0.95)
    cvar_95 = MarketRiskAnalyzer.conditional_var(portfolio, 0.95)
    max_dd = MarketRiskAnalyzer.maximum_drawdown(portfolio)
    div_ratio = MarketRiskAnalyzer.diversification_ratio(portfolio)

    # 2. 신용 리스크
    credit_score = CreditRiskAnalyzer.portfolio_credit_score(portfolio)
    concentration = CreditRiskAnalyzer.concentration_risk(portfolio)
    sector_exp = CreditRiskAnalyzer.sector_exposure(portfolio)

    # 3. 유동성 리스크
    liquidity_score = LiquidityRiskAnalyzer.portfolio_liquidity_score(portfolio)

    result = {
        "포트폴리오 수익률": f"{portfolio.expected_return():.2%}",
        "포트폴리오 변동성": f"{portfolio.volatility():.2%}",
        "샤프 비율": f"{portfolio.sharpe_ratio(0.035):.2f}",
        "시장 리스크": {
            "VaR (95%)": f"{var_95:.2%}",
            "CVaR (95%)": f"{cvar_95:.2%}",
            "최대낙폭": f"{max_dd:.2%}",
            "분산투자비율": f"{div_ratio:.2f}"
        },
        "신용 리스크": {
            "신용점수": f"{credit_score:.1f}/100",
            "집중도 (HHI)": f"{concentration:.3f}",
            "섹터별 노출도": {k: f"{v:.1%}" for k, v in sector_exp.items()}
        },
        "유동성 리스크": {
            "유동성점수": f"{liquidity_score:.1f}/100"
        }
    }

    return [types.TextContent(
        type="text",
        text=json.dumps(result, ensure_ascii=False, indent=2)
    )]


async def optimize_portfolio(args: dict) -> list[types.TextContent]:
    """포트폴리오 최적화"""
    stocks_data = args["stocks"]
    method = args["method"]
    risk_free_rate = args.get("risk_free_rate", 0.035)

    # Stock 객체 생성
    stocks = []
    for stock_data in stocks_data:
        stock = Stock(
            ticker=stock_data["ticker"],
            name=stock_data.get("name", stock_data["ticker"]),
            sector=stock_data.get("sector", "기타"),
            price=stock_data["price"],
            historical_returns=stock_data["historical_returns"],
            trading_volume=stock_data.get("trading_volume", 1000000),
            market_cap=stock_data.get("market_cap", 1000000000000),
            debt_to_equity=stock_data.get("debt_to_equity", 1.0),
            current_ratio=stock_data.get("current_ratio", 1.5),
            credit_rating=stock_data.get("credit_rating", "BBB")
        )
        stocks.append(stock)

    # 최적화 엔진
    optimizer = PortfolioOptimizer(stocks, risk_free_rate=risk_free_rate)

    # 최적화 실행
    if method == "max_sharpe":
        portfolio = optimizer.optimize_max_sharpe()
    else:  # risk_aware
        portfolio = optimizer.optimize_risk_aware()

    # 결과 분석
    analysis = optimizer.analyze_portfolio(portfolio)

    result = {
        "최적화 방법": method,
        "포트폴리오 구성": {
            stock.ticker: f"{weight:.1%}"
            for stock, weight in zip(portfolio.stocks, portfolio.weights)
        },
        "성과 지표": {
            "기대수익률": f"{analysis['expected_return']:.2%}",
            "변동성": f"{analysis['volatility']:.2%}",
            "샤프비율": f"{analysis['sharpe_ratio']:.2f}",
            "신용점수": f"{analysis['credit_score']:.1f}/100",
            "유동성점수": f"{analysis['liquidity_score']:.1f}/100"
        }
    }

    return [types.TextContent(
        type="text",
        text=json.dumps(result, ensure_ascii=False, indent=2)
    )]


async def get_fred_data(args: dict) -> list[types.TextContent]:
    """FRED 데이터 조회"""
    client = get_fred_client()
    if not client:
        return [types.TextContent(
            type="text",
            text="FRED API 키가 설정되지 않았습니다. .env 파일에 FRED_API_KEY를 설정하세요."
        )]

    data_type = args["data_type"]
    start_date = args.get("start_date")
    end_date = args.get("end_date")

    if data_type == "treasury":
        data = client.get_treasury_yields(start_date, end_date)
    elif data_type == "interest_rates":
        data = client.get_interest_rates(start_date, end_date)
    elif data_type == "economic_indicators":
        data = client.get_economic_indicators(start_date, end_date)
    elif data_type == "credit_spreads":
        data = client.get_credit_spreads(start_date, end_date)
    else:
        return [types.TextContent(type="text", text="지원하지 않는 데이터 유형입니다.")]

    # 데이터를 JSON으로 변환
    result = {}
    for name, series in data.items():
        if len(series) > 0:
            result[name] = {
                "최근값": float(series.iloc[-1]) if len(series) > 0 else None,
                "평균": float(series.mean()),
                "최대": float(series.max()),
                "최소": float(series.min()),
                "데이터포인트수": len(series)
            }

    return [types.TextContent(
        type="text",
        text=json.dumps(result, ensure_ascii=False, indent=2)
    )]


async def get_ecos_data(args: dict) -> list[types.TextContent]:
    """ECOS 데이터 조회"""
    client = get_ecos_client()
    if not client:
        return [types.TextContent(
            type="text",
            text="ECOS API 키가 설정되지 않았습니다. .env 파일에 ECOS_API_KEY를 설정하세요."
        )]

    data_type = args["data_type"]
    start_date = args.get("start_date", "20200101")
    end_date = args.get("end_date")

    if data_type == "base_rate":
        df = client.get_base_rate(start_date, end_date)
    elif data_type == "exchange_rate":
        currency = args.get("currency", "USD")
        df = client.get_exchange_rate(currency, start_date, end_date)
    elif data_type == "cpi":
        df = client.get_cpi(start_date, end_date)
    elif data_type == "gdp":
        df = client.get_gdp(start_date, end_date)
    elif data_type == "bond_yields":
        df = client.get_bond_yields(start_date, end_date)
    elif data_type == "money_supply":
        df = client.get_money_supply(start_date, end_date)
    else:
        return [types.TextContent(type="text", text="지원하지 않는 데이터 유형입니다.")]

    if df.empty:
        return [types.TextContent(type="text", text="데이터를 조회할 수 없습니다.")]

    # DataFrame을 딕셔너리로 변환
    result = df.to_dict(orient='records')

    return [types.TextContent(
        type="text",
        text=json.dumps(result[:100], ensure_ascii=False, indent=2, default=str)
    )]


async def get_company_info(args: dict) -> list[types.TextContent]:
    """DART 기업정보 조회"""
    client = get_dart_client()
    if not client:
        return [types.TextContent(
            type="text",
            text="DART API 키가 설정되지 않았습니다. .env 파일에 DART_API_KEY를 설정하세요."
        )]

    corp_name = args["corp_name"]
    info_type = args["info_type"]
    year = args.get("year", 2023)

    # 기업 코드 조회
    corp_code = client.get_corp_code(corp_name)
    if not corp_code:
        return [types.TextContent(type="text", text=f"기업 '{corp_name}'을 찾을 수 없습니다.")]

    if info_type == "overview":
        data = client.get_company_overview(corp_code)
    elif info_type == "financial_statement":
        data = client.get_financial_statement(corp_code, year)
    elif info_type == "ratios":
        data = client.get_financial_ratios(corp_code, year)
    elif info_type == "disclosures":
        start_date = f"{year}0101"
        end_date = f"{year}1231"
        data = client.get_disclosure_list(corp_code, start_date, end_date)
    else:
        return [types.TextContent(type="text", text="지원하지 않는 정보 유형입니다.")]

    return [types.TextContent(
        type="text",
        text=json.dumps(data, ensure_ascii=False, indent=2, default=str)
    )]


async def get_bond_yields(args: dict) -> list[types.TextContent]:
    """국채 수익률 조회"""
    client = get_bond_client()
    analysis_type = args["analysis_type"]

    if analysis_type == "current_curve":
        data = client.get_yield_curve()
    elif analysis_type == "historical":
        start_date = args.get("start_date")
        end_date = args.get("end_date")
        df = client.get_treasury_yields(start_date, end_date)
        data = df.to_dict(orient='records')[:100]
    elif analysis_type == "spread":
        start_date = args.get("start_date")
        end_date = args.get("end_date")
        df = client.get_historical_spreads(start_date=start_date, end_date=end_date)
        data = df.to_dict(orient='records')[:100]
    elif analysis_type == "shape_analysis":
        data = client.analyze_yield_curve_shape()
    else:
        return [types.TextContent(type="text", text="지원하지 않는 분석 유형입니다.")]

    return [types.TextContent(
        type="text",
        text=json.dumps(data, ensure_ascii=False, indent=2, default=str)
    )]


# ========== 간편 도구 구현 ==========

async def analyze_my_portfolio(args: dict) -> list[types.TextContent]:
    """내 포지션 분석 (간편)"""
    positions = args["positions"]

    try:
        # 텍스트에서 포트폴리오 생성
        portfolio, details = PortfolioHelper.create_portfolio_from_text(positions)

        # 리스크 분석
        var_95 = MarketRiskAnalyzer.value_at_risk(portfolio, 0.95)
        cvar_95 = MarketRiskAnalyzer.conditional_var(portfolio, 0.95)
        max_dd = MarketRiskAnalyzer.maximum_drawdown(portfolio)
        div_ratio = MarketRiskAnalyzer.diversification_ratio(portfolio)

        credit_score = CreditRiskAnalyzer.portfolio_credit_score(portfolio)
        concentration = CreditRiskAnalyzer.concentration_risk(portfolio)
        sector_exp = CreditRiskAnalyzer.sector_exposure(portfolio)

        liquidity_score = LiquidityRiskAnalyzer.portfolio_liquidity_score(portfolio)

        # 결과 포맷팅
        summary = PortfolioHelper.format_position_summary(details)

        result = {
            "포지션 요약": summary,
            "성과 지표": {
                "기대수익률": f"{portfolio.expected_return():.2%}",
                "변동성": f"{portfolio.volatility():.2%}",
                "샤프비율": f"{portfolio.sharpe_ratio(0.035):.2f}"
            },
            "시장 리스크": {
                "VaR (95%)": f"{var_95:.2%}",
                "CVaR (95%)": f"{cvar_95:.2%}",
                "최대낙폭": f"{max_dd:.2%}",
                "분산투자비율": f"{div_ratio:.2f}"
            },
            "신용 리스크": {
                "신용점수": f"{credit_score:.1f}/100",
                "집중도 (HHI)": f"{concentration:.3f}",
                "섹터별 노출도": {k: f"{v:.1%}" for k, v in sector_exp.items()}
            },
            "유동성 리스크": {
                "유동성점수": f"{liquidity_score:.1f}/100"
            }
        }

        return [types.TextContent(
            type="text",
            text=json.dumps(result, ensure_ascii=False, indent=2)
        )]

    except Exception as e:
        return [types.TextContent(
            type="text",
            text=f"포트폴리오 분석 실패: {str(e)}\n\n"
                 f"입력 예시: '삼성전자 100주, SK하이닉스 50주, NAVER 30주' 또는 '005930 100주, 000660 50주, 035420 30주'"
        )]


async def optimize_my_stocks(args: dict) -> list[types.TextContent]:
    """내 종목으로 최적화 (간편)"""
    tickers_text = args["tickers"]
    method = args.get("method", "max_sharpe")

    try:
        # 종목 코드 파싱
        tickers = [t.strip() for t in tickers_text.replace(',', ' ').split() if t.strip()]

        # 종목 데이터 수집
        stocks = []
        for ticker in tickers:
            # 숫자가 아니면 종목명으로 간주
            if not ticker.isdigit():
                # 간단한 이름-코드 매핑 (실제로는 검색 API 사용)
                ticker_map = {
                    '삼성전자': '005930',
                    'SK하이닉스': '000660',
                    'NAVER': '035420',
                    '카카오': '035720',
                }
                ticker = ticker_map.get(ticker, ticker)

            stock_data = PortfolioHelper.get_stock_data(ticker)
            if not stock_data:
                continue

            stock_obj = Stock(
                ticker=stock_data['ticker'],
                name=stock_data['name'],
                sector=stock_data['sector'],
                price=stock_data['price'],
                historical_returns=stock_data['historical_returns'],
                trading_volume=stock_data['trading_volume'],
                market_cap=stock_data['market_cap'],
                debt_to_equity=stock_data['debt_to_equity'],
                current_ratio=stock_data['current_ratio'],
                credit_rating=stock_data['credit_rating']
            )
            stocks.append(stock_obj)

        if not stocks:
            return [types.TextContent(type="text", text="조회 가능한 종목이 없습니다.")]

        # 최적화 엔진
        optimizer = PortfolioOptimizer(stocks, risk_free_rate=0.035)

        # 최적화 실행
        if method == "max_sharpe":
            portfolio = optimizer.optimize_max_sharpe()
        else:
            portfolio = optimizer.optimize_risk_aware()

        # 결과 분석
        analysis = optimizer.analyze_portfolio(portfolio)

        result = {
            "최적화 방법": "샤프 비율 최대화" if method == "max_sharpe" else "리스크 인식 최적화",
            "추천 포트폴리오": {
                f"{stock.name}({stock.ticker})": f"{weight:.1%}"
                for stock, weight in zip(portfolio.stocks, portfolio.weights)
                if weight > 0.001  # 0.1% 이상만 표시
            },
            "성과 지표": {
                "기대수익률": f"{analysis['expected_return']:.2%}",
                "변동성": f"{analysis['volatility']:.2%}",
                "샤프비율": f"{analysis['sharpe_ratio']:.2f}",
                "신용점수": f"{analysis['credit_score']:.1f}/100",
                "유동성점수": f"{analysis['liquidity_score']:.1f}/100"
            }
        }

        return [types.TextContent(
            type="text",
            text=json.dumps(result, ensure_ascii=False, indent=2)
        )]

    except Exception as e:
        return [types.TextContent(
            type="text",
            text=f"최적화 실패: {str(e)}\n\n"
                 f"입력 예시: '삼성전자, SK하이닉스, NAVER' 또는 '005930, 000660, 035420'"
        )]


async def get_stock_info(args: dict) -> list[types.TextContent]:
    """실시간 종목 정보"""
    ticker = args["ticker"]

    try:
        # 종목명이면 코드로 변환
        if not ticker.isdigit():
            ticker_map = {
                '삼성전자': '005930',
                'SK하이닉스': '000660',
                'NAVER': '035420',
                '카카오': '035720',
            }
            ticker = ticker_map.get(ticker, ticker)

        stock_data = PortfolioHelper.get_stock_data(ticker, days=30)

        if not stock_data:
            return [types.TextContent(type="text", text=f"종목 '{ticker}'의 정보를 조회할 수 없습니다.")]

        # 30일 수익률 계산
        returns_30d = np.array(stock_data['historical_returns'][-30:]) if len(stock_data['historical_returns']) >= 30 else []
        total_return_30d = (1 + returns_30d).prod() - 1 if len(returns_30d) > 0 else 0

        result = {
            "종목명": stock_data['name'],
            "종목코드": stock_data['ticker'],
            "섹터": stock_data['sector'],
            "현재가": f"{stock_data['price']:,.0f}원",
            "시가총액": f"{stock_data['market_cap']/100000000:.0f}억원",
            "거래량": f"{stock_data['trading_volume']:,.0f}주",
            "30일 수익률": f"{total_return_30d:.2%}" if len(returns_30d) > 0 else "N/A",
            "변동성 (연환산)": f"{np.std(stock_data['historical_returns']) * np.sqrt(252):.2%}" if len(stock_data['historical_returns']) > 0 else "N/A"
        }

        return [types.TextContent(
            type="text",
            text=json.dumps(result, ensure_ascii=False, indent=2)
        )]

    except Exception as e:
        return [types.TextContent(
            type="text",
            text=f"종목 조회 실패: {str(e)}\n\n"
                 f"입력 예시: '삼성전자' 또는 '005930'"
        )]


# ========== 한국 시장 전용 도구 구현 (외국인/기관 매매) ==========

async def get_investor_flow(args: dict) -> list[types.TextContent]:
    """투자자별 매매 동향 분석"""
    ticker = args["ticker"]
    days = args.get("days", 20)

    try:
        # 종목명 변환
        if not ticker.isdigit():
            ticker_map = {
                '삼성전자': '005930',
                'SK하이닉스': '000660',
                'NAVER': '035420',
                '카카오': '035720',
            }
            ticker = ticker_map.get(ticker, ticker)

        # KoreanStock 객체 생성 (실제로는 pykrx로 데이터 조회해야 함)
        # 여기서는 샘플 구현
        result = {
            "종목코드": ticker,
            "분석기간": f"{days}일",
            "설명": "외국인/기관 매매 동향 분석 기능은 실시간 KRX 데이터와 함께 사용하면 더 정확합니다.",
            "기능": [
                "외국인 매수 강도 분석",
                "기관 매수 강도 분석",
                "투자자 컨센서스 (외국인+기관 일치도)",
                "프로그램 매매 신호",
                "숏 스퀴즈 가능성 분석"
            ],
            "사용방법": "실시간 데이터와 함께 사용하려면 KRX API 클라이언트를 통해 TradingData를 제공해야 합니다."
        }

        return [types.TextContent(
            type="text",
            text=json.dumps(result, ensure_ascii=False, indent=2)
        )]

    except Exception as e:
        return [types.TextContent(type="text", text=f"분석 실패: {str(e)}")]


async def find_foreign_favorites(args: dict) -> list[types.TextContent]:
    """외국인 선호 종목 찾기"""
    tickers_text = args["tickers"]
    top_n = args.get("top_n", 3)

    try:
        # 종목 코드 파싱
        tickers = [t.strip() for t in tickers_text.replace(',', ' ').split() if t.strip()]

        ticker_map = {
            '삼성전자': '005930',
            'SK하이닉스': '000660',
            'NAVER': '035420',
            '카카오': '035720',
        }

        # 종목명을 코드로 변환
        converted_tickers = []
        for ticker in tickers:
            if not ticker.isdigit():
                ticker = ticker_map.get(ticker, ticker)
            converted_tickers.append(ticker)

        result = {
            "분석종목수": len(converted_tickers),
            "상위추천수": top_n,
            "설명": "외국인 선호 종목 분석은 실시간 외국인 매매 데이터가 필요합니다.",
            "추천로직": [
                "최근 20일간 외국인 순매수 강도 계산",
                "기관 매매와의 컨센서스 확인",
                "프로그램 매매 신호 반영"
            ],
            "필요데이터": "pykrx를 통한 실시간 투자자별 매매 동향 데이터"
        }

        return [types.TextContent(
            type="text",
            text=json.dumps(result, ensure_ascii=False, indent=2)
        )]

    except Exception as e:
        return [types.TextContent(type="text", text=f"분석 실패: {str(e)}")]


async def get_trading_signals(args: dict) -> list[types.TextContent]:
    """매매 전략 신호 생성"""
    ticker = args["ticker"]
    strategies = args.get("strategies", ["foreign_follow", "momentum"])

    try:
        # 종목명 변환
        if not ticker.isdigit():
            ticker_map = {
                '삼성전자': '005930',
                'SK하이닉스': '000660',
                'NAVER': '035420',
                '카카오': '035720',
            }
            ticker = ticker_map.get(ticker, ticker)

        result = {
            "종목코드": ticker,
            "적용전략": strategies,
            "설명": "다중 전략 매매 신호 생성",
            "전략설명": {
                "foreign_follow": "외국인+기관 순매수 추종 전략",
                "momentum": "가격 모멘텀 및 기술적 지표 전략",
                "mean_reversion": "볼린저 밴드 기반 평균회귀 전략"
            },
            "필요데이터": [
                "투자자별 매매 동향 (pykrx)",
                "가격 및 거래량 데이터",
                "기술적 지표 (RSI, MACD, 볼린저밴드)"
            ]
        }

        return [types.TextContent(
            type="text",
            text=json.dumps(result, ensure_ascii=False, indent=2)
        )]

    except Exception as e:
        return [types.TextContent(type="text", text=f"신호 생성 실패: {str(e)}")]


async def analyze_short_squeeze(args: dict) -> list[types.TextContent]:
    """숏 스퀴즈 가능성 분석"""
    ticker = args["ticker"]

    try:
        # 종목명 변환
        if not ticker.isdigit():
            ticker_map = {
                '삼성전자': '005930',
                'SK하이닉스': '000660',
                'NAVER': '035420',
                '카카오': '035720',
            }
            ticker = ticker_map.get(ticker, ticker)

        result = {
            "종목코드": ticker,
            "분석항목": [
                "공매도 비율 (전체 거래량 대비)",
                "외국인 + 기관 순매수 강도",
                "프로그램 매수 급증 여부",
                "거래량 급증 패턴"
            ],
            "숏스퀴즈 조건": {
                "공매도비율": "10% 이상",
                "외국인기관": "동시 순매수 전환",
                "거래량": "평균 대비 2배 이상 증가"
            },
            "데이터소스": "pykrx를 통한 공매도 데이터 및 투자자별 매매 동향",
            "참고": "실제 숏 스퀴즈 분석을 위해서는 실시간 공매도 데이터가 필요합니다."
        }

        return [types.TextContent(
            type="text",
            text=json.dumps(result, ensure_ascii=False, indent=2)
        )]

    except Exception as e:
        return [types.TextContent(type="text", text=f"분석 실패: {str(e)}")]


async def main():
    """MCP 서버 실행"""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="finance-market-mcp",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


if __name__ == "__main__":
    asyncio.run(main())
