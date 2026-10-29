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
     "demand": -0.18, "cost": 0.0, "cash": 0, "type": "negative", "sectors": list(SECTORS)},
    {"name": "원자재 가격 급등", "description": "주요 원자재 가격이 상승해 제품 원가가 증가합니다.",
     "demand": 0.0, "cost": 0.20, "cash": 0, "type": "negative", "sectors": list(SECTORS)},
    {"name": "경쟁사의 가격 인하", "description": "경쟁사가 가격을 낮춰 일부 고객을 빼앗아 갑니다.",
     "demand": -0.14, "cost": 0.0, "cash": 0, "type": "negative", "sectors": list(SECTORS)},
    {"name": "공급망 중단", "description": "부품 또는 상품 공급이 지연되어 판매 가능 물량이 줄어듭니다.",
     "demand": -0.12, "cost": 0.10, "cash": 0, "type": "negative",
     "sectors": ["제조·모빌리티", "유통·물류", "식품·외식"]},
    {"name": "품질·보안 사고", "description": "사고 대응 비용이 발생하고 고객 신뢰도가 하락합니다.",
     "demand": -0.12, "cost": 0.0, "cash": -8, "type": "negative",
     "sectors": ["IT·인공지능", "식품·외식", "제조·모빌리티", "패션·뷰티"]},
    {"name": "금리 상승", "description": "자금 조달 비용이 높아지고 투자가 부담스러워집니다.",
     "demand": -0.04, "cost": 0.0, "cash": -2, "type": "negative", "sectors": list(SECTORS)},
]

def money(value):
    return f"{value:,.1f}백만 원"

def new_game(company_name, sector, style, seed):
    rng = random.Random(seed)
    s = SECTORS[sector]
    style_cfg = STYLES[style]
    cash = s["initial_cash"] + style_cfg["cash_bonus"]
    return {
        "company_name": company_name.strip() or "새로운 기업",
        "sector": sector, "style": style, "seed": seed,
        "quarter": 1, "cash": cash, "debt": 0.0, "market_share": 5.0,
        "trust": 65.0, "morale": 65.0, "quality": 60.0,
        "brand": 45.0, "tech": 35.0, "supply_resilience": 45.0,
        "cumulative_profit": 0.0, "history": [], "events_log": [],
        "event_demand_next": 0.0, "event_cost_next": 0.0,
        "event_capacity_mult": 1.0, "last_event": None,
        "rng_state": rng.getstate(), "game_over": False, "bankrupt": False,
        "last_message": "창업을 시작했습니다. 첫 분기 경영 전략을 선택하세요.",
    }

def pick_event(game, rng):
    sector = game["sector"]
    style = game["style"]
    # Good and bad events are both possible; stability reduces negative event likelihood.
    bad_chance = 0.47 * STYLES[style]["risk_mult"]
    if game["quarter"] >= 7:
        bad_chance += 0.04
    if game["cash"] < 25:
        bad_chance += 0.08
    bad_chance = max(0.22, min(0.72, bad_chance))
    pool = NEGATIVE_EVENTS if rng.random() < bad_chance else POSITIVE_EVENTS
    eligible = [e for e in pool if sector in e["sectors"]]
    event = dict(rng.choice(eligible or pool))
    # Preparedness changes the event's impact.
    if event["type"] == "negative":
        preparedness = 0.0
        if "원자재" in event["name"] or "공급망" in event["name"]:
            preparedness = (game["supply_resilience"] - 45) / 100
        elif "품질" in event["name"] or "보안" in event["name"]:
            preparedness = ((game["quality"] + game["tech"]) / 2 - 45) / 100
        event["demand"] *= max(0.55, min(1.15, 1 - preparedness))
        event["cost"] *= max(0.55, min(1.15, 1 - preparedness))
        event["cash"] *= max(0.5, min(1.0, 1 - max(0, preparedness)))
    return event

def resolve_quarter(game, decision):
    sector = SECTORS[game["sector"]]
    style = STYLES[game["style"]]
    # Use saved RNG state for reproducible, stateful turns.
    rng = random.Random()
    rng.setstate(game["rng_state"])

    event = pick_event(game, rng)
    game["last_event"] = event
    game["events_log"].append({
        "분기": game["quarter"],
        "환경": "기회" if event["type"] == "positive" else "위기",
        "이벤트": event["name"], "설명": event["description"]
    })

    price = float(decision["price"])
    ad = float(decision["ad"])  # million KRW
    rd = float(decision["rd"])  # million KRW
    staff = int(decision["staff"])
    production = float(decision["production"])
    quality_spend = float(decision["quality_spend"])
    supply_spend = float(decision["supply_spend"])
    price_ratio = max(0.45, min(1.8, price / sector["base_price"]))

    # Event effects apply to demand and unit costs; strategy changes brand/tech/resilience.
    demand_mult = style["demand_mult"] * (1 + event["demand"])
    ad_effect = 1 + sector["ad_efficiency"] * math.log1p(ad) * 0.045
    brand_effect = 0.80 + game["brand"] / 250
    tech_effect = 0.90 + game["tech"] / 400
    price_elasticity = 1.15
    price_effect = price_ratio ** (-price_elasticity)
    trend_noise = rng.uniform(-0.06, 0.06)
    demand = sector["base_demand"] * demand_mult * ad_effect * brand_effect * tech_effect * price_effect * (1 + trend_noise)
    demand = max(0, demand)

    unit_cost = sector["unit_cost"] * (1 + event["cost"])
    # R&D creates gradual technology benefits, not instant guaranteed returns.
    tech_gain = rd * sector["rd_efficiency"] * (0.20 if game["style"] != "혁신형" else 0.27)
    game["tech"] = min(100, game["tech"] + tech_gain - 0.6)
    unit_cost *= max(0.72, 1 - game["tech"] / 1200)
    capacity = sector["base_demand"] * (0.48 + staff * 0.075) * (1 + game["tech"] / 500)
    capacity *= game["event_capacity_mult"]
    sold = min(demand, capacity, sector["base_demand"] * production)
    revenue = sold * price / 1000.0  # million KRW
    variable_cost = sold * unit_cost / 1000.0
    staff_cost = staff * sector["staff_cost"]
    fixed_cost = sector["fixed_cost"]
    event_cost_cash = float(event.get("cash", 0))
    quality_cost = quality_spend
    supply_cost = supply_spend
    total_cost = variable_cost + staff_cost + fixed_cost + ad + rd + quality_cost + supply_cost
    profit = revenue - total_cost
    # Avoid negative cash from an unrealistic free credit line; any deficit is financed as debt.
    new_cash = game["cash"] + profit + event_cost_cash
    if new_cash < 0:
        game["debt"] += abs(new_cash)
        new_cash = 0.0
    game["cash"] = new_cash
    game["cumulative_profit"] += profit + event_cost_cash

    # Strategic investment effects
    game["brand"] = max(0, min(100, game["brand"] + ad * 0.18 + (2 if event["name"] == "바이럴 확산" else 0) - 1.2))
    game["quality"] = max(0, min(100, game["quality"] + quality_spend * 0.6 + rd * 0.08 - 1.0))
    game["supply_resilience"] = max(0, min(100, game["supply_resilience"] + supply_spend * 0.75 - 0.7))
    game["morale"] = max(0, min(100, game["morale"] + (1.0 if staff >= 5 else -1.5) - (2.0 if profit < 0 else 0)))
    trust_delta = 0.4 if profit >= 0 else -1.2
    if "품질" in event["name"] or "보안" in event["name"]:
        trust_delta -= 7
    if quality_spend >= 5:
        trust_delta += 1.5
    game["trust"] = max(0, min(100, game["trust"] + trust_delta))

    # Market share responds to demand capture, brand, quality, and the event.
    capture = sold / max(1, demand)
    share_change = (capture - 0.72) * 5 + (game["brand"] - 45) * 0.018 + (game["quality"] - 60) * 0.012
    if event["name"] == "경쟁사의 가격 인하":
        share_change -= 1.5
    if event["name"] == "신규 시장 진출 기회":
        share_change += 0.7
    game["market_share"] = max(0.1, min(70, game["market_share"] + share_change))
    game["rng_state"] = rng.getstate()

    row = {
        "분기": game["quarter"], "매출(백만 원)": round(revenue, 2),
        "총비용(백만 원)": round(total_cost, 2), "순이익(백만 원)": round(profit + event_cost_cash, 2),
        "현금(백만 원)": round(game["cash"], 2), "부채(백만 원)": round(game["debt"], 2),
        "시장 점유율(%)": round(game["market_share"], 2),
        "고객 신뢰도": round(game["trust"], 1), "기술력": round(game["tech"], 1),
        "브랜드 가치": round(game["brand"], 1), "판매량": int(sold),
        "이벤트": event["name"],
    }
    game["history"].append(row)
    game["last_message"] = (
        f"{game['quarter']}분기 종료: 매출 {money(revenue)}, "
        f"순이익 {money(profit + event_cost_cash)}. "
        f"{event['name']} 이벤트가 발생했습니다."
    )
    game["quarter"] += 1
    if game["cash"] <= 0 and game["debt"] > 60:
        game["bankrupt"] = True
        game["game_over"] = True
        game["last_message"] += " 부채가 감당하기 어려운 수준에 도달해 파산했습니다."
    elif game["quarter"] > 10:
        game["game_over"] = True
        game["last_message"] += " 10분기 경영이 종료되었습니다."
    return game

def reset_to_setup():
    for key in ["game", "setup_done"]:
        st.session_state.pop(key, None)

# ----------------------------
# Session state
# ----------------------------
if "game" not in st.session_state:
    st.session_state.game = None

st.markdown("""
<style>
.main-title {font-size:2.4rem;font-weight:800;letter-spacing:-0.04em;}
.sub-title {color:#9CA3AF;margin-top:-8px;}
.event-box {padding:1rem;border-radius:0.75rem;border:1px solid rgba(128,128,128,.3);}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">🏢 CEO Simulator</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">변화하는 시장에서 10분기 동안 기업을 경영하세요. 모든 데이터와 사건은 게임용 가상 모델입니다.</div>', unsafe_allow_html=True)
st.divider()

game = st.session_state.game

if game is None:
    st.subheader("🚀 나만의 기업 창업하기")
    with st.form("setup_form"):
        col1, col2 = st.columns(2)
        with col1:
            company_name = st.text_input("기업 이름", value="넥스트웨이브")
            sector = st.selectbox("사업 분야", list(SECTORS.keys()), format_func=lambda x: f"{x} — {SECTORS[x]['description']}")
            st.info(f"**업종 특징:** {SECTORS[sector]['description']}\n\n**주요 위험:** {', '.join(SECTORS[sector]['risks'])}\n\n**기회 이벤트:** {', '.join(SECTORS[sector]['opportunities'])}")
        with col2:
            style = st.radio("경영 스타일", list(STYLES.keys()), horizontal=False)
            st.caption(STYLES[style]["description"])
            seed = st.number_input("게임 시드 (같은 번호로 비슷한 환경 재현)", min_value=1, max_value=999999, value=2026, step=1)
            st.caption("초기 자본금은 경영 스타일에 따라 달라집니다. 단위는 백만 원입니다.")
        start = st.form_submit_button("기업 설립하고 게임 시작", type="primary", use_container_width=True)
        if start:
            st.session_state.game = new_game(company_name, sector, style, int(seed))
            st.rerun()
    st.markdown("### 🎮 게임 방법")
    c1, c2, c3 = st.columns(3)
    c1.metric("게임 기간", "10분기")
    c2.metric("사업 분야", "6개")
    c3.metric("환경 변화", "기회 + 위기")
    st.markdown("**전략 팁:** 광고는 브랜드와 수요에, 연구개발은 장기 기술력에, 품질 투자는 고객 신뢰도에, 공급망 투자는 공급 충격 완화에 영향을 줍니다.")
    st.stop()

game = st.session_state.game
sector_data = SECTORS[game["sector"]]
style_data = STYLES[game["style"]]

with st.sidebar:
    st.header("🏢 기업 정보")
    st.write(f"**{game['company_name']}**")
    st.write(f"{game['sector']} · {game['style']}")
    st.metric("진행 상황", "종료" if game["game_over"] else f"{min(game['quarter'], 10)}/10 분기")
    st.metric("현금", money(game["cash"]))
    st.metric("누적 부채", money(game["debt"]))
    st.metric("시장 점유율", f"{game['market_share']:.1f}%")
    st.progress(min(1.0, max(0.0, (game["quarter"] - 1) / 10)))
    if st.button("새 게임 시작", use_container_width=True):
        reset_to_setup()
        st.rerun()
    st.caption("주의: 가상 경영 시뮬레이션이며 실제 투자·사업 예측 자료가 아닙니다.")

# Top-level metrics
m1, m2, m3, m4 = st.columns(4)
m1.metric("보유 현금", money(game["cash"]))
m2.metric("시장 점유율", f"{game['market_share']:.1f}%")
m3.metric("고객 신뢰도", f"{game['trust']:.0f}/100")
m4.metric("기술력", f"{game['tech']:.0f}/100")

tabs = st.tabs(["📊 경영 대시보드", "🧭 분기 경영", "🌦️ 환경 이벤트", "📑 최종 보고서"])

with tabs[0]:
    st.subheader("기업 성과 대시보드")
    if game["history"]:
        df = pd.DataFrame(game["history"])
        a, b = st.columns(2)
        with a:
            fig = px.line(df, x="분기", y=["매출(백만 원)", "총비용(백만 원)"], markers=True,
                          title="분기별 매출과 비용")
            st.plotly_chart(fig, use_container_width=True)
        with b:
            fig = px.bar(df, x="분기", y="순이익(백만 원)", color="순이익(백만 원)",
                         title="분기별 순이익")
            st.plotly_chart(fig, use_container_width=True)
        c, d = st.columns(2)
        with c:
            fig = px.line(df, x="분기", y="시장 점유율(%)", markers=True, title="시장 점유율 변화")
            st.plotly_chart(fig, use_container_width=True)
        with d:
            fig = px.line(df, x="분기", y=["고객 신뢰도", "기술력", "브랜드 가치"], markers=True,
                          title="비재무 지표 변화")
            st.plotly_chart(fig, use_container_width=True)
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("첫 분기 경영을 완료하면 실적 그래프가 표시됩니다.")

with tabs[1]:
    st.subheader("🧭 분기 경영 회의")
    if game["game_over"]:
        if game["bankrupt"]:
            st.error("기업이 파산했습니다. 새 게임으로 다른 전략을 시험해 보세요.")
        else:
            st.success("10분기 경영을 완료했습니다. 최종 보고서 탭에서 결과를 확인하세요.")
    else:
        st.write(f"**{game['quarter']}분기** — 이번 분기의 경영 결정을 선택하세요.")
        with st.form(f"decision_{game['quarter']}"):
            col1, col2 = st.columns(2)
            with col1:
                price = st.slider("제품 가격 (업종 기준 가격 주변)", min_value=int(sector_data["base_price"] * 0.5),
                                  max_value=int(sector_data["base_price"] * 1.6),
                                  value=int(sector_data["base_price"]), step=max(1, int(sector_data["base_price"] * 0.05)))
                ad = st.slider("광고비 (백만 원)", 0, 30, 8, 1)
                rd = st.slider("연구개발비 (백만 원)", 0, 30, 8, 1)
            with col2:
                staff = st.slider("직원 수", 1, 15, 5, 1)
                production = st.slider("생산·서비스 제공 수준", 0.4, 1.4, 1.0, 0.05,
                                       help="기준 수요 대비 생산·서비스 제공 가능량의 비율입니다.")
                quality_spend = st.slider("품질·보안 투자 (백만 원)", 0, 12, 3, 1)
                supply_spend = st.slider("공급망 안정화 투자 (백만 원)", 0, 12, 2, 1)
            st.caption("비용은 백만 원 단위입니다. 지나친 지출은 현금 부족과 부채로 이어질 수 있습니다.")
            submitted = st.form_submit_button("분기 마감 및 결과 확인", type="primary", use_container_width=True)
            if submitted:
                decision = {"price": price, "ad": ad, "rd": rd, "staff": staff,
                            "production": production, "quality_spend": quality_spend,
                            "supply_spend": supply_spend}
                st.session_state.game = resolve_quarter(game, decision)
                st.rerun()
        if game["history"]:
            st.info(game["last_message"])

with tabs[2]:
    st.subheader("🌦️ 환경 이벤트 기록")
    st.write("좋은 기회와 위기가 업종, 기업의 준비 상태, 경영 스타일에 따라 다르게 작용합니다.")
    if game["events_log"]:
        events_df = pd.DataFrame(game["events_log"])
        for _, row in events_df.iloc[::-1].iterrows():
            if row["환경"] == "기회":
                st.success(f"**{row['분기']}분기 · 기회: {row['이벤트']}**\n\n{row['설명']}")
            else:
                st.warning(f"**{row['분기']}분기 · 위기: {row['이벤트']}**\n\n{row['설명']}")
        st.dataframe(events_df, use_container_width=True, hide_index=True)
    else:
        st.info("첫 분기 마감 후 이벤트가 기록됩니다.")

with tabs[3]:
    st.subheader("📑 CEO 최종 평가")
    if not game["game_over"]:
        st.info("10분기 경영을 마치면 최종 평가와 경영 분석이 표시됩니다.")
    else:
        if game["history"]:
            df = pd.DataFrame(game["history"])
            total_profit = float(df["순이익(백만 원)"].sum())
            final_cash = game["cash"]
            final_share = game["market_share"]
            score = max(0, min(100, 35 + total_profit * 0.22 + final_share * 0.35
                               + game["trust"] * 0.12 + game["tech"] * 0.08
                               - game["debt"] * 0.25))
            if game["bankrupt"]:
                grade = "파산 — 경영 전략 전면 재검토 필요"
            elif score >= 82:
                grade = "S — 탁월한 경영 성과"
            elif score >= 68:
                grade = "A — 우수한 경영 성과"
            elif score >= 52:
                grade = "B — 성장 가능성 있음"
            elif score >= 35:
                grade = "C — 수익성 개선 필요"
            else:
                grade = "D — 재무 안정성 위기"
            x1, x2, x3 = st.columns(3)
            x1.metric("최종 CEO 점수", f"{score:.0f}/100")
            x2.metric("누적 순이익", money(total_profit))
            x3.metric("최종 현금", money(final_cash))
            st.markdown(f"### 평가: {grade}")
            best = df.loc[df["순이익(백만 원)"].idxmax()]
            worst = df.loc[df["순이익(백만 원)"].idxmin()]
            st.markdown("#### 경영 분석")
            st.write(f"- 가장 높은 순이익: {int(best['분기'])}분기 ({money(float(best['순이익(백만 원)']))})")
            st.write(f"- 가장 낮은 순이익: {int(worst['분기'])}분기 ({money(float(worst['순이익(백만 원)']))})")
            st.write(f"- 최종 시장 점유율: {final_share:.1f}%")
            st.write(f"- 최종 고객 신뢰도: {game['trust']:.0f}/100")
            st.write(f"- 최종 기술력: {game['tech']:.0f}/100")
            if game["debt"] > 0:
                st.warning("누적 부채가 발생했습니다. 다음 플레이에서는 비용 구조와 현금 여유를 더 신중히 관리해 보세요.")
            if game["trust"] < 40:
                st.warning("고객 신뢰도가 낮습니다. 품질·보안 투자와 고객 대응을 강화하는 전략을 시험해 보세요.")
            if game["tech"] < 40:
                st.info("기술력이 낮은 편입니다. 연구개발 투자의 장기 효과를 비교해 보세요.")
            st.markdown("#### 이벤트와 성과")
            st.dataframe(df[["분기", "이벤트", "매출(백만 원)", "순이익(백만 원)", "시장 점유율(%)"]], use_container_width=True, hide_index=True)
            csv = df.to_csv(index=False).encode("utf-8-sig")
            st.download_button("경영 실적 CSV 다운로드", data=csv, file_name="ceo_simulator_report.csv", mime="text/csv")
        else:
            st.info("기록된 분기 실적이 없습니다.")

st.divider()
st.caption("CEO Simulator · 교육용 가상 시뮬레이션. 실제 기업의 성과나 시장 상황을 예측하지 않습니다.")
