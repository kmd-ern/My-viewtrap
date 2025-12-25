import streamlit as st
import pandas as pd
from googleapiclient.discovery import build
from datetime import datetime

# ==========================================
# 👇 님 API 키를 제가 미리 넣어뒀습니다. 바로 실행됩니다!
API_KEY = 'AIzaSyDk-YrjKCiJSnjoSIeSB46yroeZiCCSXWI'
# ==========================================

st.set_page_config(layout="wide", page_title="나만의 뷰트랩", page_icon="🎬")

# 스타일(디자인) 설정
st.markdown("""
<style>
    .card {
        background-color: white; border-radius: 10px; padding: 0px; margin-bottom: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1); overflow: hidden; border: 1px solid #eee;
    }
    .thumb-box { position: relative; width: 100%; aspect-ratio: 16/9; }
    .thumb-img { width: 100%; height: 100%; object-fit: cover; }
    .info-box { padding: 15px; }
    .title-text { 
        font-size: 16px; font-weight: bold; margin-bottom: 8px; height: 45px; 
        overflow: hidden; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; 
        text-decoration: none; color: #333;
    }
    .meta-text { font-size: 12px; color: #666; display: flex; justify-content: space-between; margin-top: 5px; }
    .stats-text { color: #d93025; font-weight: bold; font-size: 14px; margin-top: 5px; }
    .badge { position: absolute; top: 10px; left: 10px; padding: 4px 8px; border-radius: 5px; color: white; font-size: 11px; font-weight: bold; }
    .bg-red { background-color: rgba(255, 0, 0, 0.85); }
    .bg-green { background-color: rgba(40, 167, 69, 0.85); }
    .bg-dark { background-color: rgba(0, 0, 0, 0.7); }
</style>
""", unsafe_allow_html=True)

def search_youtube(keyword):
    try:
        youtube = build('youtube', 'v3', developerKey=API_KEY)
        search_response = youtube.search().list(
            q=keyword, part='snippet', maxResults=15, type='video', order='viewCount'
        ).execute()

        video_ids = [item['id']['videoId'] for item in search_response['items']]
        channel_ids = [item['snippet']['channelId'] for item in search_response['items']]

        vid_res = youtube.videos().list(part='statistics', id=','.join(video_ids)).execute()
        ch_res = youtube.channels().list(part='statistics', id=','.join(channel_ids)).execute()

        ch_subs = {ch['id']: int(ch['statistics'].get('subscriberCount', 0) or 1) for ch in ch_res['items']}
        
        results = []
        for i, item in enumerate(search_response['items']):
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
                'id': item['id']['videoId'], 'title': item['snippet']['title'],
                'thumb': item['snippet']['thumbnails']['medium']['url'],
                'channel': item['snippet']['channelTitle'], 'date': pub_date,
                'views': views, 'subs': subs, 'perf': (views / subs) * 100,
                'is_new': is_new, 'url': f"https://www.youtube.com/watch?v={item['id']['videoId']}"
            })
        return results
    except Exception as e:
        st.error(f"오류: {e}")
        return []

if 'archive' not in st.session_state: st.session_state['archive'] = []

st.title("🎬 My ViewTrap")
tab1, tab2 = st.tabs(["🕵️ 검색 & 분석", "📚 보관함"])

with tab1:
    col1, col2 = st.columns([3, 1])
    with col1: keyword = st.text_input("키워드 입력", placeholder="예: 무자본 창업")
    with col2: sort_option = st.selectbox("정렬", ["🔥 성과순", "📅 최신순", "👁️ 조회수순"])

    if st.button("분석 시작 🚀"):
        if keyword:
            with st.spinner('데이터 긁어오는 중...'):
                data = search_youtube(keyword)
                if sort_option == "🔥 성과순": data.sort(key=lambda x: x['perf'], reverse=True)
                elif sort_option == "📅 최신순": data.sort(key=lambda x: x['date'], reverse=True)
                else: data.sort(key=lambda x: x['views'], reverse=True)
                
                cols = st.columns(3)
                for idx, video in enumerate(data):
                    with cols[idx % 3]:
                        badges = f'<span class="badge bg-dark">{video["date"]}</span>'
                        if video['is_new']: badges += '<span class="badge bg-green" style="left:80px;">✨ NEW</span>'
                        if video['perf'] >= 100: badges += '<div class="badge bg-red" style="top:35px;">🔥 대박 성과</div>'
                        
                        st.markdown(f"""
                        <div class="card">
                            <div class="thumb-box"><img src="{video['thumb']}" class="thumb-img">{badges}</div>
                            <div class="info-box">
                                <a href="{video['url']}" target="_blank" class="title-text">{video['title']}</a>
                                <div class="meta-text"><span>📺 {video['channel']}</span><span>👥 {video['subs']//1000}k</span></div>
                                <div class="stats-text">👁️ {video['views']:,}회</div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                        if st.button("💾 저장", key=f"save_{video['id']}"):
                            if not any(v['id'] == video['id'] for v in st.session_state['archive']):
                                st.session_state['archive'].append(video)
                                st.success("저장됨!")

with tab2:
    st.header(f"📚 보관함 ({len(st.session_state['archive'])}개)")
    if len(st.session_state['archive']) > 0:
        df = pd.DataFrame(st.session_state['archive'])
        st.download_button("📥 엑셀 저장", df.to_csv(index=False).encode('utf-8-sig'), "archive.csv", "text/csv")
        saved_cols = st.columns(3)
        for idx, video in enumerate(st.session_state['archive']):
            with saved_cols[idx % 3]:
                st.image(video['thumb'], use_container_width=True)
                st.write(f"**{video['title']}**")
