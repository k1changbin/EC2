import streamlit as st
from utils.load_data import load_quiz, load_players
from utils.match import match_player
from utils.config import MAX_VALUES, STAT_LABELS
import plotly.graph_objects as go

st.set_page_config(page_title="축구 DNA 분석기", page_icon="⚽", layout="wide")

# 세션 상태 초기화
if "login_status" not in st.session_state:
    st.session_state.login_status = False
if "user_id" not in st.session_state:
    st.session_state.user_id = "게스트"
if "page" not in st.session_state:
    st.session_state.page = "main"          # 화면 전환을 위한 상태 변수 (main / quiz / result)
if "stats" not in st.session_state:
    st.session_state.stats = {k: 0 for k in MAX_VALUES.keys()}
if "current_q" not in st.session_state:
    st.session_state.current_q = 0          # 현재 보여줄 문제 인덱스 (0번부터 시작)
if "answers" not in st.session_state:
    st.session_state.answers = {}           # 사용자가 선택한 답변을 모아둘 딕셔너리
if "show_login_form" not in st.session_state:
    st.session_state.show_login_form = False

# 본 프로젝트는 보안을 위해 st.secrets를 사용합니다. 로컬에서 실행 시 
#.streamlit/secrets.toml 파일을 생성하고 아래 내용을 추가해야 로그인이 가능합니다. 
try:
    # secrets.toml의 [passwords] 섹션에 있는 모든 아이디:비밀번호를 자동으로 가져옴
    USER_DB = dict(st.secrets["passwords"])
except FileNotFoundError:
    # 로컬 테스트 시 secrets 파일이 없어도 에러가 나지 않도록 빈 딕셔너리 처리
    USER_DB = {}

# --- 상단 레이아웃 (헤더 및 로그인 버튼) ---
header_col, login_col = st.columns([8, 1])

with header_col:
    st.title("축구 DNA 분석기")
    st.text("학번: 2023204035 | 이름: 권창빈")

with login_col:
    # 로그인 상태에 따른 버튼 표시
    if not st.session_state.login_status:
        if st.button("로그인"):
            print("로그인 버튼 클릭") 
            st.session_state.show_login_form = True
            st.rerun()
    else:
        st.success(f"{st.session_state.user_id}")
        if st.button("로그아웃"):
            print("로그아웃 버튼 클릭")
            st.session_state.login_status = False
            st.session_state.user_id = "게스트"
            st.rerun()

st.divider()

# --- 로그인 입력창 ---
if not st.session_state.login_status and st.session_state.show_login_form:
    with st.expander("로그인 정보 입력", expanded=True):
        input_id = st.text_input("아이디")
        input_pw = st.text_input("비밀번호", type="password")
        if st.button("완료"):
            print("완료 버튼 클릭")
            if input_id in USER_DB and USER_DB[input_id] == input_pw:
                print(f"로그인 성공 : {input_id} 접속")
                st.session_state.login_status = True
                st.session_state.user_id = input_id
                st.session_state.show_login_form = False
                st.rerun()
            else:
                print(f"로그인 실패 시도 id : {input_id}")
                st.error("정보가 일치하지 않습니다.")
        if st.button("닫기"):
            print("닫기 버튼 클릭")
            st.session_state.show_login_form = False
            st.rerun()

# --- 메인 콘텐츠 및 화면 전환 ---

# [메인 화면]
if st.session_state.page == "main":
    st.subheader("나와 가장 닮은 축구 스타는 누구일까요?")

    # 버튼을 화면 중앙에 배치
    _, center_col, _ = st.columns([1, 1, 1])
    with center_col:
        st.write("") # 위아래 여백
        if st.button("분석하러 가기", use_container_width=True, type="primary", key="btn_start_analysis"):
            print("'분석하러 가기' 버튼 클릭")
            st.session_state.page = "quiz" # 퀴즈 페이지로 상태 변경
            st.rerun()
        st.write("")

# [퀴즈 화면]
elif st.session_state.page == "quiz":
    st.subheader("DNA 분석기")
    
    quiz = load_quiz()
    total_q = len(quiz)
    current_q = st.session_state.current_q  # 현재 문제 번호

    # --- 실시간 DNA 업데이트 로직 ---
    # 1. JSON 구조에 맞춘 실시간 점수 계산
    temp_stats = {k: 0 for k in MAX_VALUES.keys()}
    
    for idx in range(total_q):
        selected_val = st.session_state.get(f"radio_{idx}") or st.session_state.answers.get(idx)
        if selected_val:
            # 현재 문제의 category를 소문자로 가져옴 (예: "Speed" -> "speed")
            category = quiz[idx]["category"].lower()
            
            for choice in quiz[idx]["choices"]:
                if choice["text"] == selected_val:
                    # 선택지에 할당된 score를 해당 카테고리에 누적
                    temp_stats[category] += choice["score"]
                    break  

    # 2. 사이드바에 실시간 분석 결과 표시
    with st.sidebar:
        st.header("실시간 DNA 분석")
        
        # user_id 로그인 구현체에 맞게 예외 처리 (로그인 안 된 경우 게스트)
        user_name = st.session_state.user_id
        st.caption(f"분석 대상: **{user_name}**")
        
        
        # config.py의 데이터 순서를 기준으로 키와 라벨을 동적으로 가져옴
        stats_keys = list(MAX_VALUES.keys())
        categories = [STAT_LABELS[k] for k in stats_keys]
        
        fig = go.Figure(data=go.Scatterpolar(
            r=[temp_stats.get(k, 0) for k in stats_keys], # 키 리스트를 사용하여 값 추출
            theta=categories,
            fill='toself',
            line_color='#FF4B4B'
        ))

        fig.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 100])), 
            showlegend=False,
            margin=dict(l=30, r=30, t=30, b=30),
            height=300
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # 각 항목별 개별 MAX_VAL 적용하여 프로그레스 바 표시
        st.write("### 능력치 상세")
        
        for k in stats_keys: # 여기도 stats_keys를 활용하여 순서 일관성 유지
            v = temp_stats[k]
            label = STAT_LABELS[k]
            max_val = MAX_VALUES[k]  # utils/config.py 에서 전부 100으로 설정
            
            # 현재 점수 / 최대 점수 텍스트
            st.write(f"**{label}** : {v} / {max_val} pts")
            
            # 항목별 max값을 기준으로 비율 계산 (0.0 ~ 1.0)
            progress_ratio = min(v / max_val, 1.0) if max_val > 0 else 0
            st.progress(progress_ratio)

    # --- 메인 퀴즈 UI ---
    st.write(f"**문제 {current_q + 1} / {total_q}**")
    st.progress((current_q + 1) / total_q)
    st.divider()

    q = quiz[current_q]
    choices_text = [c["text"] for c in q["choices"]]
    
    # 기본값 설정
    default_index = None
    if current_q in st.session_state.answers:
        if st.session_state.answers[current_q] in choices_text:
            default_index = choices_text.index(st.session_state.answers[current_q])
    
    # q['category']가 "Attack"이면 -> .lower()로 "attack"으로 변환 -> STAT_LABELS에서 "공격"을 가져옴
    korean_category = STAT_LABELS.get(q['category'].lower(), q['category'])
    st.caption(f"측정 항목: **{korean_category}**")
    
    # 라디오 버튼 (클릭 시 세션 상태가 즉시 바뀌어 사이드바에 반영됨)
    selected = st.radio(q["question"], choices_text, index=default_index, key=f"radio_{current_q}")

    st.write("") 

    col1, col2 = st.columns(2)
    with col1:
        if current_q > 0:
            if st.button("이전", use_container_width=True):
                print("이전 클릭")
                st.session_state.answers[current_q] = selected
                st.session_state.current_q -= 1
                st.rerun()

    with col2:
        if current_q < total_q - 1:
            # 선택지가 None이 아닐 때만 다음으로 넘어가도록
            if st.button("다음", use_container_width=True, type="primary", disabled=(selected is None)):
                print("다음 클릭")
                st.session_state.answers[current_q] = selected
                st.session_state.current_q += 1
                st.rerun()
        else:
            # 결과 보기 버튼도 마찬가지
            if st.button("결과 보기", use_container_width=True, type="primary", disabled=(selected is None)):
                print("결과 보기 클릭")
                st.session_state.answers[current_q] = selected
                st.session_state.stats = temp_stats.copy()
                st.session_state.page = "result"
                st.rerun()
            
    st.divider()
    if st.button("메인 화면으로 돌아가기"):
        print("메인 화면으로 돌아가기 클릭")
        st.session_state.page = "main"
        st.session_state.current_q = 0
        st.session_state.answers = {}
        st.rerun()

# [결과 화면]
elif st.session_state.page == "result":
    st.subheader("분석 결과")
    
    if st.session_state.login_status:
        st.write(f" {st.session_state.user_id}님의 정밀 분석 데이터입니다.")
    else:
        st.warning("⚠️ 로그인을 하지 않은 '게스트' 결과입니다")

    stats = st.session_state.stats
    players = load_players()
    
    # 모든 선수와의 유사도를 계산하고 상위 3명을 추출
    top_matches = match_player(stats, players)[:3] 
    p1 = top_matches[0] # 1위 선수

    st.success(f"분석 완료! 당신과 가장 닮은 상위 3명의 선수를 찾았습니다.")
    st.divider()

    # --- 상단 섹션: 1위 선수와 레이더 차트 비교 ---
    st.write(f"### Best Match: {p1['name']}")
    st.caption(f"주 포지션: {p1['position']}")
    top_col1, top_col2 = st.columns([1.5, 1])

    with top_col1:
        # config에서 데이터 가져오기
        stats_keys = list(MAX_VALUES.keys()) 
        categories = [STAT_LABELS[k] for k in stats_keys]
        user_vals = [stats.get(k, 0) for k in stats_keys]
        player_vals = [p1.get(k, 0) for k in stats_keys]

        # Plotly 차트 생성
        fig = go.Figure()
        fig.add_trace(go.Scatterpolar(
            r=user_vals, theta=categories, fill='toself', name='나 (Your DNA)', line=dict(color='#FF4B4B')
        ))
        fig.add_trace(go.Scatterpolar(
            r=player_vals, theta=categories, fill='toself', name=f"{p1['name']}", line=dict(color='#1F77B4')
        ))
        fig.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
            showlegend=True,
            legend=dict(yanchor="top", y=1.2, xanchor="left", x=0),
            margin=dict(t=50, b=30, l=30, r=30)
        )
        st.plotly_chart(fig, use_container_width=True)

    with top_col2:
        st.write("") 
        # 1. 전체 매칭률 표시
        p1_sim = p1.get('similarity', 0)
        st.metric(label="플레이 스타일 싱크로율", value=f"{p1_sim}%")
        st.progress(p1_sim / 100)
        
        st.write("---")
        st.success(f"당신은 {p1['name']} 선수와 축구 DNA 구성비가 매우 흡사합니다.")
        # 스타일 비중 분석
        with st.expander("스타일 비중 한눈에 비교하기", expanded=True):
            
            st.info(f"""
                **💡 분석 가이드**
                * **점수(pts):** 월드클래스 선수가 아닌 **일반인 숙련도** 기준입니다.
                * **매칭률:** 전체 역량 중 각 항목이 차지하는 **비중**이 **{p1['name']}** 선수와 얼마나 닮았는지를 나타냅니다.
            """)
            
            # 2. 비중 계산을 위한 각 총합 구하기
            user_total = sum(stats.values())
            player_total = sum(p1.get(k, 0) for k in stats_keys)

            # 3. 항목별 비중 바 생성 
            for key in stats_keys:
                u_score = stats.get(key, 0)
                p_score = p1.get(key, 0)
                label = STAT_LABELS[key]
                
                # 각 항목이 전체 능력치 총합에서 차지하는 비중(%) 계산
                u_ratio = (u_score / user_total * 100) if user_total > 0 else 0
                p_ratio = (p_score / player_total * 100) if player_total > 0 else 0
                
                st.markdown(f"**{label}**")
                
                # 나의 비중 표시
                st.caption(f"나의 {label} 비중: {u_ratio:.1f}% ({int(u_score)}pts)")
                st.progress(u_ratio / 100)
                
                # 선수 비중 표시
                st.caption(f"{p1['name']}의 {label} 비중: {p_ratio:.1f}% ({int(p_score)}pts)")
                st.progress(p_ratio / 100)
                st.write("") 
        

    # --- 하단 : 2, 3위 선수 나열 ---
    st.write("### Next Matches")
    bot_cols = st.columns(2)

    for i, player in enumerate(top_matches[1:3]):
        with bot_cols[i]:
            st.markdown(f"#### {i+2}위")
            p_name = player['name']
            p_sim = player.get('similarity', 0)
            st.metric(label=p_name, value=f"{p_sim}%")
            st.progress(p_sim / 100)
            st.write(f"포지션: {player['position']}")

    st.divider()
    print("다시 검사하기 버튼 클릭")
    if st.button("다시 검사하기", use_container_width=True):
        st.session_state.page = "main"
        st.session_state.current_q = 0
        st.session_state.answers = {}
        st.session_state.stats = {k: 0 for k in MAX_VALUES.keys()}
        st.rerun()