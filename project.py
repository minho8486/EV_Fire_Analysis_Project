import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import plotly.graph_objects as go

plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False
st.set_page_config(layout="wide", page_title="전기차 화재 분석", page_icon="🔥")

# ===== 데이터 불러오기 =====
fire_total = "통합_화재_통계.csv"
fire_EV    = "전기차_화재_통계.csv"
charger    = "전국_충전소_데이터.csv"
car_info   = "자동차_등록_대수_현황.csv"

df_fire_total = pd.read_csv(fire_total, encoding="utf-8-sig")
df_fire_EV    = pd.read_csv(fire_EV, encoding="utf-8-sig")
df_charger    = pd.read_csv(charger, encoding="utf-8-sig")
df_car_info   = pd.read_csv(car_info, encoding="utf-8-sig")

# ===== 전처리 =====
df_fire_total = df_fire_total[df_fire_total["장소소분류"] == "승용자동차"].copy()
df_fire_total["연도"] = pd.to_datetime(df_fire_total["일시"], errors="coerce").dt.year
df_fire_EV["연도"] = pd.to_datetime(df_fire_EV["화재발생일"], errors="coerce").dt.year

# ===== Sidebar 필터 =====
st.sidebar.header("필터링 분석 옵션 (tab2)")

st.sidebar.write("연도 선택")
# 유니크 연도 가져오기
years = sorted(df_fire_EV["연도"].dropna().unique())

# 체크박스로 선택된 연도 모으기
year_filter = []
for y in years:
    if st.sidebar.checkbox(f"{y}년", value=True):  # 기본값 True로 모두 선택
        year_filter.append(y)

# 선택된 연도로 데이터 필터링
df_ev_filtered = df_fire_EV[df_fire_EV["연도"].isin(year_filter)].copy()

region_filter = st.sidebar.multiselect("지역 선택", df_fire_EV["시도"].dropna().unique())
cause_filter  = st.sidebar.multiselect("발화요인 대분류 선택", df_fire_EV["발화요인대분류"].dropna().unique())
subcause_filter = st.sidebar.multiselect("발화요인 소분류 선택", df_fire_EV["발화요인소분류"].dropna().unique())
status_filter = st.sidebar.multiselect("차량상태 선택", df_fire_EV["차량상태"].dropna().unique())

# ===== 필터 적용 데이터 =====
df_ev_filtered = df_fire_EV[df_fire_EV["연도"].isin(year_filter)].copy()
if region_filter:
    df_ev_filtered = df_ev_filtered[df_ev_filtered["시도"].isin(region_filter)]
if status_filter:
    df_ev_filtered = df_ev_filtered[df_ev_filtered["차량상태"].isin(status_filter)]
if cause_filter:
    df_ev_filtered = df_ev_filtered[df_ev_filtered["발화요인대분류"].isin(cause_filter)]
if subcause_filter:
    df_ev_filtered = df_ev_filtered[df_ev_filtered["발화요인소분류"].isin(subcause_filter)]

df_total_filtered = df_fire_total[df_fire_total["연도"].isin(year_filter)].copy()

# ===== 발화요인/차량상태 데이터 =====
ev_fire_cause_all = df_fire_EV["발화요인대분류"].value_counts()
ev_vehicle_status_all = df_fire_EV["차량상태"].value_counts()

# ===== 탭 구조 =====
tab1, tab2, tab3 = st.tabs(["📊 주요 분석", "🔥 전기차 화재 필터링 분석", "📍 지역별 충전소 대비 화재 분석"])

# ===== KPI 카드 스타일 =====
kpi_style = """
<style>
.kpi-card {
    padding: 20px;
    border-radius: 15px;
    color: white;
    text-align: center;
    box-shadow: 2px 2px 12px rgba(0,0,0,0.15);
    margin: 10px;
}
.kpi-title {
    font-size: 16px;
    font-weight: 600;
    margin-bottom: 8px;
}
.kpi-value {
    font-size: 28px;
    font-weight: bold;
}
.kpi-1 { background: linear-gradient(135deg, #6a11cb, #2575fc); }
.kpi-2 { background: linear-gradient(135deg, #fff176, #dd2476); }
.kpi-3 { background: linear-gradient(135deg, #11998e, #38ef7d); }
</style>
"""

# ==============================
# Tab1: 전체 데이터 KPI + Plotly 시각화
# ==============================
with tab1:
    st.markdown("### 🔥 전기차 화재 분석")

    st.markdown(kpi_style, unsafe_allow_html=True)

    # ===== KPI 값 =====
    total_fire_count = len(df_fire_total)
    ev_fire_count = len(df_fire_EV)
    ev_fire_ratio = round(ev_fire_count / total_fire_count * 100, 2)

    # ===== KPI 카드 표시 =====
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"""
        <div class="kpi-card kpi-1">
            <div class="kpi-title">전체 차량 화재 건수</div>
            <div class="kpi-value">{total_fire_count:,} 건</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="kpi-card kpi-2">
            <div class="kpi-title">전기차 화재 건수</div>
            <div class="kpi-value">{ev_fire_count:,} 건</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="kpi-card kpi-3">
            <div class="kpi-title">전기차 화재 비율</div>
            <div class="kpi-value">{ev_fire_ratio}%</div>
        </div>
        """, unsafe_allow_html=True)

    # ===== 연도별 화재 데이터 준비 =====
    yearly_total = df_fire_total.groupby("연도").size()
    yearly_ev = df_fire_EV.groupby("연도").size()
    yearly_ratio = (yearly_ev / yearly_total * 100).round(2)

    # Plotly: 화재 건수 + EV 비율
    fig_fire = go.Figure()
    fig_fire.add_trace(go.Bar(x=yearly_total.index, y=yearly_total.values, name="전체 화재 건수", marker_color="lightgray"))
    fig_fire.add_trace(go.Bar(x=yearly_ev.index, y=yearly_ev.values, name="EV 화재 건수", marker_color="tomato"))
    fig_fire.add_trace(go.Scatter(x=yearly_ratio.index, y=yearly_ratio.values, name="EV 화재 비율 (%)",
                                  mode="lines+markers", yaxis="y2", line=dict(color="green", width=2)))
    fig_fire.update_layout(
        title="연도별 EV 화재 분석 (전체/EV 건수 + 비율)",
        xaxis=dict(title="연도"),
        yaxis=dict(title="화재 건수"),
        yaxis2=dict(title="EV 화재 비율 (%)", overlaying="y", side="right"),
        barmode="group", template="plotly_white"
    )
    st.plotly_chart(fig_fire, use_container_width=True)

    # ===== 자동차 등록 대수 분석 =====
    st.markdown("### 🚗 자동차 등록 대수 분석")
    df_car_info["전기차비율(%)"] = (df_car_info["전기차등록대수"] / df_car_info["전체차량등록대수"] * 100).round(2)

    latest_year = df_car_info["연도"].max()
    latest_data = df_car_info[df_car_info["연도"] == latest_year].iloc[0]

    # ===== 자동차 등록대수 KPI 카드 표시 =====
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"""
        <div class="kpi-card kpi-1">
            <div class="kpi-title">전체 차량 등록대수</div>
            <div class="kpi-value">{latest_data['전체차량등록대수']:,} 대</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="kpi-card kpi-2">
            <div class="kpi-title">전기차 등록대수</div>
            <div class="kpi-value">{latest_data['전기차등록대수']:,} 대</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="kpi-card kpi-3">
            <div class="kpi-title">전기차 등록 비율</div>
            <div class="kpi-value">{latest_data['전기차비율(%)']}%</div>
        </div>
        """, unsafe_allow_html=True)

    # Plotly: 등록대수 + EV 비율
    fig_car = go.Figure()
    fig_car.add_trace(go.Bar(x=df_car_info["연도"], y=df_car_info["전체차량등록대수"], name="전체 차량 등록대수", marker_color="lightblue"))
    fig_car.add_trace(go.Bar(x=df_car_info["연도"], y=df_car_info["전기차등록대수"], name="EV 차량 등록대수", marker_color="orange"))
    fig_car.add_trace(go.Scatter(x=df_car_info["연도"], y=df_car_info["전기차비율(%)"], name="EV 등록 비율 (%)",
                                 mode="lines+markers", yaxis="y2", line=dict(color="darkblue", width=2)))
    fig_car.update_layout(
        title="연도별 자동차 등록대수 및 EV 비율",
        xaxis=dict(title="연도"),
        yaxis=dict(title="등록 대수"),
        yaxis2=dict(title="EV 등록 비율 (%)", overlaying="y", side="right"),
        barmode="group", template="plotly_white"
    )
    st.plotly_chart(fig_car, use_container_width=True)

    # Tab1 분석 인사이트
    st.markdown("### 📌 분석 인사이트")
    st.markdown(f"""
    - 전체 승용차 대비 전기차 화재 비율은 약 **{ev_fire_ratio}%**로 나타났습니다.
    - 연도별 EV 화재 건수는 지속적으로 증가/변동하고 있으며, 최근 연도는 **{yearly_ev.iloc[-1]} 건**으로 나타납니다.
    - 자동차 등록 대수 중 전기차 비율은 꾸준히 증가하여, 최신 연도인 {latest_year}년에는 약 **{latest_data['전기차비율(%)']}%**에 달합니다.
    - 전기차 등록 대수/화재 비율을 보면 전기차라서 화재가 더 많이 발생한다고 단정짓기 어렵습니다.
    - 다만, 전기차 보급이 늘어남에 따라 화재 예방 및 안전 관리의 중요성이 더욱 커지고 있습니다.
    """)


# ==============================
# Tab2: 필터 적용 분석
# ==============================
with tab2:
    st.markdown("### 🔥 전기차 화재 필터링 분석")

 # ===== KPI 카드 =====
    filtered_count = len(df_ev_filtered)
    total_count = len(df_fire_EV)
    filter_ratio = round(filtered_count / total_count * 100, 2)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"""
        <div class="kpi-card kpi-1">
            <div class="kpi-title">전체 EV 화재 건수</div>
            <div class="kpi-value">{total_count:,} 건</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="kpi-card kpi-2">
            <div class="kpi-title">필터 적용 후 건수</div>
            <div class="kpi-value">{filtered_count:,} 건</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="kpi-card kpi-3">
            <div class="kpi-title">필터 후 비율</div>
            <div class="kpi-value">{filter_ratio}%</div>
        </div>
        """, unsafe_allow_html=True)

    # ===== 발화요인 대분류 (가로 막대) =====
    st.markdown("### 🔥 발화요인 대분류별 건수")
    ev_fire_cause_filtered = df_ev_filtered["발화요인대분류"].value_counts()

    fig_cause = go.Figure(go.Bar(
        x=ev_fire_cause_filtered.values,
        y=ev_fire_cause_filtered.index,
        orientation='h',
        text=ev_fire_cause_filtered.values,
        textposition='auto',
        marker_color='tomato'
    ))
    fig_cause.update_layout(
        xaxis_title="건수",
        yaxis_title="발화요인 대분류",
        template="plotly_white",
        height=500
    )
    st.plotly_chart(fig_cause, use_container_width=True)

    # ===== 발화요인 소분류 (Top 10, 가로 막대) =====
    st.markdown("### 🔥 발화요인 소분류별 건수 (Top 10)")
    ev_fire_subcause_filtered = df_ev_filtered["발화요인소분류"].value_counts().head(10)

    if not ev_fire_subcause_filtered.empty:
        fig_subcause = go.Figure(go.Bar(
            x=ev_fire_subcause_filtered.values[::-1],
            y=ev_fire_subcause_filtered.index[::-1],
            orientation='h',
            text=ev_fire_subcause_filtered.values[::-1],
            textposition='auto',
            marker_color='orange'
        ))
        fig_subcause.update_layout(
            xaxis_title="건수",
            yaxis_title="발화요인 소분류 (Top 10)",
            template="plotly_white",
            height=500
        )
        st.plotly_chart(fig_subcause, use_container_width=True)
    else:
        st.info("선택된 필터에 해당하는 데이터가 없습니다.")

    # ===== 차량상태 (도넛 차트) =====
    st.markdown("### 🚗 차량상태별 비율")
    status_counts = df_ev_filtered["차량상태"].value_counts()

    fig_status = go.Figure(go.Pie(
        labels=status_counts.index,
        values=status_counts.values,
        hole=0.4,  # 도넛
        textinfo='percent+label'
    ))
    fig_status.update_layout(
        title="차량상태별 비율 (필터 적용)",
        template="plotly_white",
        height=400
    )
    st.plotly_chart(fig_status, use_container_width=True)

    # ===== 연도별 필터 전/후 비교 =====
    st.markdown("### 📊 연도별 화재 건수 (필터 전 vs 후)")
    total_by_year = df_fire_EV["연도"].value_counts().sort_index() 
    filtered_by_year = df_ev_filtered["연도"].value_counts().sort_index()
    compare_df = pd.DataFrame({
    "연도": total_by_year.index,
    "필터 전": total_by_year.values,
    "필터 후": filtered_by_year.reindex(total_by_year.index, fill_value=0).values
    })

    fig_compare = go.Figure()
    fig_compare.add_trace(go.Bar(
        x=compare_df["연도"], y=compare_df["필터 전"], name="필터 전", marker_color="lightgray", text=compare_df["필터 전"], textposition='outside'
    ))
    fig_compare.add_trace(go.Bar(
        x=compare_df["연도"], y=compare_df["필터 후"], name="필터 후", marker_color="dodgerblue", text=compare_df["필터 후"], textposition='outside'
    ))
    fig_compare.update_layout(
        barmode='group',
        title="연도별 필터 전/후 화재 건수 비교",
        xaxis_title="연도",
        yaxis_title="건수",
        template="plotly_white"
    )
    st.plotly_chart(fig_compare, use_container_width=True)

    # ===== 연도별 필터 후 비율 (라인 그래프) =====
    st.markdown("### 📈 연도별 전체 대비 필터 후 비율 (%)")
    ratio_by_year = (compare_df["필터 후"] / compare_df["필터 전"] * 100).round(2)
    fig_ratio = go.Figure()
    fig_ratio.add_trace(go.Scatter(
        x=compare_df["연도"], y=ratio_by_year,
        mode="lines+markers+text",
        text=ratio_by_year, textposition="top center",
        line=dict(color="green", width=2),
        name="필터 후 비율 (%)"
    ))
    fig_ratio.update_layout(
        title="연도별 전체 대비 필터 후 비율 (%)",
        xaxis_title="연도",
        yaxis_title="비율 (%)",
        template="plotly_white"
    )
    st.plotly_chart(fig_ratio, use_container_width=True)

# ==============================
# Tab3: 지역별 충전소 대비 전기차 화재 비율
# ==============================


with tab3:
    st.markdown("### 📊 지역별 충전소 1,0000대당 전기차 화재 비율 분석")

    # ===== 지역별 EV 화재 건수 & 충전소 수 =====
    ev_region = df_fire_EV["시도"].value_counts()
    charger_region = df_charger["시도"].value_counts().reindex(ev_region.index, fill_value=0)

    # ===== 충전소 10000대당 화재 비율 계산 =====
    fire_per_10000 = (ev_region / charger_region * 10000).round(2)
    fire_per_10000 = fire_per_10000.replace([float("inf"), float("nan")], 0)

    # ===== KPI 카드 =====
    avg_ratio = fire_per_10000.mean().round(2)
    max_region = fire_per_10000.idxmax()
    max_ratio = fire_per_10000.max()

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"""
        <div class="kpi-card kpi-1">
            <div class="kpi-title">전체 지역 평균 화재율</div>
            <div class="kpi-value">{avg_ratio}</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="kpi-card kpi-2">
            <div class="kpi-title">화재율 최고 지역</div>
            <div class="kpi-value">{max_region}</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class="kpi-card kpi-3">
            <div class="kpi-title">최고 화재율 (1,0000대당)</div>
            <div class="kpi-value">{max_ratio}</div>
        </div>
        """, unsafe_allow_html=True)

    # ===== 지역별 전기차 화재 그래프 =====
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=ev_region.values,
        y=ev_region.index,
        orientation="h", 
        text=ev_region.values,
        textposition='outside',
        marker_color='royalblue',
        name='지역별 전기차 화재'
    ))
    fig.update_layout(
        yaxis_title="지역",
        xaxis_title="지역별 전기차 화재 수",
        title="지역별 전기차 화재 수",
        template="plotly_white",
        uniformtext_minsize=8,
        uniformtext_mode='hide'
    )
    st.plotly_chart(fig, use_container_width=True)

    # ===== 전기차 충전기 그래프 =====
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=charger_region.values,
        y=charger_region.index,
        orientation="h",
        text=charger_region.values,
        textposition='outside',
        marker_color='forestgreen',
        name='지역별 전기차 충전기'
    ))
    fig.update_layout(
        yaxis_title="지역",
        xaxis_title="지역별 전기차 충전기 수",
        title="지역별 전기차 충전기 수",
        template="plotly_white",
        uniformtext_minsize=8,
        uniformtext_mode='hide'
    )
    st.plotly_chart(fig, use_container_width=True)

    # ===== Plotly 막대그래프 =====

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=fire_per_10000.index,
        y=fire_per_10000.values,
        text=fire_per_10000.values,
        textposition='outside',
        marker_color='tomato',
        name='화재율'
    ))
    fig.update_layout(
        yaxis_title="충전소 1,0000대당 화재 건수",
        xaxis_title="지역",
        title="지역별 충전소 1,0000대당 전기차 화재 건수",
        template="plotly_white",
        uniformtext_minsize=8,
        uniformtext_mode='hide'
    )
    st.plotly_chart(fig, use_container_width=True)

    # ===== 분석 텍스트 =====
    st.markdown("### 📌 분석 인사이트")
    st.markdown(f"""
    - 평균적으로 충전소 1,0000대당 전기차 화재 건수는 **{avg_ratio}** 수준입니다.  
    - 화재율이 가장 높은 지역은 **{max_region}**으로 **{max_ratio}** 건을 기록했습니다.  
    - 일부 지역은 충전소 수 대비 화재가 집중되어 있어, 안전 관리 및 예방 정책 강화 필요.  
    - 이 시각화를 통해 지역별 안전 정책, 충전소 관리, 화재 예방 전략 수립 가능.
    """)
