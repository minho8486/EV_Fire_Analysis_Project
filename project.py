import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import plotly.express as px

plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False
st.set_page_config(layout="wide", page_title="전기차 화재 분석", page_icon="🔥")

# ===== 데이터 불러오기 =====
fire_total = "통합_화재_통계.csv"
fire_EV    = "전기차_화재_통계.csv"
car_info   = "자동차_등록_대수_현황.csv"
car_maker  = "차종별_전기차_화재.csv"
foreign_fire = "해외_전기차_화재.csv"
manufac_fire = "전기차_제조사_점유율_화재.csv"

df_fire_total = pd.read_csv(fire_total, encoding="utf-8-sig")
df_fire_EV    = pd.read_csv(fire_EV, encoding="utf-8-sig")
df_car_info   = pd.read_csv(car_info, encoding="utf-8-sig")
df_car_maker  = pd.read_csv(car_maker, encoding="utf-8-sig")
df_foreign_fire = pd.read_csv(foreign_fire, encoding="utf-8-sig")
df_manufac_fire = pd.read_csv(manufac_fire, encoding="utf-8-sig")

# ===== 전처리 =====
df_fire_total = df_fire_total[df_fire_total["장소소분류"].isin(["승용자동차", "화물자동차", "버스"])].copy()
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

subcause_filter = st.sidebar.multiselect("발화요인 선택", df_fire_EV["발화요인소분류"].dropna().unique())
status_filter = st.sidebar.multiselect("차량상태 선택", df_fire_EV["차량상태"].dropna().unique())

# ===== 필터 적용 데이터 =====
df_ev_filtered = df_fire_EV[df_fire_EV["연도"].isin(year_filter)].copy()
if status_filter:
    df_ev_filtered = df_ev_filtered[df_ev_filtered["차량상태"].isin(status_filter)]
if subcause_filter:
    df_ev_filtered = df_ev_filtered[df_ev_filtered["발화요인소분류"].isin(subcause_filter)]

df_total_filtered = df_fire_total[df_fire_total["연도"].isin(year_filter)].copy()

# ===== 발화요인/차량상태 데이터 =====
ev_fire_cause_all = df_fire_EV["발화요인대분류"].value_counts()
ev_vehicle_status_all = df_fire_EV["차량상태"].value_counts()

# ===== 탭 구조 =====
tab1, tab2, tab3 = st.tabs(["📊 주요 분석", "🔥 전기차 화재 필터링 분석", "📍 추가 참고 분석 데이터"])

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
    df_fire_count = (
        df_fire_total.groupby("연도").size().reset_index(name="전체")
        .merge(df_fire_EV.groupby("연도").size().reset_index(name="EV"), on="연도", how="left")
    )
    df_fire_count["EV"] = df_fire_count["EV"].fillna(0).astype(int)
    df_fire_count["비EV"] = df_fire_count["전체"] - df_fire_count["EV"]
    df_fire_count["EV비율(%)"] = (df_fire_count["EV"] / df_fire_count["전체"] * 100).round(2)

    # 🔥 화재 건수 시각화 (100% stacked + EV 비율 선)
    fig_fire = go.Figure()
    fig_fire.add_trace(go.Bar(
        x=df_fire_count["연도"],
        y=df_fire_count["EV"],
        name="EV 화재 건수",
        marker_color="tomato"
    ))
    fig_fire.add_trace(go.Bar(
        x=df_fire_count["연도"],
        y=df_fire_count["비EV"],
        name="비EV 화재 건수",
        marker_color="lightgray"
    ))
    fig_fire.add_trace(go.Scatter(
        x=df_fire_count["연도"],
        y=df_fire_count["EV비율(%)"],
        name="EV 화재 비율 (%)",
        mode="lines+markers",
        line=dict(color="green", width=2),
        yaxis="y2"
    ))
    fig_fire.update_layout(
        title="연도별 EV vs 비EV 화재 비율 (100% Stacked + EV 비율 선)",
        xaxis=dict(title="연도"),
        yaxis=dict(title="비율 (%)", range=[0, 100]),
        yaxis2=dict(title="EV 화재 비율 (%)", overlaying="y", side="right"),
        barmode="stack",
        barnorm="percent",   # ✅ 전체를 100%로 정규화
        template="plotly_white",
        height=500
    )
    st.plotly_chart(fig_fire, use_container_width=True)


    # ===== 자동차 등록 대수 분석 =====
    st.markdown("### 🚗 자동차 등록 대수 분석")
    df_car_info["전기차비율(%)"] = (df_car_info["전기차등록대수"] / df_car_info["전체차량등록대수"] * 100).round(2)
    df_car_info["비EV등록대수"] = df_car_info["전체차량등록대수"] - df_car_info["전기차등록대수"]

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

    # 🚗 등록대수 시각화 (100% stacked + EV 등록 비율 선)
    fig_car = go.Figure()
    fig_car.add_trace(go.Bar(
        x=df_car_info["연도"],
        y=df_car_info["전기차등록대수"],
        name="EV 차량 등록대수",
        marker_color="orange"
    ))
    fig_car.add_trace(go.Bar(
        x=df_car_info["연도"],
        y=df_car_info["비EV등록대수"],
        name="비EV 차량 등록대수",
        marker_color="lightblue"
    ))
    fig_car.add_trace(go.Scatter(
        x=df_car_info["연도"],
        y=df_car_info["전기차비율(%)"],
        name="EV 등록 비율 (%)",
        mode="lines+markers",
        line=dict(color="#98df8a", width=2),
        yaxis="y2"
    ))
    fig_car.update_layout(
        title="연도별 EV vs 비EV 등록 비율 (100% Stacked + EV 비율 선)",
        xaxis=dict(title="연도"),
        yaxis=dict(title="비율 (%)", range=[0, 100]),
        yaxis2=dict(title="EV 등록 비율 (%)", overlaying="y", side="right"),
        barmode="stack",
        barnorm="percent",   # ✅ 전체를 100%로 정규화
        template="plotly_white",
        height=500
    )
    st.plotly_chart(fig_car, use_container_width=True)


    st.markdown("### 🔥 10만대당 화재 건수 비교")

    # 연도별 등록대수, 화재건수
    df_car_info = df_car_info.set_index("연도")

    # 전기차 등록대수 & 화재건수
    ev_registered = df_car_info["전기차등록대수"]
    ev_fire_by_year = df_fire_EV.groupby("연도").size()

    # 내연기관 등록대수 & 화재건수
    ice_registered = df_car_info["전체차량등록대수"] - ev_registered
    ice_fire_by_year = df_fire_total.groupby("연도").size() - ev_fire_by_year

    # 10만대당 화재 건수 계산
    ev_fire_per_100k = (ev_fire_by_year / ev_registered * 100000).round(2)
    ice_fire_per_100k = (ice_fire_by_year / ice_registered * 100000).round(2)

    # 전기차 시각화
    fig_ev = go.Figure()
    fig_ev.add_trace(go.Bar(
        x=ev_registered.index,
        y=ev_registered.values,
        name="EV 등록대수",
        marker_color="royalblue",
        yaxis="y1"
    ))
    fig_ev.add_trace(go.Scatter(
        x=ev_fire_per_100k.index,
        y=ev_fire_per_100k.values,
        name="EV 화재 (10만대당 건수)",
        mode="lines+markers",
        marker_color="tomato",
        yaxis="y2"
    ))
    fig_ev.update_layout(
        title="연도별 전기차 등록대수 & 10만대당 화재 건수",
        xaxis_title="연도",
        yaxis=dict(title="EV 등록대수", side="left"),
        yaxis2=dict(title="10만대당 화재 건수", overlaying="y", side="right"),
        template="plotly_white"
    )
    st.plotly_chart(fig_ev, use_container_width=True)

    # 내연기관 시각화
    fig_ice = go.Figure()
    fig_ice.add_trace(go.Bar(
        x=ice_registered.index,
        y=ice_registered.values,
        name="내연기관 등록대수",
        marker_color="seagreen",
        yaxis="y1"
    ))
    fig_ice.add_trace(go.Scatter(
        x=ice_fire_per_100k.index,
        y=ice_fire_per_100k.values,
        name="내연기관 화재 (10만대당 건수)",
        mode="lines+markers",
        marker_color="orange",
        yaxis="y2"
    ))
    fig_ice.update_layout(
        title="연도별 내연기관 등록대수 & 10만대당 화재 건수",
        xaxis_title="연도",
        yaxis=dict(title="내연기관 등록대수", side="left"),
        yaxis2=dict(title="10만대당 화재 건수", overlaying="y", side="right"),
        template="plotly_white"
    )
    st.plotly_chart(fig_ice, use_container_width=True)

    # Tab1 분석 인사이트
    st.markdown("### 📌 분석 인사이트")
    


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
            <div class="kpi-title">전기차 총 화재 건수</div>
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
            <div class="kpi-title">필터데이터/전체 비율</div>
            <div class="kpi-value">{filter_ratio}%</div>
        </div>
        """, unsafe_allow_html=True)

    # ===== 발화요인 소분류 =====
    st.markdown("### 🔥 화재별 발화요인")

    ev_fire_subcause_filtered = df_ev_filtered["발화요인소분류"].value_counts().sort_values(ascending=True)
    if not ev_fire_subcause_filtered.empty:
        fig_subcause = go.Figure(go.Bar(
            x=ev_fire_subcause_filtered.values,
            y=ev_fire_subcause_filtered.index,
            orientation='h',
            text=ev_fire_subcause_filtered.values,
            textposition='auto',
            marker_color='orange'
        ))
        fig_subcause.update_layout(
            xaxis_title="총량",
            yaxis_title="발화요인",
            template="plotly_white",
            height=600
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
    st.markdown("### 📈 연도별 필터 후/전체 비율 (%)")
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
    # 시각화용 데이터
    manufacturer_counts = df_car_maker["제조사"].value_counts()
    fire_origin_counts = df_car_maker["최초발화점"].value_counts()
    situation_counts = df_car_maker["상황"].value_counts()

    total_counts = len(df_car_maker)
    filtered_df = df_car_maker[(df_car_maker["최초발화점"] == "고전압배터리") & (df_car_maker["상황"] != "주행중(충돌)")]
    filter_count = len(filtered_df)
    filter_m_ratio = round(filter_count / total_counts * 100, 2)

    # 추가자료 시각화
    st.markdown("### 🔥 전기차 제조사별 화재")

    fig_subcause = go.Figure(go.Bar(
        x=manufacturer_counts.index,
        y=manufacturer_counts.values,
        text=manufacturer_counts.values,
        textposition='auto',
        marker_color='orange'
    ))
    fig_subcause.update_layout(
        xaxis_title="제조사",
        yaxis_title="건수",
        template="plotly_white",
        height=500
    )
    st.plotly_chart(fig_subcause, use_container_width=True)

    st.markdown("### 🚗 최초 발화점 비율")

    col4, col5 = st.columns(2)
    with col4:
        fig_status = go.Figure(go.Pie(
            labels=fire_origin_counts.index,
            values=fire_origin_counts.values,
            hole=0.4,  # 도넛
            textinfo='percent+label'
        ))
        fig_status.update_layout(
            title="최초발화점",
            template="plotly_white",
            height=400
        )
        st.plotly_chart(fig_status, use_container_width=True)

    with col5:
        fig_status = go.Figure(go.Pie(
            labels=situation_counts.index,
            values=situation_counts.values,
            hole=0.4,  # 도넛
            textinfo='percent+label'
        ))
        fig_status.update_layout(
            title="상황",
            template="plotly_white",
            height=400
        )
        st.plotly_chart(fig_status, use_container_width=True)

    st.markdown("### 🚗 전기차 안정성 분석")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"""
        <div class="kpi-card kpi-1">
            <div class="kpi-title">총 화재 건수</div>
            <div class="kpi-value">{total_counts:,} 건</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="kpi-card kpi-2">
            <div class="kpi-title">고전압배터리 중 주행중(충돌)이 아닌 것</div>
            <div class="kpi-value">{filter_count:,} 건</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="kpi-card kpi-3">
            <div class="kpi-title">비율</div>
            <div class="kpi-value">{filter_m_ratio}%</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("### 🌎 해외 전기차 화재 비교")

    df_forieign_cleaned = df_foreign_fire.dropna(subset=["전기차(만대당)"])
    df_selected = df_forieign_cleaned[["연도", "국가", "전기차(만대당)"]]
    new_row1 = {"연도": 2021, "국가": "한국", "전기차(만대당)": 1.04}
    new_row2 = {"연도": 2022, "국가": "한국", "전기차(만대당)": 1.1}
    new_row3 = {"연도": 2023, "국가": "한국", "전기차(만대당)": 1.32}
    df_selected = pd.concat([df_selected, pd.DataFrame([new_row1])], ignore_index=True)
    df_selected = pd.concat([df_selected, pd.DataFrame([new_row2])], ignore_index=True)
    df_selected = pd.concat([df_selected, pd.DataFrame([new_row3])], ignore_index=True)
    df_selected["연도"] = df_selected["연도"].astype(int)
    df_selected = df_selected.sort_values(by="연도", ascending=True).reset_index(drop=True)

    # 연도별 그룹 국가별 막대그래프
    fig_bar = px.bar(
        df_selected,
        x="연도",
        y="전기차(만대당)",
        color="국가",
        barmode="group",          # 연도 안에서 국가별 막대 나란히
        text="전기차(만대당)",
        labels={"전기차(만대당)": "전기차 1만대당 (대)"},
        title="연도별 국가별 전기차(1만대당) 비교"
    )
    fig_bar.update_layout(
        template="plotly_white",
        yaxis=dict(title="전기차(1만대당)"),
        height=500
    )
    st.plotly_chart(fig_bar, use_container_width=True)

    st.markdown("### 🚗 제조사별 화재 비교")

    # 산점도 생성
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df_manufac_fire["제조사"],
        y=df_manufac_fire["점유율"],
        mode='markers+lines+text',
        name="제조사 점유율 (%)",
        marker=dict(size=12, color='yellow'),
        text=df_manufac_fire["점유율"],
        textposition="top center"
    ))
    fig.add_trace(go.Scatter(
        x=df_manufac_fire["제조사"],
        y=df_manufac_fire["전기차10만대당"],
        mode='markers+lines+text',
        name="전기차화재 10만대당 (대)",
        marker=dict(size=12, color='red'),
        text=df_manufac_fire["전기차10만대당"],
        textposition="top center"
    ))
    fig.add_trace(go.Scatter(
        x=df_manufac_fire["제조사"],
        y=df_manufac_fire["배터리10만대당"],
        mode='markers+lines+text',
        name="배터리화재 10만대당 (대)",
        marker=dict(size=12, color='green'),
        text=df_manufac_fire["배터리10만대당"],
        textposition="top center"
    ))
    fig.update_layout(
        title="제조사별 점유율, 전기차/배터리 10만대당 화재 비교",
        xaxis_title="제조사",
        yaxis_title="값",
        template="plotly_white",
        height=600
    )
    st.plotly_chart(fig, use_container_width=True)