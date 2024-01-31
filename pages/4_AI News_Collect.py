import streamlit as st
import openai
from components import convert
import tiktoken
import feedparser
from datetime import datetime, timedelta
import deepl
from googleapiclient.discovery import build
from components.db_manager import DBManagerNews

st.set_page_config(page_title="AI NEWS", page_icon="🐍", layout='centered', initial_sidebar_state='auto')

if convert.check_auth() == False:
    st.stop()

st.title("AI NEWS COLLECT 🌎")

db = DBManagerNews()
translator = deepl.Translator(st.secrets["api_deepl"])

clear_button = st.sidebar.button("새 대화 시작", type="primary", key="clear_newss")
if clear_button:
    st.cache_data.clear()
    st.session_state['nmessages'] = [
        {"role": "system", "content": "You are a helpful assistant.", "hide": False}
    ]

delete_button = st.sidebar.button("뉴스 DB 초기화", type="primary", key="del_news")
if delete_button:
    db.del_news()

get_news_list = ['한국', '미국', '캐나다', '나이지리아', '베트남', '일본', '모로코', 'UAE', '인도네시아', '말레이시아', '짐바브웨', '파키스탄', '사우디아라비아', '에티오피아'] #, '리비아',  '이라크', '캄보디아', '오만', '투르크']
get_news_range = st.multiselect("국가를 선택해주세요 - 국가 변경 시 수집 시간이 조금 걸려요", get_news_list, ['한국', '베트남', '나이지리아'])
gpt_feed_max = st.slider('최신뉴스 갯수를 자유롭게 변경하세요 ', 0, 50, 5)

def parse_pubdate(entry):
    published_dt = datetime.strptime(entry.published, '%a, %d %b %Y %H:%M:%S %Z')
    formatted_str = published_dt.strftime('%Y. %m. %d')
    return formatted_str

def get_news_feed(news_range):
    sorted_all_feeds = []
    for conutry in get_news_range:
        nation = ''
        if conutry == '한국': # 'KR':
            rss_url = f'https://news.google.com/rss?hl=ko&gl=KR&ceid=KR:ko'
            nation = '🇰🇷 '
            # nation = '!https://newsapi.org/images/flags/kr.svg'
        elif conutry =='캐나다': # 'US':
            rss_url = f'https://news.google.com/rss?hl=en-CA&gl=CA&ceid=CA:en'
            nation = '🇨🇦 '
        elif conutry =='미국': # 'US':
            rss_url = f'https://news.google.com/rss?h|=en-US&gl=US&ceid=US:en'
            nation = '🇺🇸 '
        elif conutry == '일본': #'JP':
            rss_url = f'https://news.google.com/rss?hl=ja&gl=JP&ceid=JP:ja'
            nation = '🇯🇵 '
        elif conutry == '베트남': #'VN':
            rss_url = f'https://news.google.com/rss?hl=vi&gl=VN&ceid=VN:vi'
            nation = '🇻🇳 '
        elif conutry == '나이지리아': #'NG':
            rss_url = f'https://news.google.com/rss??hl=en-NG&gl=NG&ceid=NG:en'
            nation = '🇳🇬 '
        elif conutry == '짐바브웨': #'ZW':
            rss_url = f'https://news.google.com/rss?hl=en-ZW&gl=ZW&ceid=ZW:en'
            nation = '🇿🇼 '
        elif conutry == '인도네시아' :
            rss_url = f'https://news.google.com/rss?hl=en-ID&gl=ID&ceid=ID:en'
            nation = '🇮🇩 '
        elif conutry == '파키스탄' :
            rss_url = f'https://news.google.com/rss?hl=en-PK&gl=PK&ceid=PK:en'
            nation = '🇵🇰 '
        elif conutry == '싱가포르' :
            rss_url = f'https://news.google.com/rss?hl=en-SG&gl=SG&ceid=SG:en'
            nation = '🇸🇬 '
        elif conutry == '사우디아라비아' :
            rss_url = f'https://news.google.com/rss?hl=ar&gl=SA&ceid=SA:ar'
            nation = '🇸🇦 '
        elif conutry == '에티오피아' :
            rss_url = f'https://news.google.com/rss?hl=en-ET&gl=ET&ceid=ET:en'
            nation = '🇪🇹 '
        elif conutry == '모로코' :
            rss_url = f'https://news.google.com/rss?hl=fr&gl=MA&ceid=MA:fr'
            nation = '🇲🇦 '
        elif conutry == 'UAE' :
            rss_url = f'https://news.google.com/rss?hl=ar&gl=AE&ceid=AE:ar'
            nation = '🇦🇪 '
        elif conutry == '말레이시아' :
            rss_url = f'https://news.google.com/rss?hl=ms-MY&gl=MY&ceid=MY:ms'
            nation = '🇲🇾 '
        # elif conutry == '이라크' : '🇮🇶'
        # elif conutry == '리비아' : '🇱🇾'
        # elif conutry == '캄보디아' : '🇰🇭'
        # elif conutry == '오만' : '🇴🇲'
        # elif conutry == '투르크메니스탄' : '🇹🇲'

    # https://news.google.com/home?hl=en-ZA&gl=ZA&ceid=ZA:en 남아프리카
    # https://news.google.com/home?hl=ar&gl=EG&ceid=EG:ar 이집트
    # https://news.google.com/home?hl=te&gl=IN&ceid=IN:te 인도
    # https://news.google.com/home?hl=th&gl=TH&ceid=TH:th 태국
        else:
            return []
        # nation = '[' + conutry + ']'
        feeds = feedparser.parse(rss_url)
        st.write(feeds)

        # 각 항목의 pubDate를 기준으로 내림차순으로 정렬합니다 (최신 날짜가 먼저 오도록).
        sorted_feeds = sorted(feeds.entries, key=parse_pubdate, reverse=True)
        # sorted_feeds = sorted_feeds[:gpt_feed_max]
        for idx, feed in enumerate(sorted_feeds):
            feed['num'] = idx + 1
            feed['nation'] = nation
            feed['conutry'] = conutry
        sorted_all_feeds += sorted_feeds

    return sorted_all_feeds

def get_news_feeds(get_news_range, gpt_feed_max):

    # ID nation conutry title deepl papago google link published updated_at
    # deepl = translator.translate_text(feed['title'], target_lang='KO')

    gpt_feeds = '''

    #입력문
    '''

    gpt_feed_col = 3

    sorted_all_feeds = get_news_feed(get_news_range)
    # with st.expander('수집 내용 보기', expanded=False):
    #     st.write(sorted_all_feeds)

    cols = st.columns(gpt_feed_col)

    updated_at = datetime.now()

    for idx, feed in enumerate(sorted_all_feeds): 
        st.write(feed)
        if gpt_feed_max < feed.num:
            continue
        result = db.get_news(feed)
        if len(result) != 0:
            continue
        
        if feed.conutry == '한국':
            deepl = ''
            chatgpt = ''
        else:
            deepl = translator.translate_text(feed['title'], target_lang='KO')

            prompt = f"아래 문장을 한국어로 번역해줘 #아래:\n\n{feed.title}"
            messages = [{"role": "user", "content": prompt}]
            response = openai.chat.completions.create(
                model=st.session_state["openai_model"],
                messages=messages,
                # max_tokens=60,  # 필요한 경우 어휘 수를 조정하십시오
                # temperature=0.3  # 결과의 창의성을 조정하는 파라미터 (낮은 값 = 더 리터럴한 번역)
            )
            chatgpt = response.choices[0].message.content 
        db.save_news(feed, deepl, chatgpt, updated_at)

        pub_date = parse_pubdate(feed)
        colsnum = ( idx % gpt_feed_col )
        with cols[colsnum]:
            st.link_button(feed.nation + ' ' + feed.title + '\n\n[GPT번역] '+ str(chatgpt) + '\n\n[DEEPL번역] ' + str(deepl) + '\n\n' + f' {pub_date}', feed.link)
        gpt_feeds += f'[국가: {feed.conutry}] [기사] {feed.title} \n\n'
    gpt_feeds += '''
    #출력형식       
    [한국] - 긍정 : 긍정 또는 부정관련 단어 3개
    1. 기사
    2. 기사
    [미국] - 부정 : 긍정 또는 부정관련 단어 3개
    1. 기사
    2. 기사
        '''
    return gpt_feeds

# date_since = (datetime.now() - timedelta(3)).strftime('%Y-%m-%d')
# stock_name = '건설'
# rss_url = f'https://news.google.com/rss/search?q={stock_name}+after:{date_since}&hl=ko&gl=KR&ceid=KR%3Ako'
# feeds = feedparser.parse(rss_url)
# st.write(feeds)

if st.button('수집하기', type="primary"):
    gpt_feeds = get_news_feeds(get_news_range, gpt_feed_max)

st.stop()

# @st.cache_data
def get_tube_feed():
    youtube = build("youtube", "v3",developerKey=st.secrets["api_youtube"])
    search_response = youtube.search().list(
    q = '건설',
    order = "relevance",
    part = "snippet",
    maxResults = 9
    ).execute()

    def info_to_dict(videoId, title, description, url):
        result = {
            "videoId": videoId,
            "title": title,
            "description": description,
            "url": url
        }
        return result

    result_json = {}
    idx =0
    for item in search_response['items']:
        if item['id']['kind'] == 'youtube#video':
            result_json[idx] = info_to_dict(item['id']['videoId'], item['snippet']['title'], item['snippet']['description'], item['snippet']['thumbnails']['medium']['url'])
            idx += 1
    
    gpt_feed_col = 3
    cols = st.columns(gpt_feed_col)
    for idx, item in enumerate(search_response['items']):
        if item['id']['kind'] == 'youtube#video':
            colsnum = ( idx % gpt_feed_col )
            with cols[colsnum]:
                st.image(item['snippet']['thumbnails']['medium']['url'])

get_tube_feed()

if "nmessages" not in st.session_state:
    st.session_state.nmessages = []

for message in st.session_state.nmessages:
    if message["hide"] == False:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

prompt = st.chat_input("Say something")

prompt1_button = st.button("GPT 요약하기", type="primary", key="prompt1")
if prompt1_button:
    gpt_feed = '''
    #명령문
    아래의 제약조건과 입력문을 바탕으로
    [국가]별로 구분해서 기사를 한국어로 요약해서 출력해주세요
    요약 후에는 '긍정' 또는 '부정' 둘 중 하나의 단어로만 대답해주세요
    추가 설명없이 긍정 또는 부정과 관련된 단어 3개만 작성해주세요
    
    #제약조건
    요점을 명확히 한다
    문장은 간결하게 알기 쉽게 쓴다

    '''
    gpt_feeds = gpt_feed + gpt_feeds

    prompt = gpt_feeds
    st.session_state['nmessages'] = [
        {"role": "user", "content": gpt_feeds, 'hide': True}
    ]

prompt2_button = st.button("건설 뉴스 요약하기", type="primary", key="prompt2")
if prompt2_button:

    gpt_feed = '''
    #명령문
    아래의 제약조건과 입력문을 바탕으로
    [국가]별로 건설 관련 기사를 한국어로 요약해서 출력해주세요
    요약 후에는 '긍정' 또는 '부정' 둘 중 하나의 단어로만 대답해주세요
    추가 설명없이 긍정 또는 부정과 관련된 단어 3개만 작성해주세요
    
    #제약조건
    건설 관련 기사만 출력한다
    건설 관련 기사가 없으면 건설관련 뉴스가 없습니다 라고만 대답한다
    건설 관련 기사가 없는 국가는 출력하지 않는다
    요점을 명확히 한다
    문장은 간결하게 알기 쉽게 쓴다
    한국어로 출력한다

    '''
    gpt_feeds = gpt_feed + gpt_feeds
    prompt = gpt_feeds

if prompt:
    if prompt1_button or prompt2_button :
        # 기존 유저 메시지는 삭제하기
        st.session_state.nmessages = [
            message for message in st.session_state.nmessages
            if message["role"] != "user" or message["hide"] != True
        ]
        st.session_state.nmessages.append({"role": "user", "content": prompt, "hide": True})

    else:
        st.session_state.nmessages.append({"role": "user", "content": prompt, "hide": False})
        with st.chat_message("user"):
            st.markdown(prompt)

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        for response in openai.chat.completions.create(
            model=st.session_state["openai_model"],
            # model = 'gpt-3.5-turbo-1106',
            messages=[
                {"role": m["role"], "content": m["content"]}
                for m in st.session_state.nmessages
            ],
            stream=True,
        ):
            for chunk in response.choices:
                if chunk.finish_reason == 'stop':
                    break
                full_response += chunk.delta.content
            message_placeholder.markdown(full_response + "▌")
        message_placeholder.markdown(full_response)
    st.session_state.nmessages.append({"role": "assistant", "content": full_response, "hide": False})

tokenizer = tiktoken.get_encoding("cl100k_base")
tokenizer = tiktoken.encoding_for_model("gpt-4-1106-preview") # gpt-3.5-turbo

with st.expander('프롬프트 보기', expanded=False):
    st.write(st.session_state)

message_cnt = 0
token_size = 0
for message in st.session_state['nmessages']:
    if message['role'] == 'system':
        continue
    encoding_result = tokenizer.encode(message['content'])
    token_size = token_size + len(encoding_result)
    message_cnt = message_cnt + 1

if token_size != 0:
    st.caption(f"{message_cnt} 개의 대화에서 {token_size} 토큰을 사용하였습니다. 예상비용은 {round(token_size * 0.00001, 2)}$ 입니다")
