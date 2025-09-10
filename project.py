import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go

plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False
st.set_page_config(layout="wide", page_title="전기차 화재 분석", page_icon="🔥")

# ===== 데이터 불러오기 =====
fire_total = "통합_화재_통계_2021-2023.csv"
fire_EV    = "전기차_화재_통계.csv"
charger    = "전국_충전소_데이터.csv"
car_info   = "자동차_등록_대수_대수_현황.csv"

df_fire_total = pd.read_csv(fire_total, encoding="utf-8-sig")
df_fire_EV    = pd.read_csv(fire_EV, encoding="utf-8-sig")
df_charger    = pd.read_csv(charger, encoding="utf-8-sig")
df_car_info   = pd.read_csv(car_info, encoding="utf-8-sig")

# ===== 전처리 =====
df_fire_total = df_fire_total[df_fire_total["장소소분류"] == "승용자동차"].copy()
df_fire_total["연도"] = pd.to_datetime(df_fire_total["일시"], errors="coerce").dt.year
df_fire_EV["연도"] = pd.to_datetime(df_fire_EV["화재발생일"], errors="coerce").dt.year


# ===== Sidebar 필터 =====
st.sidebar.header("필터")
show_all_years = st.sidebar.checkbox("전체 데이터 보기", value=True)
if show_all_years:
    year_filter = sorted(df_fire_EV["연도"].dropna().unique())
else:
    year_filter = st.sidebar.multiselect(
        "연도 선택",
        options=sorted(df_fire_EV["연도"].dropna().unique()),
        default=sorted(df_fire_EV["연도"].dropna().unique())
    )

region_filter = st.sidebar.multiselect("시도 선택", df_fire_EV["시도"].dropna().unique())
status_filter = st.sidebar.multiselect("차량상태 선택", df_fire_EV["차량상태"].dropna().unique())
cause_filter  = st.sidebar.multiselect("발화요인 선택", df_fire_EV["발화요인대분류"].dropna().unique())
subcause_filter = st.sidebar.multiselect("발화요인 소분류 선택", df_fire_EV["발화요인소분류"].dropna().unique())

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
tab1, tab2 = st.tabs(["📊 주요 분석 (전체)", "🔥 발화요인 & 차량상태 (필터 적용)"])

# ==============================
# Tab1: 전체 데이터 KPI + 분석 (대시보드형)
# ==============================
with tab1:
    st.markdown("## 🔥 전기차 화재 대시보드 (전체 데이터 기준)")

    # ===== KPI 카드 =====
    total_fire_count = len(df_fire_total)
    ev_fire_count = len(df_fire_EV)
    ev_fire_ratio = round(ev_fire_count / total_fire_count * 100, 2)

    kpi_col1, kpi_col2, kpi_col3 = st.columns(3)
    kpi_col1.metric("전체 차량 화재 건수", total_fire_count, delta=None)
    kpi_col2.metric("전기차 화재 건수", ev_fire_count, delta=None)
    kpi_col3.metric("전기차 화재 비율 (%)", f"{ev_fire_ratio}%", delta=None)

    # ===== 누적 화재 추세 (Plotly Interactive) =====
    st.markdown("### 📈 연도별 누적 화재 건수")
    df_cum_ev = df_fire_EV.groupby("연도").size().cumsum().reset_index(name="EV 누적")
    df_cum_total = df_fire_total.groupby("연도").size().cumsum().reset_index(name="전체 누적")
    fig_cum = go.Figure()
    fig_cum.add_trace(go.Scatter(x=df_cum_ev["연도"], y=df_cum_ev["EV 누적"],
                                 mode='lines+markers', name="전기차 누적", line=dict(color='red')))
    fig_cum.add_trace(go.Scatter(x=df_cum_total["연도"], y=df_cum_total["전체 누적"],
                                 mode='lines+markers', name="전체 승용차 누적", line=dict(color='blue')))
    fig_cum.update_layout(xaxis_title="연도", yaxis_title="누적 화재 건수", template="plotly_white")
    st.plotly_chart(fig_cum, use_container_width=True)

    # ===== 연도별 EV vs 전체 비율 =====
    st.markdown("### ⚖️ 연도별 전기차 화재 비율 (%)")
    ev_by_year = df_fire_EV.groupby("연도").size()
    total_by_year = df_fire_total.groupby("연도").size()
    ratio = (ev_by_year / total_by_year * 100).round(2)
    fig_ratio = px.bar(x=ratio.index, y=ratio.values, text=ratio.values, labels={"x":"연도","y":"비율 (%)"})
    fig_ratio.update_traces(texttemplate="%{text}%", textposition="outside", marker_color="salmon")
    st.plotly_chart(fig_ratio, use_container_width=True)

    # ===== 충전소 vs 화재 건수 =====
    st.markdown("### 🔌 지역별 충전소 개수 vs 전기차 화재 건수")
    ev_region = df_fire_EV["시도"].value_counts()
    charger_region = df_charger["시도"].value_counts().reindex(ev_region.index)
    fig, ax = plt.subplots(figsize=(8,6))
    sns.regplot(x=charger_region, y=ev_region, ax=ax, scatter_kws={"s":100, "color":"purple"})
    ax.set_xlabel("충전소 개수")
    ax.set_ylabel("EV 화재 건수")
    ax.set_title("충전소 개수 vs EV 화재 건수")
    st.pyplot(fig)

    # ===== Top-N 지역/발화요인 =====
    st.markdown("### 🏆 Top-5 분석")
    top_col1, top_col2 = st.columns(2)
    with top_col1:
        st.markdown("#### 🔝 화재율 높은 지역")
        st.table(ev_region.head(5))
    with top_col2:
        st.markdown("#### 🔝 주요 발화 요인")
        st.table(df_fire_EV["발화요인대분류"].value_counts().head(5))

# ==============================
# Tab2: 필터 적용 분석
# ==============================
with tab2:
    st.markdown("## 🔥 필터 적용 전기차 화재 분석")

    # 발화요인 대분류
    col3, col4, col5 = st.columns(3)
    with col3:
        st.markdown("### 발화요인 대분류")
        fig, ax = plt.subplots(figsize=(6,4))
        ev_fire_cause_all.plot(kind="bar", ax=ax, color="skyblue")
        ax.set_ylabel("건수")
        ax.set_xlabel("발화요인 대분류")
        ax.set_title("발화요인 대분류별 화재 건수")
        st.pyplot(fig)

    # 발화요인 소분류
    with col4:
        st.markdown("### 발화요인 소분류")
        ev_fire_subcause_filtered = df_ev_filtered["발화요인소분류"].value_counts()
        if not ev_fire_subcause_filtered.empty:
            fig, ax = plt.subplots(figsize=(6,4))
            ev_fire_subcause_filtered.plot(kind="bar", ax=ax, color="salmon")
            ax.set_ylabel("건수")
            ax.set_xlabel("발화요인 소분류")
            ax.set_title("발화요인 소분류별 화재 건수")
            st.pyplot(fig)
        else:
            st.write("선택된 필터에 해당하는 데이터가 없습니다.")

    # 차량상태
    with col5:
        st.markdown("### 차량상태")
        fig, ax = plt.subplots(figsize=(6,4))
        ev_vehicle_status_all.plot(kind="bar", ax=ax, color="lightgreen")
        ax.set_ylabel("건수")
        ax.set_xlabel("차량상태")
        ax.set_title("차량상태별 화재 건수")
        st.pyplot(fig)

    # 연도별 필터 전/후 비교
    st.markdown("### 📊 연도별 필터 전 vs 후 화재 건수 비교")
    total_by_year = df_fire_EV["연도"].value_counts().sort_index()
    filtered_by_year = df_ev_filtered["연도"].value_counts().sort_index()
    compare_df = pd.DataFrame({
        "연도": total_by_year.index,
        "필터 전": total_by_year.values,
        "필터 후": filtered_by_year.reindex(total_by_year.index, fill_value=0).values
    })
    fig, ax = plt.subplots(figsize=(10,6))
    compare_df.set_index("연도")[["필터 전","필터 후"]].plot(kind="bar", ax=ax, color=["lightgray","dodgerblue"])
    ax.set_title("연도별 필터 전/후 화재 건수 비교")
    ax.set_ylabel("건수")
    ax.legend(title="구분")
    st.pyplot(fig)

    # 연도별 전체 대비 필터 후 비율
    st.markdown("### 📊 연도별 전체 대비 필터 후 비율 (%)")
    ratio_by_year = (compare_df["필터 후"] / compare_df["필터 전"] * 100).round(2)
    fig, ax = plt.subplots(figsize=(10,6))
    sns.barplot(x=compare_df["연도"], y=ratio_by_year, palette="Blues_d", ax=ax)
    for i, v in enumerate(ratio_by_year.values):
        ax.text(i, v+0.5, f"{v}%", ha="center", fontsize=9)
    ax.set_title("연도별 전체 대비 필터 후 비율 (%)")
    ax.set_xlabel("연도")
    ax.set_ylabel("비율 (%)")
    st.pyplot(fig)
