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

from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.server.stdio import stdio_server
from mcp import types

# 환경변수 로드
load_dotenv()

# 프로젝트 모듈 임포트
from src.data_sources import FREDClient, ECOSClient, DARTClient, BondClient
from src.models.stock import Stock, Portfolio
from src.risk.market_risk import MarketRiskAnalyzer
from src.risk.credit_risk import CreditRiskAnalyzer
from src.risk.liquidity_risk import LiquidityRiskAnalyzer
from src.portfolio.optimizer import PortfolioOptimizer

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
        # 포트폴리오 리스크 분석
        types.Tool(
            name="analyze_portfolio_risk",
            description="포트폴리오의 시장 리스크, 신용 리스크, 유동성 리스크를 종합 분석합니다.",
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
        if name == "analyze_portfolio_risk":
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
