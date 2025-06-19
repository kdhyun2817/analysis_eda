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

        # ✅ 전처리
        sejong_rows = df['지역'].astype(str).str.contains("세종", na=False)
        df.loc[sejong_rows] = df.loc[sejong_rows].replace("-", "0")

        for col in ['인구', '출생아수(명)', '사망자수(명)']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

        df['연도'] = pd.to_numeric(df['연도'], errors='coerce')
        df['지역'] = df['지역'].astype(str)

        # ✅ 탭 구성
        tabs = st.tabs(["📄 Basic Stats", "📈 Yearly Trend", "📍 Regional Analysis", "🔄 Change Analysis", "📊 Visualization"])

        # ----------------------------
        # 📄 TAB 1: Basic Stats
        # ----------------------------
        with tabs[0]:
            st.subheader("📋 데이터 미리보기 (처음 5행)")
            st.dataframe(df.head(), use_container_width=True)

            st.subheader("📈 요약 통계 (`df.describe()`)")
            desc = df.describe(include='all').transpose()
            st.dataframe(desc, use_container_width=True)

            st.subheader("🧾 데이터 구조 (`df.info()`)")
            buffer = io.StringIO()
            df.info(buf=buffer)
            st.text(buffer.getvalue())

        # ----------------------------
        # 📈 TAB 2: Yearly Trend (전국 기준 + 예측)
        # ----------------------------
        with tabs[1]:
            st.subheader("📊 전국 연도별 인구 추이 및 2035년 예측")
            nat = df[df['지역'] == '전국'].copy().dropna(subset=['연도', '인구'])
            nat = nat.sort_values('연도')

            if not nat.empty:
                recent = nat.sort_values('연도', ascending=False).head(3)
                birth = recent['출생아수(명)'].mean()
                death = recent['사망자수(명)'].mean()
                net = birth - death
                last_year = int(nat['연도'].max())
                last_pop = nat[nat['연도'] == last_year]['인구'].values[0]
                forecast_2035 = last_pop + net * (2035 - last_year)

                fig, ax = plt.subplots()
                ax.plot(nat['연도'], nat['인구'], marker='o', label="실측치")
                ax.scatter(2035, forecast_2035, color="red", label="2035 예측")
                ax.text(2035, forecast_2035, f"{int(forecast_2035):,}", ha='center', va='bottom')
                ax.set_title("전국 인구 추이")
                ax.set_xlabel("연도")
                ax.set_ylabel("인구 수")
                ax.legend()
                st.pyplot(fig)
            else:
                st.warning("전국 데이터가 없습니다.")

        # ----------------------------
        # 📍 TAB 3: Regional Analysis
        # ----------------------------
        with tabs[2]:
            st.subheader("🗺️ 지역별 인구 / 출생 / 사망 추이")
            regions = sorted(df['지역'].unique())
            region = st.selectbox("지역 선택", [r for r in regions if r != '전국'])

            reg_df = df[df['지역'] == region]
            fig, ax = plt.subplots()
            ax.plot(reg_df['연도'], reg_df['인구'], label='인구', marker='o')
            ax.plot(reg_df['연도'], reg_df['출생아수(명)'], label='출생아수', linestyle='--')
            ax.plot(reg_df['연도'], reg_df['사망자수(명)'], label='사망자수', linestyle='-.')
            ax.set_title(f"{region} 지역 추이")
            ax.set_xlabel("연도")
            ax.set_ylabel("인구 / 출생 / 사망")
            ax.legend()
            st.pyplot(fig)

        # ----------------------------
        # 🔄 TAB 4: Change Analysis
        # ----------------------------
        with tabs[3]:
            st.subheader("📉 지역별 연도간 인구 변화량 상위 100건")
            df_local = df[df['지역'] != '전국'].copy()
            df_local = df_local.sort_values(['지역', '연도'])
            df_local['증감'] = df_local.groupby('지역')['인구'].diff()
            top100 = df_local.dropna(subset=['증감']).nlargest(100, columns='증감', keep='all')

            def highlight(val):
                try:
                    v = float(str(val).replace(",", ""))
                    if v > 0:
                        return "background-color: rgba(0, 102, 255, 0.2);"
                    else:
                        return "background-color: rgba(255, 0, 0, 0.2);"
                except:
                    return ""

            top100['인구'] = top100['인구'].apply(lambda x: f"{int(x):,}")
            top100['증감'] = top100['증감'].apply(lambda x: f"{int(x):,}")
            styled = top100[['연도', '지역', '인구', '증감']].style.applymap(highlight, subset=['증감'])

            st.dataframe(styled, use_container_width=True)

        # ----------------------------
        # 📊 TAB 5: Visualization (Stacked Area)
        # ----------------------------
        with tabs[4]:
            st.subheader("📈 지역별 인구 누적 변화 (Stacked Area Chart)")

            region_dict = {
                "서울": "Seoul", "부산": "Busan", "대구": "Daegu", "인천": "Incheon", "광주": "Gwangju",
                "대전": "Daejeon", "울산": "Ulsan", "세종": "Sejong", "경기": "Gyeonggi", "강원": "Gangwon",
                "충북": "Chungbuk", "충남": "Chungnam", "전북": "Jeonbuk", "전남": "Jeonnam",
                "경북": "Gyeongbuk", "경남": "Gyeongnam", "제주": "Jeju"
            }

            df_viz = df[df['지역'] != '전국'].copy()
            df_viz['Region_EN'] = df_viz['지역'].map(region_dict)
            pivot = df_viz.pivot_table(index='Region_EN', columns='연도', values='인구', aggfunc='mean').fillna(0)
            pivot = pivot.sort_index(axis=1)
            pivot_T = pivot.transpose()

            fig, ax = plt.subplots(figsize=(12, 6))
            colors = sns.color_palette("tab20", n_colors=len(pivot_T.columns))
            pivot_T.plot.area(ax=ax, stacked=True, color=colors)
            ax.set_title("지역별 인구 추이 (누적 면적 차트)")
            ax.set_xlabel("연도")
            ax.set_ylabel("인구 수")
            ax.legend(loc='upper left', bbox_to_anchor=(1.0, 1.0), title="Region")
            st.pyplot(fig)



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