import streamlit as st
import pandas as pd
# import numpy as np
from pykrx import stock
import matplotlib.pyplot as plt
from prophet import Prophet
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import yfinance as yf
from pandas_datareader import data as pdr
from components import convert
import feedparser
from googleapiclient.discovery import build

st.set_page_config(page_title="AI Stock Search Engine", page_icon="🐍", layout="wide")

if convert.check_auth() == False:
    st.stop()

st.title("AI 주가 예측")

clear_button = st.sidebar.button("Clear Cache", key="clear", type="secondary")
if clear_button:
    st.cache_data.clear()

search_date = st.sidebar.date_input("기준일자", datetime.today())
today_button = st.sidebar.button("Today", key="today")
if today_button:
    search_date = datetime.today()

@st.cache_data
def load_data():
    stocks_KQ = pd.DataFrame({'종목코드':stock.get_market_ticker_list(market="KOSPI")})
    stocks_KQ['종목명'] = stocks_KQ['종목코드'].map(lambda x: stock.get_market_ticker_name(x))
    stocks_KQ['코드'] = stocks_KQ['종목코드'] + '.KS'
    
    stocks_KS = pd.DataFrame({'종목코드':stock.get_market_ticker_list(market="KOSDAQ")})
    stocks_KS['종목명'] = stocks_KS['종목코드'].map(lambda x: stock.get_market_ticker_name(x))
    stocks_KS['코드'] = stocks_KS['종목코드'] + '.KQ'

    stocks_KQKS = pd.concat([stocks_KQ, stocks_KS])
    
    # 전체 종목의 업종 
    krx_url = 'https://kind.krx.co.kr/corpgeneral/corpList.do?method=download&searchType=13'
    fdr_datastk_data = pd.read_html(krx_url, header=0, encoding='cp949')[0]  # 해당 site에서 table 추출 및 header는 가장 첫번째 행
    stk_data = fdr_datastk_data[['종목코드', '업종', '주요제품']].copy()  # 9개의 열 중 '회사명', '종목코드' 만 추출하여 dataframe 완성
    # 종목코드가 모두 6자리로 이루어져있지만 혹시 모르니, 6자리 미만 코드는 앞에 0을 채워넣어 6자리 숫자텍스트로 변환
    stk_data['종목코드'] = stk_data['종목코드'].astype(str).str.zfill(6) #6자리로 변환
    stock_list = pd.merge(stocks_KQKS, stk_data, on='종목코드', how='left')
    # 전체 종목의 펀더멘탈 지표 가져오기
    # 펀더멘탈 지표는 PER, PBR, EPS, BPS, DIV, DPS를 가져옵니다.
    currdate = search_date.strftime('%Y-%m-%d')
    stock_fud = pd.DataFrame(stock.get_market_fundamental_by_ticker(date=currdate, market="ALL"))
    stock_fud = stock_fud.reset_index()
    stock_fud.rename(columns={'티커':'종목코드'}, inplace=True)

    # result = pd.merge(stock_list, stock_fud, left_on='종목코드', right_on='종목코드', how='left')
    result = pd.merge(stock_list, stock_fud, on='종목코드', how='left')
    
    stock_price = stock.get_market_ohlcv_by_ticker(date=currdate, market="ALL")
    stock_price = stock_price.reset_index()
    stock_price.rename(columns={'티커':'종목코드'}, inplace=True)
    # result1 = pd.merge(result, stock_price, left_on='종목코드', right_on='종목코드', how='left')
    result1 = pd.merge(result, stock_price, on='종목코드', how='left')
    #코넥스 제거
    result1.dropna(subset=['종목명'], how='any', axis=0, inplace=True)
    
    # result1 = result1.replace([0], np.nan)    # 0값을 NaN으로 변경
    # result1 = result1.dropna(axis=0)      # NaN을 가진 행 제거
    # result1 = result1.sort_values(by=['PER'], ascending=True)
    result1 = result1.sort_values(by=['거래량'], ascending=False)
    result1['내재가치'] = (result1['BPS'] + (result1['EPS']) * 10) / 2
    result1['내재가치/종가'] = (result1['내재가치'] / result1['종가'])
    # st.write('result1')
    # st.write(result1.head())
    # result1.sort_values(by=['거래량'], ascending=False, inplace=)
    return result1

analy = load_data()
with st.expander(f'{search_date} 종목리스트 {analy.shape} ', expanded=False):
    st.write(analy)

# 검색 기능
text_search = st.text_input("AI Stock Search Engine", value="대우건설", placeholder='종목코드, 종목명, 업종, 주요제품으로 검색하세요')
m1 = analy["종목코드"].str.contains(text_search)
m2 = analy["종목명"].str.contains(text_search)
m3 = analy["업종"].str.contains(text_search)
m4 = analy["주요제품"].str.contains(text_search)

df_search = analy[m1 | m2 | m3 | m4]

anal_sel = st.empty()

anal_tube = st.container() # 유튜브 검색
anal_news = st.container() # 구글 뉴스

# 주가예측
col1, col2, col3 = st.columns(3)
with col1:
    anal_03t = st.empty()
    anal_03y= st.empty()
with col2:
    anal_rst = st.empty()
    anal_rsi = st.empty()
with col3:
    anal_10t = st.empty()
    anal_10y = st.empty()

anal_info = st.empty() # 회사개요

def analys(stock_name, stock_code):
    selected_analy = analy[analy['코드'] == stock_code]
    # 선택 종목 종가정보
    anal_sel.write(selected_analy)

    try:
        # 유튜브 검색
        youtube = build("youtube", "v3",developerKey=st.secrets["api_youtube"])
        search_response = youtube.search().list(
        q = stock_name,
        order = "relevance",
        part = "snippet",
        maxResults = 10
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

        with anal_tube:
            # st.write(result_json)
            gpt_feed_col = 5
            cols = st.columns(gpt_feed_col)
            for idx, item in enumerate(search_response['items']):
                if item['id']['kind'] == 'youtube#video':
                    # result_json[idx] = info_to_dict(item['id']['videoId'], item['snippet']['title'], item['snippet']['description'], item['snippet']['thumbnails']['medium']['url'])
                    # idx += 1
                    colsnum = ( idx % gpt_feed_col )
                    with cols[colsnum]:
                        st.image(item['snippet']['thumbnails']['medium']['url'])
    except Exception as e:
        st.write('관련 유튜브 정보가 없습니다.', e)
    
    try:
        # 구글 뉴스 검색
        # 현재 날짜에서 1일을 빼서 '1d' 형태의 문자열을 생성 (어제 날짜)
        date_since = (datetime.now() - timedelta(3)).strftime('%Y-%m-%d')
        rss_url = f'https://news.google.com/rss/search?q={stock_name}+after:{date_since}&hl=ko&gl=KR&ceid=KR:ko'

        feeds = feedparser.parse(rss_url)
        # pubDate를 datetime 객체로 파싱하기 위한 함수를 정의합니다.
        def parse_pubdate(entry):
            return datetime.strptime(entry.published, '%a, %d %b %Y %H:%M:%S %Z')

        # 각 항목의 pubDate를 기준으로 내림차순으로 정렬합니다 (최신 날짜가 먼저 오도록).
        sorted_feeds = sorted(feeds.entries, key=parse_pubdate, reverse=True)

        cols = anal_news.columns(5)
        # for idx, feed in enumerate(sorted_feeds[:10]): 
        for idx, feed in enumerate(sorted_feeds): 
            pub_date = parse_pubdate(feed)
            colsnum = ( idx % 5 )
            with cols[colsnum]:
                st.link_button(feed.title + f' {pub_date}', feed.link)
    except Exception as e:
        st.write('관련 뉴스 정보가 없습니다.', e)

    start_date = datetime(2010,3,1)
    end_date = datetime.today()
    yf.pdr_override()
    stock = pdr.get_data_yahoo(str(stock_code), start_date, end_date)
    get_stock_data = yf.Ticker(stock_code)
    if 'longBusinessSummary' in get_stock_data.info:
        anal_info.write(get_stock_data.info['longBusinessSummary'])
    stock_trunc = stock[:-30]

    df = pd.DataFrame({"ds":stock_trunc.index, "y":stock_trunc["Close"]})
    df.reset_index(inplace=True)
    del df ["Date"]
    m = Prophet(yearly_seasonality=True, daily_seasonality=True)
    m.fit(df)

    future = m.make_future_dataframe(periods=90, freq='D')
    forecast = m.predict(future)

    anal_10t.write(""" ### 10년 추세 """)

    fig2 = plt.figure(figsize=(8,3))
    plt.plot(stock.index, stock["Close"], label="real")
    plt.plot(forecast["ds"], forecast["yhat"], label="forecast")
    anal_10y.pyplot(fig2)

    # anal_03t.write(""" ### 향후 3개월 예측 """)
    anal_03t.write(f"### {stock_name} 향후 3개월 예측")
    idx_num = forecast.index[(forecast['ds'] >= datetime.today())]
    forecast = forecast[idx_num[0] - 120:] #마지막 10개?
    stock = stock[idx_num[0] - 120:]

    # 예측 그래프
    m.plot(forecast)
    m.plot_components(forecast)

    fig2 = plt.figure(figsize=(8,3))
    last_date = stock['Close'][-1:].index[0]
    last_dt = last_date.strftime('%Y-%m-%d')
    last_Close = round(stock['Close'][-1:][0])

    plt.plot(stock.index, stock["Close"], label="real")
    plt.annotate(f'Stock \n {last_Close} \n {last_dt}', 
                xy=(last_date, last_Close),
                xytext=(last_date + relativedelta(weeks=1), last_Close),
                weight='bold',
                arrowprops=dict(arrowstyle="->",
                                connectionstyle="arc3,rad=0.2"),
                )
    fore = forecast[['ds', 'yhat']][-1:]
    fore_date = fore.iloc[0]['ds']
    fore_dt = fore_date.strftime('%Y-%m-%d')
    fore_Close = round(fore.iloc[0]['yhat'])
    plt.plot(forecast["ds"], forecast["yhat"], label="forecast")
    plt.annotate(f'AI \n {fore_Close} \n {fore_dt}', 
                xy=(fore_date, fore_Close),
                xytext=(fore_date - relativedelta(weeks=16), fore_Close),
                weight='bold',
                arrowprops=dict(arrowstyle="->",
                                connectionstyle="arc3,rad=0.2"),
                )
    anal_03y.pyplot(fig2)

    anal_rst.write(""" ### 최근 3개월 RSI """)
    # RSI 예측 Plotting
    rsi_data = convert.calculate_rsi(stock)

    fig3 = plt.figure(figsize=(14, 7))
    plt.subplot(2, 1, 1)
    plt.plot(rsi_data.index, rsi_data['Close'], label='Close Price')
    plt.title('Close Price & RSI Graph')

    plt.subplot(2, 1, 2)
    plt.plot(rsi_data.index, rsi_data['RSI'], label='RSI', color='orange')
    plt.axhline(0, linestyle='--', alpha=0.5, color='black')
    plt.axhline(20, linestyle='--', alpha=0.5, color='red')
    plt.axhline(30, linestyle='--', alpha=0.5, color='red')
    plt.axhline(70, linestyle='--', alpha=0.5, color='blue')
    plt.axhline(80, linestyle='--', alpha=0.5, color='blue')
    plt.axhline(100, linestyle='--', alpha=0.5, color='black')
    anal_rsi.pyplot(fig3)

expander_stocks = st.container()
with expander_stocks:
    N_cards_per_row = 8
    if text_search:
        for n_row, row in df_search.reset_index().iterrows():
            i = n_row%N_cards_per_row
            if i==0:
                st.write("---")
                cols = st.columns(N_cards_per_row, gap="small")
            # draw the card
            with cols[n_row%N_cards_per_row]:
                search = st.button(f"**{row['종목명']}**", type="primary", key=f"{row['코드']}")
                st.markdown(f"****{row['업종']}****")
                st.caption(f"{row['주요제품']}")
                if search:
                    with st.spinner('Wait for it...'):
                        analys(f"{row['종목명']}", f"{row['코드']}")
st.stop()