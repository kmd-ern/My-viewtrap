import streamlit as st
import pandas as pd
from googleapiclient.discovery import build
from datetime import datetime

# ==========================================
# 👇 API 키 설정 (그대로 두시면 됩니다)
API_KEY = 'AIzaSyDk-YrjKCiJSnjoSIeSB46yroeZiCCSXWI'
# ==========================================

# 1. 페이지 설정
st.set_page_config(layout="wide", page_title="뷰트랩 V3", page_icon="🚀")

# 2. 스타일 (CSS) - 카드 디자인 및 배지
st.markdown("""
<style>
    .card {
        background-color: white; border-radius: 12px; padding: 0px; margin-bottom: 20px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1); overflow: hidden; border: 1px solid #eee;
        transition: transform 0.2s;
    }
    .card:hover { transform: translateY(-3px); box-shadow: 0 4px 12px rgba(0,0,0,0.15); }
    .thumb-box { position: relative; width: 100%; aspect-ratio: 16/9; }
    .thumb-img { width: 100%; height: 100%; object-fit: cover; }
    
    .info-box { padding: 15px; }
    .title-text { 
        font-size: 15px; font-weight: bold; margin-bottom: 8px; height: 42px; 
        overflow: hidden; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; 
        text-decoration: none; color: #222; line-height: 1.4;
    }
    .meta-row { display: flex; justify-content: space-between; align-items: center; font-size: 12px; color: #666; margin-top: 8px;}
    .stats-main { color: #d93025; font-weight: 800; font-size: 14px; }
    
    /* 배지 스타일 */
    .badge { position: absolute; padding: 3px 6px; border-radius: 4px; color: white; font-size: 10px; font-weight: bold; z-index: 2;}
    .badge-date { top: 8px; left: 8px; background-color: rgba(0, 0, 0, 0.7); }
    .badge-new { top: 8px; left: 80px; background-color: #28a745; }
    .badge-perf { bottom: 8px; right: 8px; background-color: #dc3545; font-size: 11px; padding: 4px 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.3); }
    .badge-good { bottom: 8px; right: 8px; background-color: #fd7e14; font-size: 11px; padding: 4px 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.3); }
    
    /* 탭 스타일 조정 */
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] { height: 50px; white-space: pre-wrap; background-color: #f8f9fa; border-radius: 5px; padding: 10px 20px; font-weight: bold;}
    .stTabs [aria-selected="true"] { background-color: #e7f5ff; color: #007bff; border-bottom: 2px solid #007bff;}
</style>
""", unsafe_allow_html=True)

# 3. 데이터 수집 함수
def search_youtube(keyword):
    try:
        youtube = build('youtube', 'v3', developerKey=API_KEY)
        # 트렌드 파악을 위해 20개 가져오기
        search_response = youtube.search().list(
            q=keyword, part='snippet', maxResults=20, type='video', order='viewCount'
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
            
            # 성과도 계산
            perf = (views / subs) * 100
            
            # 최신 영상 여부 (1달 이내)
            is_new = False
            try:
                date_obj = datetime.strptime(pub_date, "%Y-%m-%d")
                if (datetime.now() - date_obj).days <= 30: is_new = True
            except: pass

            results.append({
                'id': item['id']['videoId'], 'title': item['snippet']['title'],
                'thumb': item['snippet']['thumbnails']['medium']['url'],
                'channel': item['snippet']['channelTitle'], 'date': pub_date,
                'views': views, 'subs': subs, 'perf': perf,
                'is_new': is_new, 'url': f"https://www.youtube.com/watch?v={item['id']['videoId']}"
            })
        return results
    except Exception as e:
        st.error(f"API 오류: {e}")
        return []

# 카드 그리는 함수 (반복 줄이기)
def render_grid(data_list):
    cols = st.columns(3) # 3열 배치
    for idx, video in enumerate(data_list):
        with cols[idx % 3]:
            # 배지 HTML 조립
            badges = f'<span class="badge badge-date">{video["date"]}</span>'
            if video['is_new']: badges += '<span class="badge badge-new">✨ NEW</span>'
            
            perf_badge = ""
            if video['perf'] >= 100: perf_badge = f'<div class="badge badge-perf">🔥 기여도 {int(video["perf"])}%</div>'
            elif video['perf'] >= 30: perf_badge = f'<div class="badge badge-good">👍 기여도 {int(video["perf"])}%</div>'
            
            st.markdown(f"""
            <div class="card">
                <div class="thumb-box">
                    <img src="{video['thumb']}" class="thumb-img">
                    {badges}
                    {perf_badge}
                </div>
                <div class="info-box">
                    <a href="{video['url']}" target="_blank" class="title-text">{video['title']}</a>
                    <div class="meta-row">
                        <span>📺 {video['channel']}</span>
                        <span>👥 {video['subs']//1000}k</span>
                    </div>
                    <div class="meta-row">
                        <span class="stats-main">👁️ {video['views']:,}회</span>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # 저장 버튼
            if st.button("💾 보관함 담기", key=f"btn_{video['id']}_{datetime.now().microsecond}"):
                if 'archive' not in st.session_state: st.session_state['archive'] = []
                if not any(v['id'] == video['id'] for v in st.session_state['archive']):
                    st.session_state['archive'].append(video)
                    st.toast(f"✅ 저장 완료: {video['title'][:10]}...")
                else:
                    st.toast("⚠️ 이미 보관함에 있습니다.")

# 4. 세션 상태 (검색 결과 저장용)
if 'search_results' not in st.session_state: st.session_state['search_results'] = None
if 'archive' not in st.session_state: st.session_state['archive'] = []

# ==========================================
# 5. 메인 화면 구성
# ==========================================
st.title("🚀 My ViewTrap Analysis")

# 검색창 (맨 위에 고정)
with st.container():
    c1, c2 = st.columns([4, 1])
    with c1:
        keyword = st.text_input("분석할 키워드를 입력하세요", placeholder="예: 무자본 창업, 다이어트 식단")
    with c2:
        st.write("") # 줄맞춤용
        st.write("")
        search_btn = st.button("분석 시작 🔍", use_container_width=True, type="primary")

# 검색 로직
if search_btn and keyword:
    with st.spinner(f"YouTube에서 '{keyword}' 데이터를 긁어오는 중..."):
        st.session_state['search_results'] = search_youtube(keyword)

# ---------------------------------------------------------
# 탭 기능 구현 (여기가 핵심!)
# ---------------------------------------------------------
if st.session_state['search_results']:
    data = st.session_state['search_results']
    
    st.write("---")
    st.subheader(f"📊 '{keyword}' 분석 결과")
    
    # 탭 3개 생성
    tab_perf, tab_views, tab_new = st.tabs(["🔥 기여도순 (추천)", "👁️ 조회수순", "📅 최신순"])
    
    # 1. 기여도순 탭
    with tab_perf:
        sorted_data = sorted(data, key=lambda x: x['perf'], reverse=True)
        render_grid(sorted_data)
        
    # 2. 조회수순 탭
    with tab_views:
        sorted_data = sorted(data, key=lambda x: x['views'], reverse=True)
        render_grid(sorted_data)
        
    # 3. 최신순 탭
    with tab_new:
        sorted_data = sorted(data, key=lambda x: x['date'], reverse=True)
        render_grid(sorted_data)

# ---------------------------------------------------------
# 보관함 (사이드바 또는 아래쪽)
# ---------------------------------------------------------
with st.expander("📂 내 보관함 열기 (저장된 영상 확인)", expanded=False):
    if len(st.session_state['archive']) > 0:
        st.write(f"총 {len(st.session_state['archive'])}개의 영상이 저장되었습니다.")
        
        # 엑셀 다운로드
        df = pd.DataFrame(st.session_state['archive'])
        st.download_button("📥 엑셀로 내보내기", df.to_csv(index=False).encode('utf-8-sig'), "my_viewtrap.csv", "text/csv")
        
        # 보관함 그리드
        cols = st.columns(3)
        for idx, video in enumerate(st.session_state['archive']):
            with cols[idx % 3]:
                st.markdown(f"**{video['title']}**")
                st.image(video['thumb'])
                st.caption(f"조회수: {video['views']:,}회")
    else:
        st.info("아직 저장된 영상이 없습니다.")
