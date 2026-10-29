import random
import math
import pandas as pd
import streamlit as st
import plotly.express as px

st.set_page_config(page_title="CEO Simulator", page_icon="🏢", layout="wide")

# ----------------------------
# Game configuration (fictional model)
# ----------------------------
SECTORS = {
    "IT·인공지능": {
        "description": "AI 서비스, 소프트웨어, 디지털 플랫폼",
        "initial_cash": 100.0, "base_price": 50, "base_demand": 1800,
        "unit_cost": 13.0, "fixed_cost": 12.0, "staff_cost": 2.8,
        "rd_efficiency": 1.35, "ad_efficiency": 1.05,
        "risks": ["사이버 보안 사고", "신기술 경쟁 심화", "핵심 개발자 이탈"],
        "opportunities": ["AI 기술 혁신", "디지털 서비스 수요 급증", "정부의 디지털 전환 지원"],
        "risk_weights": [1.2, 1.3, 1.0], "opportunity_weights": [1.5, 1.2, 1.0],
    },
    "식품·외식": {
        "description": "식품 제조, 카페, 외식 브랜드",
        "initial_cash": 100.0, "base_price": 12, "base_demand": 7000,
        "unit_cost": 4.5, "fixed_cost": 18.0, "staff_cost": 2.4,
        "rd_efficiency": 0.85, "ad_efficiency": 1.15,
        "risks": ["원재료 가격 급등", "제품 품질 사고", "유행 변화로 인한 수요 감소"],
        "opportunities": ["인기 메뉴 유행", "원재료 가격 하락", "지역 상권 활성화"],
        "risk_weights": [1.3, 1.1, 1.0], "opportunity_weights": [1.2, 1.2, 1.0],
    },
    "제조·모빌리티": {
        "description": "전자제품, 자동차 부품, 배터리",
        "initial_cash": 100.0, "base_price": 120, "base_demand": 900,
        "unit_cost": 72.0, "fixed_cost": 22.0, "staff_cost": 3.0,
        "rd_efficiency": 1.2, "ad_efficiency": 0.75,
        "risks": ["공급망 중단", "원자재 가격 급등", "생산 설비 고장"],
        "opportunities": ["생산 기술 혁신", "원자재 가격 하락", "해외 신규 수주"],
        "risk_weights": [1.4, 1.3, 1.0], "opportunity_weights": [1.2, 1.3, 1.0],
    },
    "패션·뷰티": {
        "description": "의류, 화장품, 뷰티 브랜드",
        "initial_cash": 100.0, "base_price": 45, "base_demand": 2300,
        "unit_cost": 19.0, "fixed_cost": 15.0, "staff_cost": 2.5,
        "rd_efficiency": 0.9, "ad_efficiency": 1.3,
        "risks": ["유행 급변", "재고 과잉", "경쟁 브랜드의 대규모 할인"],
        "opportunities": ["제품 바이럴 확산", "유명 브랜드 협업", "신규 소비 트렌드"],
        "risk_weights": [1.3, 1.2, 1.0], "opportunity_weights": [1.4, 1.1, 1.3],
    },
    "친환경·에너지": {
        "description": "재생에너지, 친환경 소재, 에너지 효율",
        "initial_cash": 100.0, "base_price": 90, "base_demand": 1000,
        "unit_cost": 55.0, "fixed_cost": 24.0, "staff_cost": 3.0,
        "rd_efficiency": 1.3, "ad_efficiency": 0.8,
        "risks": ["대규모 설비 투자 부담", "정책 지원 축소", "원자재 공급 차질"],
        "opportunities": ["친환경 보조금", "에너지 가격 상승에 따른 수요", "신기술 상용화"],
        "risk_weights": [1.2, 1.0, 1.0], "opportunity_weights": [1.5, 1.2, 1.1],
    },
    "유통·물류": {
        "description": "온라인 쇼핑몰, 배송, 물류 플랫폼",
        "initial_cash": 100.0, "base_price": 28, "base_demand": 4000,
        "unit_cost": 15.0, "fixed_cost": 17.0, "staff_cost": 2.5,
        "rd_efficiency": 0.8, "ad_efficiency": 1.1,
        "risks": ["물류망 마비", "배송비 급등", "온라인 소비 감소"],
        "opportunities": ["온라인 소비 증가", "운송비 하락", "대형 유통 계약"],
        "risk_weights": [1.3, 1.2, 1.0], "opportunity_weights": [1.3, 1.1, 1.2],
    },
}

STYLES = {
    "안정형": {"cash_bonus": 10.0, "demand_mult": 0.96, "risk_mult": 0.78, "rd_mult": 0.85,
             "description": "위험 노출을 낮추고 현금 여력을 확보합니다."},
    "성장형": {"cash_bonus": 0.0, "demand_mult": 1.08, "risk_mult": 1.05, "rd_mult": 1.0,
             "description": "시장 점유율 확대를 우선하지만 변동성도 큽니다."},
    "혁신형": {"cash_bonus": -5.0, "demand_mult": 1.0, "risk_mult": 1.08, "rd_mult": 1.35,
             "description": "연구개발 효과가 크지만 초기 자금 부담이 높습니다."},
}

POSITIVE_EVENTS = [
    {"name": "경기 호황", "description": "소비 심리가 개선되어 시장 수요가 증가합니다.",
     "demand": 0.16, "cost": 0.0, "cash": 0, "type": "positive", "sectors": list(SECTORS)},
    {"name": "정부 지원 정책", "description": "정부 지원 프로그램으로 운영 자금 일부를 지원받습니다.",
     "demand": 0.0, "cost": 0.0, "cash": 12, "type": "positive",
     "sectors": ["IT·인공지능", "친환경·에너지", "제조·모빌리티"]},
    {"name": "기술 혁신", "description": "새로운 기술로 생산성 또는 제품 경쟁력이 개선됩니다.",
     "demand": 0.10, "cost": -0.08, "cash": 0, "type": "positive",
     "sectors": ["IT·인공지능", "제조·모빌리티", "친환경·에너지"]},
    {"name": "바이럴 확산", "description": "온라인에서 제품 화제성이 높아져 수요가 증가합니다.",
     "demand": 0.18, "cost": 0.0, "cash": 0, "type": "positive",
     "sectors": ["패션·뷰티", "식품·외식", "IT·인공지능"]},
    {"name": "원자재 가격 하락", "description": "주요 투입 원가가 하락합니다.",
     "demand": 0.0, "cost": -0.12, "cash": 0, "type": "positive", "sectors": list(SECTORS)},
    {"name": "신규 시장 진출 기회", "description": "새로운 고객층에 접근할 기회가 생깁니다.",
     "demand": 0.13, "cost": 0.0, "cash": -3, "type": "positive", "sectors": list(SECTORS)},
]
NEGATIVE_EVENTS = [
    {"name": "경기 침체", "description": "소비가 위축되어 시장 전체의 수요가 감소합니다.",
