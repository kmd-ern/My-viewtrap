import streamlit as st
from googleapiclient.discovery import build
from datetime import datetime

# ==========================================
# 👇 API 키 입력 (따옴표 안에 넣으세요)
API_KEY = 'AIzaSyDk-YrjKCiJSnjoSIeSB46yroeZiCCSXWI'
# ==========================================

# 1. 페이지 설정 (탭 이름 등)
st.set_page_config(page_title="나만의 뷰트랩", layout="wide")

# 2. 스타일(CSS) - 카드 디자인
st.markdown("""
<style>
    .card {
        background-color: white;
        border-radius: 10px;
        padding: 0;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        border: 1px solid #e0e0e0;
        overflow: hidden;
    }
    .thumb-container { position: relative; width: 100%; aspect-ratio: 16/9; }
    .thumb-img { width: 100%; height: 100%; object-fit: cover; }
    .badge-overlay { position: absolute; top: 10px; left: 10px; display: flex; flex-direction: column; gap: 5px; }
    .badge { padding: 4px 8px; border-radius: 5px; font-size: 12px; font-weight: bold; color: white; width: fit-content; }
    .bg-red { background-color: #ff4b4b; }
    .bg-orange { background-color: #ffa421; }
    .bg-green { background-color: #21c354; }
    .bg-dark { background-color: rgba(0,0,0,0.7); }
    .info { padding: 15px; }
    .title { font-size: 16px; font-weight: bold; margin-bottom: 5px; line-height: 1.4; height: 45px; overflow: hidden; color: #333; text-decoration: none; display: block;}
    .meta { font-size: 13px; color: #666; display: flex; justify-content: space-between; margin-top: 10px; }
    .stats { color: #d93025; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# 3. 데이터 저장소 (세션 스테이트 - 웹사이트가 켜져있는 동안 기억함)
if 'archive' not in st.session_state:
    st.session_state.archive = []

# 4. 함수: 유튜브 검색
def search_youtube(keyword):
    try:
        youtube = build('youtube', 'v3', developerKey=API_KEY)
        search_response = youtube.search().list(
            q=keyword, part='snippet', maxResults=12, type='video', order='viewCount'
        ).execute()

        video_ids = [item['id']['videoId'] for item in search_response['items']]
        channel_ids = [item['snippet']['channelId'] for item in search_response['items']]

        # 상세 정보 조회
        vid_res = youtube.videos().list(part='statistics', id=','.join(video_ids)).execute()
        ch_res = youtube.channels().list(part='statistics', id=','.join(channel_ids)).execute()

        ch_subs = {ch['id']: int(ch['statistics'].get('subscriberCount', 0) or 1) for ch in ch_res['items']}
        
        results = []
        for i, item in enumerate(search_res['items']):
            vid_stats = vid_res['items'][i]['statistics']
            views = int(vid_stats.get('viewCount', 0))
            ch_id = item['snippet']['channelId']
            subs = ch_subs.get(ch_id, 1)
            pub_date = item['snippet']['publishedAt'][:10]
            
            # 최신 영상 여부 (30일 이내)
            is_new = False
            try:
                date_obj = datetime.strptime(pub_date, "%Y-%m-%d")
                if (datetime.now() - date_obj).days <= 30: is_new = True
            except: pass

            results.append({
                'id': item['id']['videoId'],
                'title': item['snippet']['title'],
                'thumb': item['snippet']['thumbnails']['medium']['url'],
                'channel': item['snippet']['channelTitle'],
                'views': views,
                'subs': subs,
                'date': pub_date,
                'perf': (views / subs) * 100,
                'is_new': is_new,
                'url': f"https://www.youtube.com/watch?v={item['id']['videoId']}"
            })
        return results
    except Exception as e:
        st.error(f"에러가 발생했습니다: {e}")
        return []

# 5. 화면 구성 (UI)
st.title("📱 My ViewTrap")

# 탭 만들기
tab1, tab2 = st.tabs(["🔍 영상 찾기", "📚 보관함"])

with tab1:
    # 검색창 (엔터키 치면 자동 적용됨)
    col1, col2 = st.columns([4, 1])
    with col1:
        query = st.text_input("키워드 검색", placeholder="예: 스마트스토어, 다이어트")
    with col2:
        sort_option = st.selectbox("정렬", ["🔥 성과순", "📅 최신순", "👁️ 조회수순"])

    if query:
        # 데이터 가져오기
        with st.spinner('유튜브 분석 중...'):
            data = search_youtube(query)

        # 정렬 로직
        if sort_option == "🔥 성과순":
            data.sort(key=lambda x: x['perf'], reverse=True)
        elif sort_option == "📅 최신순":
            data.sort(key=lambda x: x['date'], reverse=True)
        else:
            data.sort(key=lambda x: x['views'], reverse=True)

        # 그리드 형태로 보여주기 (3열)
        cols = st.columns(3)
        for idx, video in enumerate(data):
            with cols[idx % 3]:
                # 배지 HTML 생성
                badges = f'<div class="badge bg-dark">{video["date"]}</div>'
                if video['is_new']: badges += '<div class="badge bg-green">✨ NEW</div>'
                if video['perf'] >= 100: badges += f'<div class="badge bg-red">🔥 성과 {int(video["perf"])}%</div>'
                elif video['perf'] >= 30: badges += f'<div class="badge bg-orange">👍 {int(video["perf"])}%</div>'

                # 카드 HTML 출력
                st.markdown(f"""
                <div class="card">
                    <div class="thumb-container">
                        <img src="{video['thumb']}" class="thumb-img">
                        <div class="badge-overlay">{badges}</div>
                    </div>
                    <div class="info">
                        <a href="{video['url']}" target="_blank" class="title">{video['title']}</a>
                        <div class="meta">
                            <span>📺 {video['channel']} (구독 {video['subs']//1000}k)</span>
                        </div>
                        <div class="meta">
                            <span class="stats">👁️ {video['views']:,}회</span>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                # 저장 버튼 (Streamlit 버튼 사용)
                # 이미 저장된 건지 확인
                is_saved = any(v['id'] == video['id'] for v in st.session_state.archive)
                if is_saved:
                    st.button("✅ 저장됨", key=f"saved_{video['id']}", disabled=True)
                else:
                    if st.button("📥 보관함 담기", key=f"btn_{video['id']}"):
                        st.session_state.archive.append(video)
                        st.rerun() # 화면 새로고침해서 버튼 상태 업데이트

with tab2:
    st.header(f"내 보관함 ({len(st.session_state.archive)}개)")
    if len(st.session_state.archive) == 0:
        st.info("아직 저장된 영상이 없습니다. 검색 탭에서 영상을 담아보세요!")
    else:
        # 보관함 그리드
        arch_cols = st.columns(3)
        for idx, video in enumerate(reversed(st.session_state.archive)): # 최신 저장순
            with arch_cols[idx % 3]:
                # (위와 동일한 카드 디자인 - 간략화)
                st.markdown(f"""
                <div class="card">
                    <img src="{video['thumb']}" style="width:100%; aspect-ratio:16/9; object-fit:cover;">
                    <div style="padding:10px;">
                        <div style="font-weight:bold; font-size:14px; margin-bottom:5px;">{video['title']}</div>
                        <div style="font-size:12px; color:#666;">{video['channel']}</div>
                        <div style="color:red; font-weight:bold;">👁️ {video['views']:,}회</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                # 삭제 버튼 (선택 사항)
                if st.button("🗑️ 삭제", key=f"del_{video['id']}"):
                    st.session_state.archive.remove(video)
                    st.rerun()
