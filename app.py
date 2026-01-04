import streamlit as st
from googleapiclient.discovery import build
from datetime import datetime

# ==========================================
# 👇 API 키 입력 (따옴표 안에 넣으세요)
API_KEY = 'AIzaSyDk-YrjKCiJSnjoSIeSB46yroeZiCCSXWI'
# ==========================================

# 1. 페이지 설정
st.set_page_config(page_title="나만의 뷰트랩", layout="wide")

# 2. 스타일(CSS)
st.markdown("""
<style>
    .card {
        background-color: white; border-radius: 10px; padding: 0; margin-bottom: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1); border: 1px solid #e0e0e0; overflow: hidden;
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

# 3. 데이터 저장소 (세션 스테이트 - 기억력 장치)
if 'archive' not in st.session_state:
    st.session_state.archive = []

if 'search_results' not in st.session_state:
    st.session_state.search_results = [] # 검색 결과도 기억하게 만듦!

# 4. 함수: 유튜브 검색
def search_youtube(keyword):
    try:
        youtube = build('youtube', 'v3', developerKey=API_KEY)
        search_response = youtube.search().list(
            q=keyword, part='snippet', maxResults=12, type='video', order='viewCount'
        ).execute()

        video_ids = [item['id']['videoId'] for item in search_response['items']]
        channel_ids = [item['snippet']['channelId'] for item in search_response['items']]

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

tab1, tab2 = st.tabs(["🔍 영상 찾기", "📚 보관함"])

# [탭 1] 검색 기능
with tab1:
    # 폼(Form)을 써야 엔터칠 때 페이지가 새로고침 되는 걸 깔끔하게 처리함
    with st.form(key='search_form'):
        col1, col2, col3 = st.columns([4, 1, 1])
        with col1:
            query = st.text_input("키워드 검색", placeholder="예: 스마트스토어")
        with col2:
            sort_option = st.selectbox("정렬", ["🔥 성과순", "📅 최신순", "👁️ 조회수순"])
        with col3:
            st.write("") # 줄맞춤용
            search_btn = st.form_submit_button("검색 🔍")

    # 검색 버튼을 눌렀을 때만 데이터를 새로 가져옴
    if search_btn and query:
        with st.spinner('유튜브 분석 중...'):
            new_data = search_youtube(query)
            st.session_state.search_results = new_data # 결과를 기억장치에 저장!

    # 기억된 결과가 있으면 화면에 그리기
    if st.session_state.search_results:
        data = st.session_state.search_results
        
        # 정렬 로직 (보여줄 때만 정렬)
        sorted_data = sorted(data, key=lambda x: x['perf'] if sort_option == "🔥 성과순" else (x['date'] if sort_option == "📅 최신순" else x['views']), reverse=True)

        cols = st.columns(3)
        for idx, video in enumerate(sorted_data):
            with cols[idx % 3]:
                # 배지 HTML
                badges = f'<div class="badge bg-dark">{video["date"]}</div>'
                if video['is_new']: badges += '<div class="badge bg-green">✨ NEW</div>'
                if video['perf'] >= 100: badges += f'<div class="badge bg-red">🔥 성과 {int(video["perf"])}%</div>'
                elif video['perf'] >= 30: badges += f'<div class="badge bg-orange">👍 {int(video["perf"])}%</div>'

                st.markdown(f"""
                <div class="card">
                    <div class="thumb-container">
                        <img src="{video['thumb']}" class="thumb-img">
                        <div class="badge-overlay">{badges}</div>
                    </div>
                    <div class="info">
                        <a href="{video['url']}" target="_blank" class="title">{video['title']}</a>
                        <div class="meta"><span>📺 {video['channel']}</span></div>
                        <div class="meta"><span class="stats">👁️ {video['views']:,}회 / 구독 {video['subs']//1000}k</span></div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                # 저장 버튼 로직 (가장 중요한 수정 부분!)
                # 이미 저장된 영상인지 ID로 확인
                is_saved = any(v['id'] == video['id'] for v in st.session_state.archive)
                
                if is_saved:
                    st.button("✅ 저장됨", key=f"saved_{video['id']}", disabled=True)
                else:
                    # 버튼을 누르면 -> archive에 추가하고 -> rerun(새로고침)해서 버튼 상태를 '저장됨'으로 바꿈
                    if st.button("📥 보관함 담기", key=f"btn_{video['id']}"):
                        st.session_state.archive.append(video)
                        st.rerun()

# [탭 2] 보관함 기능
with tab2:
    st.header(f"내 보관함 ({len(st.session_state.archive)}개)")
    if len(st.session_state.archive) == 0:
        st.info("아직 저장된 영상이 없습니다.")
    else:
        arch_cols = st.columns(3)
        for idx, video in enumerate(reversed(st.session_state.archive)):
            with arch_cols[idx % 3]:
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
                if st.button("🗑️ 삭제", key=f"del_{video['id']}"):
                    st.session_state.archive.remove(video)
                    st.rerun()
