import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# 1. 페이지 기본 설정
st.set_page_config(
    page_title="서울 100년 기온 변화 분석",
    page_icon="🌡️",
    layout="wide"
)

# 2. 데이터 로드 및 전처리 (캐싱 적용)
DATA_URL = "https://raw.githubusercontent.com/greatsong/modudata/main/data/seoul.csv"

@st.cache_data
def load_data():
    # 데이터 읽기 (열: 날짜, 지점, 평균기온, 최저기온, 최고기온)
    df = pd.read_csv(DATA_URL, encoding='utf-8')
    
    # 열 이름 정리 (공백 제거)
    df.columns = df.columns.str.strip()
    
    # 날짜 데이터 변환 및 연도 추출
    df['날짜'] = pd.to_datetime(df['날짜'])
    df['연도'] = df['날짜'].dt.year
    
    # 평균기온 결측치 제거
    df = df.dropna(subset=['평균기온'])
    
    # 연도별 연평균 기온 계산
    yearly_df = df.groupby('연도')['평균기온'].mean().reset_index()
    yearly_df.rename(columns={'평균기온': '연평균기온'}, inplace=True)
    
    # 데이터가 부족한 연도 제외 (예: 데이터 수집 개수가 적은 연도 정제)
    counts = df.groupby('연도')['평균기온'].count()
    valid_years = counts[counts >= 300].index
    yearly_df = yearly_df[yearly_df['연도'].isin(valid_years)].reset_index(drop=True)
    
    # 10년 이동평균 계산
    yearly_df['10년_이동평균'] = yearly_df['연평균기온'].rolling(window=10, min_periods=1).mean()
    
    return yearly_df

# 앱 데이터 불러오기
try:
    df_yearly = load_data()
except Exception as e:
    st.error(f"데이터를 불러오는 중 오류가 발생했습니다: {e}")
    st.stop()

# 3. 메인 화면 구성
st.title("🌡️ 서울의 100년 기온 변화 추이")
st.write("1900년대 초반부터 현재까지, 서울의 연평균 기온이 어떻게 변해왔는지 한눈에 확인해보세요.")

# 주요 요약 지표 (Metrics)
first_year = int(df_yearly['연도'].min())
last_year = int(df_yearly['연도'].max())
start_temp = df_yearly.iloc[0]['연평균기온']
end_temp = df_yearly.iloc[-1]['연평균기온']
diff_temp = end_temp - start_temp

col1, col2, col3, col4 = st.columns(4)
col1.metric("분석 시작 연도", f"{first_year}년")
col2.metric("최근 연도", f"{last_year}년")
col3.metric("최근 연평균 기온", f"{end_temp:.1f} °C")
col4.metric("시작 대비 변화", f"{diff_temp:+.1f} °C", delta_color="inverse")

st.markdown("---")

# 4. 연평균 기온 그래프 (Plotly)
fig = go.Figure()

# 연평균 기온 선 그래프
fig.add_trace(
    go.Scatter(
        x=df_yearly['연도'],
        y=df_yearly['연평균기온'],
        mode='lines+markers',
        name='연평균 기온',
        line=dict(color='#EF4444', width=2),
        marker=dict(size=5),
        hovertemplate='%{x}년: %{y:.2f}°C<extra></extra>'
    )
)

# 10년 이동평균선
fig.add_trace(
    go.Scatter(
        x=df_yearly['연도'],
        y=df_yearly['10년_이동평균'],
        mode='lines',
        name='10년 이동평균',
        line=dict(color='#F59E0B', width=3, dash='dash'),
        hovertemplate='%{x}년 10년 평균: %{y:.2f}°C<extra></extra>'
    )
)

# Layout 설정
fig.update_layout(
    title=dict(text=f"서울 연도별 연평균 기온 변화 ({first_year}년 ~ {last_year}년)", font=dict(size=18)),
    xaxis_title="연도",
    yaxis_title="평균 기온 (°C)",
    hovermode="x unified",
    template="plotly_white",
    height=500,
    legend=dict(orient="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
)

st.plotly_chart(fig, use_container_width=True)

# 5. 데이터 표 및 다운로드
with st.expander("📄 데이터 원본 보기"):
    st.dataframe(df_yearly, use_container_width=True)
    
    csv_data = df_yearly.to_csv(index=False).encode('utf-8-sig')
    st.download_button(
        label="CSV 파일로 다운로드",
        data=csv_data,
        file_name="seoul_yearly_temperature.csv",
        mime="text/csv"
    )
