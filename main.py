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
