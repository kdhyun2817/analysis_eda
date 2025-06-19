import streamlit as st
import pyrebase
import time
import io
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# ---------------------
# Firebase 설정
# ---------------------
firebase_config = {
    "apiKey": "AIzaSyCswFmrOGU3FyLYxwbNPTp7hvQxLfTPIZw",
    "authDomain": "sw-projects-49798.firebaseapp.com",
    "databaseURL": "https://sw-projects-49798-default-rtdb.firebaseio.com",
    "projectId": "sw-projects-49798",
    "storageBucket": "sw-projects-49798.firebasestorage.app",
    "messagingSenderId": "812186368395",
    "appId": "1:812186368395:web:be2f7291ce54396209d78e"
}

firebase = pyrebase.initialize_app(firebase_config)
auth = firebase.auth()
firestore = firebase.database()
storage = firebase.storage()

# ---------------------
# 세션 상태 초기화
# ---------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_email = ""
    st.session_state.id_token = ""
    st.session_state.user_name = ""
    st.session_state.user_gender = "선택 안함"
    st.session_state.user_phone = ""
    st.session_state.profile_image_url = ""

# ---------------------
# 홈 페이지 클래스
# ---------------------
class Home:
    def __init__(self, login_page, register_page, findpw_page):
        st.title("🏠 Home")
        if st.session_state.get("logged_in"):
            st.success(f"{st.session_state.get('user_email')}님 환영합니다.")

        # Kaggle 데이터셋 출처 및 소개
        st.markdown("""
                ---
                **Bike Sharing Demand 데이터셋**  
                - 제공처: [Kaggle Bike Sharing Demand Competition](https://www.kaggle.com/c/bike-sharing-demand)  
                - 설명: 2011–2012년 캘리포니아 주의 수도인 미국 워싱턴 D.C. 인근 도시에서 시간별 자전거 대여량을 기록한 데이터  
                - 주요 변수:  
                  - `datetime`: 날짜 및 시간  
                  - `season`: 계절  
                  - `holiday`: 공휴일 여부  
                  - `workingday`: 근무일 여부  
                  - `weather`: 날씨 상태  
                  - `temp`, `atemp`: 기온 및 체감온도  
                  - `humidity`, `windspeed`: 습도 및 풍속  
                  - `casual`, `registered`, `count`: 비등록·등록·전체 대여 횟수  
                """)

# ---------------------
# 로그인 페이지 클래스
# ---------------------
class Login:
    def __init__(self):
        st.title("🔐 로그인")
        email = st.text_input("이메일")
        password = st.text_input("비밀번호", type="password")
        if st.button("로그인"):
            try:
                user = auth.sign_in_with_email_and_password(email, password)
                st.session_state.logged_in = True
                st.session_state.user_email = email
                st.session_state.id_token = user['idToken']

                user_info = firestore.child("users").child(email.replace(".", "_")).get().val()
                if user_info:
                    st.session_state.user_name = user_info.get("name", "")
                    st.session_state.user_gender = user_info.get("gender", "선택 안함")
                    st.session_state.user_phone = user_info.get("phone", "")
                    st.session_state.profile_image_url = user_info.get("profile_image_url", "")

                st.success("로그인 성공!")
                time.sleep(1)
                st.rerun()
            except Exception:
                st.error("로그인 실패")

# ---------------------
# 회원가입 페이지 클래스
# ---------------------
class Register:
    def __init__(self, login_page_url):
        st.title("📝 회원가입")
        email = st.text_input("이메일")
        password = st.text_input("비밀번호", type="password")
        name = st.text_input("성명")
        gender = st.selectbox("성별", ["선택 안함", "남성", "여성"])
        phone = st.text_input("휴대전화번호")

        if st.button("회원가입"):
            try:
                auth.create_user_with_email_and_password(email, password)
                firestore.child("users").child(email.replace(".", "_")).set({
                    "email": email,
                    "name": name,
                    "gender": gender,
                    "phone": phone,
                    "role": "user",
                    "profile_image_url": ""
                })
                st.success("회원가입 성공! 로그인 페이지로 이동합니다.")
                time.sleep(1)
                st.switch_page(login_page_url)
            except Exception:
                st.error("회원가입 실패")

# ---------------------
# 비밀번호 찾기 페이지 클래스
# ---------------------
class FindPassword:
    def __init__(self):
        st.title("🔎 비밀번호 찾기")
        email = st.text_input("이메일")
        if st.button("비밀번호 재설정 메일 전송"):
            try:
                auth.send_password_reset_email(email)
                st.success("비밀번호 재설정 이메일을 전송했습니다.")
                time.sleep(1)
                st.rerun()
            except:
                st.error("이메일 전송 실패")

# ---------------------
# 사용자 정보 수정 페이지 클래스
# ---------------------
class UserInfo:
    def __init__(self):
        st.title("👤 사용자 정보")

        email = st.session_state.get("user_email", "")
        new_email = st.text_input("이메일", value=email)
        name = st.text_input("성명", value=st.session_state.get("user_name", ""))
        gender = st.selectbox(
            "성별",
            ["선택 안함", "남성", "여성"],
            index=["선택 안함", "남성", "여성"].index(st.session_state.get("user_gender", "선택 안함"))
        )
        phone = st.text_input("휴대전화번호", value=st.session_state.get("user_phone", ""))

        uploaded_file = st.file_uploader("프로필 이미지 업로드", type=["jpg", "jpeg", "png"])
        if uploaded_file:
            file_path = f"profiles/{email.replace('.', '_')}.jpg"
            storage.child(file_path).put(uploaded_file, st.session_state.id_token)
            image_url = storage.child(file_path).get_url(st.session_state.id_token)
            st.session_state.profile_image_url = image_url
            st.image(image_url, width=150)
        elif st.session_state.get("profile_image_url"):
            st.image(st.session_state.profile_image_url, width=150)

        if st.button("수정"):
            st.session_state.user_email = new_email
            st.session_state.user_name = name
            st.session_state.user_gender = gender
            st.session_state.user_phone = phone

            firestore.child("users").child(new_email.replace(".", "_")).update({
                "email": new_email,
                "name": name,
                "gender": gender,
                "phone": phone,
                "profile_image_url": st.session_state.get("profile_image_url", "")
            })

            st.success("사용자 정보가 저장되었습니다.")
            time.sleep(1)
            st.rerun()

# ---------------------
# 로그아웃 페이지 클래스
# ---------------------
class Logout:
    def __init__(self):
        st.session_state.logged_in = False
        st.session_state.user_email = ""
        st.session_state.id_token = ""
        st.session_state.user_name = ""
        st.session_state.user_gender = "선택 안함"
        st.session_state.user_phone = ""
        st.session_state.profile_image_url = ""
        st.success("로그아웃 되었습니다.")
        time.sleep(1)
        st.rerun()

# ---------------------
# EDA 페이지 클래스
# ---------------------
class EDA:
    def __init__(self):
        st.set_page_config(layout="wide")
        st.title("📊 Population Trends EDA")

        uploaded = st.file_uploader("Upload population_trends.csv", type="csv")
        if not uploaded:
            st.info("Please upload the CSV file.")
            st.stop()

        df = pd.read_csv(uploaded)

        # --- 전처리 ---
        sejong_mask = df['지역'].astype(str).str.contains("세종", na=False)
        df.loc[sejong_mask, :] = df.loc[sejong_mask, :].replace("-", "0")

        cols_to_numeric = ['인구', '출생아수(명)', '사망자수(명)']
        for col in cols_to_numeric:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

        df['연도'] = pd.to_numeric(df['연도'], errors='coerce')
        df['지역'] = df['지역'].astype(str)

        tabs = st.tabs(["📄 Basic Stats", "📈 Yearly Trend", "📍 Regional Analysis", "🔄 Change Analysis", "📊 Visualization"])

        # 탭 0: 기본 통계 및 데이터 구조
        with tabs[0]:
            st.subheader("Data Preview (first 5 rows)")
            st.dataframe(df.head(), use_container_width=True)

            st.subheader("Summary Statistics (df.describe())")
            st.dataframe(df.describe(include='all').transpose(), use_container_width=True)

            st.subheader("DataFrame Info (df.info())")
            buffer = io.StringIO()
            df.info(buf=buffer)
            s = buffer.getvalue()
            st.text(s)

        # 탭 1: 전국 인구 추이 + 2035년 예측
        with tabs[1]:
            st.subheader("National Population Trend and 2035 Forecast")
            nat = df[df['지역'] == '전국'].copy()

            nat['연도'] = pd.to_numeric(nat['연도'], errors='coerce')
            nat['인구'] = pd.to_numeric(nat['인구'], errors='coerce')
            nat['출생아수(명)'] = pd.to_numeric(nat.get('출생아수(명)', 0), errors='coerce').fillna(0)
            nat['사망자수(명)'] = pd.to_numeric(nat.get('사망자수(명)', 0), errors='coerce').fillna(0)

            nat = nat.dropna(subset=['연도', '인구']).sort_values('연도')

            recent = nat.sort_values('연도', ascending=False).head(3)
            avg_birth = recent['출생아수(명)'].mean()
            avg_death = recent['사망자수(명)'].mean()

            last_year = nat['연도'].max()
            last_pop = nat.loc[nat['연도'] == last_year, '인구'].values[0]

            years_to_2035 = 2035 - last_year
            forecast_pop = last_pop + (avg_birth - avg_death) * years_to_2035

            fig, ax = plt.subplots()
            ax.plot(nat['연도'], nat['인구'], marker='o', label="Actual Population")
            ax.scatter(2035, forecast_pop, color="red", label="Predicted Population 2035")
            ax.text(2035, forecast_pop, f"{int(forecast_pop):,}", ha='center', va='bottom', color='red')
            ax.set_title("National Population Trend")
            ax.set_xlabel("Year")
            ax.set_ylabel("Population")
            ax.legend()
            st.pyplot(fig)

        # 탭 2: 지역별 분석 (기존 내용 유지)
        with tabs[2]:
            st.subheader("Regional Population/Birth/Death Trends")
            regions = sorted(df['지역'].unique())
            region = st.selectbox("Select Region", [r for r in regions if r != '전국'])
            reg_df = df[df['지역'] == region]
            fig, ax = plt.subplots()
            ax.plot(reg_df['연도'], reg_df['인구'], label='Population')
            ax.plot(reg_df['연도'], reg_df['출생아수(명)'], label='Births')
            ax.plot(reg_df['연도'], reg_df['사망자수(명)'], label='Deaths')
            ax.set_title(f"Trends in {region}")
            ax.set_xlabel("Year")
            ax.set_ylabel("Count")
            ax.legend()
            st.pyplot(fig)

        # 탭 3: 인구 증감 상위 100 사례 + 컬러 강조
        with tabs[3]:
            st.subheader("Top 100 Population Changes by Region-Year")

            df_local = df[df['지역'] != '전국'].copy()
            df_local = df_local.sort_values(['지역', '연도'])
            df_local['증감'] = df_local.groupby('지역')['인구'].diff()

            top100 = df_local.dropna(subset=['증감']).nlargest(100, columns='증감', keep='all')

            top100['인구'] = top100['인구'].apply(lambda x: f"{int(x):,}")
            top100['증감'] = top100['증감'].apply(lambda x: f"{int(x):,}")

            def highlight_change(val):
                try:
                    v = float(val.replace(",", ""))
                    if v > 0:
                        return "background-color: rgba(0, 102, 255, 0.2);"  # 연한 파랑
                    elif v < 0:
                        return "background-color: rgba(255, 0, 0, 0.2);"    # 연한 빨강
                    else:
                        return ""
                except:
                    return ""

            styled_df = top100[['연도', '지역', '인구', '증감']].style.applymap(highlight_change, subset=['증감'])
            st.dataframe(styled_df, use_container_width=True)

        # 탭 4: 최근 5년 인구 변화량 및 변화율 그래프
        with tabs[4]:
            st.subheader("Population Change Analysis in Last 5 Years by Region")

            region_dict = {
                "서울": "Seoul", "부산": "Busan", "대구": "Daegu", "인천": "Incheon", "광주": "Gwangju",
                "대전": "Daejeon", "울산": "Ulsan", "세종": "Sejong", "경기": "Gyeonggi", "강원": "Gangwon",
                "충북": "Chungbuk", "충남": "Chungnam", "전북": "Jeonbuk", "전남": "Jeonnam",
                "경북": "Gyeongbuk", "경남": "Gyeongnam", "제주": "Jeju"
            }

            df_local = df[df['지역'] != '전국'].copy()
            df_local['Region_EN'] = df_local['지역'].map(region_dict)

            latest_year = df_local['연도'].max()
            year_5ago = latest_year - 5

            recent_df = df_local[df_local['연도'].between(year_5ago, latest_year)]

            pivot_pop = recent_df.pivot_table(index='Region_EN', columns='연도', values='인구', aggfunc='mean').fillna(0)

            pivot_pop['Change'] = pivot_pop[latest_year] - pivot_pop[year_5ago]
            pivot_pop['ChangeRate'] = (pivot_pop['Change'] / pivot_pop[year_5ago]) * 100

            pivot_pop = pivot_pop.sort_values(by='Change', ascending=False)

            # 인구 변화량 그래프
            fig1, ax1 = plt.subplots(figsize=(10, 6))
            sns.barplot(x=pivot_pop['Change'] / 1000, y=pivot_pop.index, ax=ax1, palette='viridis')
            ax1.set_title('Population Change in Last 5 Years by Region')
            ax1.set_xlabel('Population Change (thousands)')
            ax1.set_ylabel('Region')
            for i, v in enumerate(pivot_pop['Change'] / 1000):
                ax1.text(v + 0.05, i, f"{v:.1f}", va='center')
            st.pyplot(fig1)

            st.markdown(
                """
                **Explanation:**  
                This chart shows the absolute population change in thousands for each region over the last five years.  
                Positive values indicate population growth, while negative values indicate decline.
                """
            )

            # 인구 변화율 그래프
            fig2, ax2 = plt.subplots(figsize=(10, 6))
            sns.barplot(x=pivot_pop['ChangeRate'], y=pivot_pop.index, ax=ax2, palette='coolwarm', dodge=False)
            ax2.set_title('Population Change Rate in Last 5 Years by Region')
            ax2.set_xlabel('Change Rate (%)')
            ax2.set_ylabel('Region')
            for i, v in enumerate(pivot_pop['ChangeRate']):
                ax2.text(v + (1 if v >= 0 else -3), i, f"{v:.1f}%", va='center')
            st.pyplot(fig2)

            st.markdown(
                """
                **Explanation:**  
                This chart shows the percentage change in population for each region over the last five years, relative to the population five years ago.  
                It highlights which regions have experienced the fastest growth or decline proportionally.
                """
            )




# ---------------------
# 페이지 객체 생성
# ---------------------
Page_Login    = st.Page(Login,    title="Login",    icon="🔐", url_path="login")
Page_Register = st.Page(lambda: Register(Page_Login.url_path), title="Register", icon="📝", url_path="register")
Page_FindPW   = st.Page(FindPassword, title="Find PW", icon="🔎", url_path="find-password")
Page_Home     = st.Page(lambda: Home(Page_Login, Page_Register, Page_FindPW), title="Home", icon="🏠", url_path="home", default=True)
Page_User     = st.Page(UserInfo, title="My Info", icon="👤", url_path="user-info")
Page_Logout   = st.Page(Logout,   title="Logout",  icon="🔓", url_path="logout")
Page_EDA      = st.Page(EDA,      title="EDA",     icon="📊", url_path="eda")

# ---------------------
# 네비게이션 실행
# ---------------------
if st.session_state.logged_in:
    pages = [Page_Home, Page_User, Page_Logout, Page_EDA]
else:
    pages = [Page_Home, Page_Login, Page_Register, Page_FindPW]

selected_page = st.navigation(pages)
selected_page.run()