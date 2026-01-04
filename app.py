import streamlit as st
from googleapiclient.discovery import build
from datetime import datetime

# ==========================================
# 👇 API 키 (그대로 두세요)
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

# 3. 데이터 저장소
if 'archive' not in st.session_state:
    st.session_state.archive = []
if 'search_results' not in st.session_state:
    st.session_state.search_results = []

# 4. 함수: 유튜브 검색 (옵션 추가됨: order_mode)
def search_youtube(keyword, order_mode):
    try:
        youtube = build('youtube', 'v3', developerKey=API_KEY)
        
        # order_mode에 따라 'viewCount'(조회수순) 또는 'date'(최신순)으로 요청
        search_response = youtube.search().list(
            q=keyword, part='snippet', maxResults=12, type='video', order=order_mode
        ).execute()

        video_ids = [item['id']['videoId'] for item in search_response['items']]
        channel_ids = [item['snippet']['channelId'] for item in search_response['items']]

        if not video_ids:
            return []

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

# 5. 화면 구성
st.title("📱 My ViewTrap
