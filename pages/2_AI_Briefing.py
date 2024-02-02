import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import altair as alt
import openai
from components import convert
import feedparser
import sqlite3
from components.db_manager import DBManagerEconomic

st.set_page_config(page_title="AI DW", page_icon="🐍", layout='wide')
if convert.check_auth() == False:
    st.stop()

st.header(f"일하기 좋은 회사 1위 대우건설 VS 동종사 👋")

db = DBManagerEconomic()

clear_button = st.sidebar.button("Clear Cache", key="clear")
if clear_button:
    st.cache_data.clear()

progress_stock = st.progress(0) # 주가정보 로딩바
status_stock = st.empty() # 주가정보 로딩바

st.write(""" ### 🤖 AI 브리핑 """)
dt_today = datetime.today().strftime('%Y년 %m월 %d일 %H시%M분')
with st.expander(f"{dt_today} by {st.session_state['openai_model']}", expanded=True):
    ai_stock_text = st.empty() # 주가정보 ChatGPT 답변
    anal_news = st.container()

search_date = st.sidebar.date_input("기준일자", datetime.today())
today_button = st.sidebar.button("Today", key="today")
if today_button:
    search_date = datetime.today()

dt_range = st.sidebar.selectbox("기간",['1주', '1개월', '3개월', '6개월', '1년', '3년', '10년'], index=2)
if "dt_range" in st.session_state:
    if dt_range != st.session_state["dt_range"]:
        st.session_state["dt_range"] = dt_range
        st.cache_data.clear()
else:
    st.session_state["dt_range"] = dt_range

end_date = search_date
if dt_range == '1주':
    start_date = datetime.today() - relativedelta(weeks=1)
elif dt_range == '1개월':
    start_date = datetime.today() - relativedelta(months=1)
elif dt_range == '3개월':
    start_date = end_date - relativedelta(months=3)
elif dt_range == '6개월':    
    start_date = datetime.today() - relativedelta(months=6)
elif dt_range == '1년':    
    start_date = datetime.today() - relativedelta(years=1)
elif dt_range == '3년':    
    start_date = datetime.today() - relativedelta(years=3)
elif dt_range == '10년':    
    start_date = datetime.today() - relativedelta(years=10)

##########################################################################
### 1. 주요 뉴스 ##########################################################
##########################################################################
def parse_pubdate(entry):
    published_dt = datetime.strptime(entry.published, '%a, %d %b %Y %H:%M:%S %Z')
    formatted_str = published_dt.strftime('%Y. %m. %d')
    return formatted_str

date_since = (datetime.now() - timedelta(3)).strftime('%Y-%m-%d')
stock_name = '건설'
rss_url = f'https://news.google.com/rss/search?q={stock_name}+after:{date_since}&hl=ko&gl=KR&ceid=KR%3Ako'
feeds = feedparser.parse(rss_url)
sorted_feeds = sorted(feeds.entries, key=parse_pubdate, reverse=True)

cols = anal_news.columns(5)
for idx, feed in enumerate(sorted_feeds[:10]): 
    pub_date = parse_pubdate(feed)
    colsnum = ( idx % 5 )
    with cols[colsnum]:
        st.link_button(feed.title + f' {pub_date}', feed.link)

##########################################################################
### 1. 주요 경제지표 ######################################################
##########################################################################
status_Text = '1/3 주요 지표를 불러오는 중입니다...'
progress_stock.progress(0)
status_stock.text(f"{status_Text}")
products = [
    {'name': '달러인덱스', 'symbol': 'DX-Y.NYB'}
    ]
multi_products = st.sidebar.multiselect(
    "지표를 선택하세요",
    [
        "크루드오일 CL=F",
        "금 GC=F",
        "은 SI=F",
        # "구리 GH=F",
        "S&P500 ^GSPC",
        "천연가스 LNG",
        "10년물 ^TNX",
        "DBC DBC"
        # "BTC-USD BTC-USD"
        ],
    [ #초기 선택
        "크루드오일 CL=F",
        "금 GC=F",
        "은 SI=F",
        # "구리 GH=F",
        "S&P500 ^GSPC",
        "천연가스 LNG",
        "10년물 ^TNX",
        "DBC DBC"
        # "BTC-USD BTC-USD"
        ]
    )
for product in multi_products:
    words = product.split()
    products.append({'name': words[0], 'symbol': words[1]})

@st.cache_data
def load_eco_data(products):
    change_eco_df = pd.DataFrame() # 변동률
    last_df = pd.DataFrame() # 변동률    
    for idx, product in enumerate(products):

        get_product_data = yf.Ticker(product['symbol'])
        product_df = get_product_data.history(period='1d', start=start_date, end=end_date)

        # try: # 저장된 이력이 가져오기
        #     product_df = db.get_eco(product['symbol'], start_date, end_date) # 경제지표 불러오기
        #     st.write('try')
        #     st.write(product_df)
        # except:
        #     get_product_data = yf.Ticker(product['symbol'])
        #     product_df = get_product_data.history(period='1d', start=start_date, end=end_date)
        #     st.write('except')
        #     st.write(product_df)
        #     db.save_eco(product['symbol'], product_df) # 경제지표 저장

        # st.write(product_df)
        # st.write (product_df.dtypes)
        # st.stop()

        # 일간변동률, 누적합계
        product_df['dpc'] = (product_df.Close/product_df.Close.shift(1)-1)*100
        product_df['cs'] = round(product_df.dpc.cumsum(), 2)

        change2_df = pd.DataFrame(
            {
                'Date2': product_df.index,
                'symbol': product['name'],
                'Close': round(product_df.Close, 2),
                'rate': product_df.cs,
                }
        )
        change2_df.reset_index(drop=True, inplace=True)
        change2_df.columns = ['Date', 'symbol', 'Close', 'rate']
        change_eco_df = pd.concat([change_eco_df, change2_df])

        last2_df = pd.DataFrame(product_df.iloc[len(product_df.index)-1]).T
        last3_df = pd.DataFrame(
            {
                'symbol': product['name'],
                'Date': last2_df.index,
                'Close': last2_df.Close, 
                'rate': last2_df.cs,
                }
        )
        last_df = pd.concat([last_df, last3_df])
    return change_eco_df, last_df

change_eco_df, last_df = load_eco_data(products)




# st.write(f""" ### 📈 주요지표 {dt_range} 변동률 """)
base = alt.Chart(change_eco_df).encode(x='Date:T')
columns = sorted(change_eco_df.symbol.unique())
selection = alt.selection_point(
    fields=['Date'], nearest=True, on='mouseover', empty=False, clear='mouseout'
)
lines_eco = base.mark_line().encode(
    x = alt.X('Date:T', title=''),
    y = alt.Y('rate:Q', title=''),
    color = alt.Color('symbol:N', title='지표', legend=alt.Legend(
        orient='bottom', 
        direction='horizontal',
        titleAnchor='end'))
)
points_eco = lines_eco.mark_point().transform_filter(selection)

rule_eco = base.transform_pivot(
    'symbol', value='Close', groupby=['Date']
    ).mark_rule().encode(
    opacity=alt.condition(selection, alt.value(0.3), alt.value(0)),
    tooltip=[alt.Tooltip(c, type='quantitative') for c in columns]
).add_params(selection)

text_data = last_df
text_data.reset_index(drop=True, inplace=True)
text_sort_eco = text_data.sort_values(by=['rate'], ascending=False)
text_sort_eco.reset_index(drop=True, inplace=True)
text_data3 = pd.DataFrame(text_sort_eco.loc[0]).T
if len(text_sort_eco.index) > 1:
    text_data3.loc[1] = text_sort_eco.loc[len(text_sort_eco.index)-1]
if len(text_sort_eco.index) > 2:
    text_data3.loc[2] = text_sort_eco.loc[round(len(text_sort_eco.index)/2)]

labels_eco = alt.Chart(text_data3).mark_text(
    # point=True,
    fontWeight=600,
    fontSize=15,
    # color='white',
    align='left',
    dx=15,
    dy=-8
).encode(
    x = alt.X('Date:T', title=''),
    # y = alt.Y('rate:Q', title=rate_text),
    y = alt.Y('rate:Q', title=''),
    # y = 'rate:Q',
    text=alt.Text('rate:Q', format='.1f'),
    color = alt.Color('symbol:N', title='')
)

labels2_eco = alt.Chart(text_data3).mark_text(
    # point=True,
    fontWeight=600,
    fontSize=15,
    # color='white',
    align='left',
    dx=15,
    dy=10
).encode(
    x = alt.X('Date:T', title=''),
    # y = alt.Y('rate:Q', title=rate_text),
    y = alt.Y('rate:Q', title=''),
    text=alt.Text('symbol:N', title=''),
    color = alt.Color('symbol:N', title='')
)

# st.altair_chart(lines_eco + rule_eco + points_eco + labels_eco + labels2_eco, 
#                 use_container_width=True)

##########################################################################
### 2. 환율 정보 #########################################################
##########################################################################
status_Text = '2/3 환율 정보를 불러오는 중입니다...'
progress_stock.progress(0)
status_stock.text(f"{status_Text}")
currencies = [
    {'name': ' USD/KRW', 'symbol': 'KRW=X'}
    ]
multi_currencies = st.sidebar.multiselect(
    "통화를 선택하세요",
    [
        'USD/AED AED=X', 
        # 'USD/AUD AUD=X', 미사용
        'USD/BWP BWP=X',
        # 'USD/CAD CAD=X', 미사용
        # 'USD/CHF CHF=X', 미사용
        'USD/CNY CNY=X',
        'USD/COP COP=X',
        'USD/DZD DZD=X',
        'USD/ETB ETB=X',
        'USD/HKD HKD=X',
        'USD/IDR IDR=X',
        'USD/INR INR=X',
        'USD/IRR IRR=X',
        'USD/JOD JOD=X',
        'USD/JPY JPY=X',
        'USD/LYD LYD=X',
        'USD/MAD MAD=X',
        'USD/MYR MYR=X',
        'USD/MZN MZN=X',
        'USD/NGN NGN=X',
        'USD/OMR OMR=X',
        'USD/PGK PGK=X',
        'USD/QAR QAR=X',
        'USD/SAR SAR=X',
        'USD/SGD SGD=X',
        # 'USD/VED VED=X', 미사용
        'USD/VND VND=X',
        'USD/ZAR ZAR=X',
        # 'USD/ZMK ZMK=X', 미사용
        'USD/ZMW ZMW=X'
        ],
    [ #초기 선택
         'USD/AED AED=X', 
        # 'USD/AUD AUD=X', 미사용
        # 'USD/BWP BWP=X',
        # 'USD/CAD CAD=X', 미사용
        # 'USD/CHF CHF=X', 미사용
        'USD/CNY CNY=X',
        # 'USD/COP COP=X',
        # 'USD/DZD DZD=X',
        # 'USD/ETB ETB=X',
        # 'USD/HKD HKD=X',
        # 'USD/IDR IDR=X',
        # 'USD/INR INR=X',
        'USD/IRR IRR=X',
        # 'USD/JOD JOD=X',
        'USD/JPY JPY=X',
        'USD/LYD LYD=X',
        # 'USD/MAD MAD=X',
        'USD/MYR MYR=X',
        # 'USD/MZN MZN=X',
        'USD/NGN NGN=X',
        # 'USD/OMR OMR=X',
        # 'USD/PGK PGK=X',
        'USD/QAR QAR=X',
        'USD/SAR SAR=X',
        'USD/SGD SGD=X',
        # 'USD/VED VED=X', 미사용
        'USD/VND VND=X',
        # 'USD/ZAR ZAR=X',
        # 'USD/ZMK ZMK=X', 미사용
        'USD/ZMW ZMW=X'
        ]
    )
for currency in multi_currencies:
    words = currency.split()
    currencies.append({'name': words[0], 'symbol': words[1]})

@st.cache_data
def load_cur_data(currencies):
    change_cur_df = pd.DataFrame() # 변동률
    last_cur_df = pd.DataFrame() # 변동률

    for idx, currency in enumerate(currencies):

        get_currency_data = yf.Ticker(currency['symbol'])
        currency_df = get_currency_data.history(period='1d', start=start_date, end=end_date)
        # 일간변동률, 누적합계
        currency_df['dpc'] = (currency_df.Close/currency_df.Close.shift(1)-1)*100
        currency_df['cs'] = round(currency_df.dpc.cumsum(), 2)
        change2_df = pd.DataFrame(
            {
                'symbol': currency['name'],
                'Close': round(currency_df.Close, 2),
                'rate': currency_df.cs,
                }
        )
        change2_df.reset_index(drop=False, inplace=True)
        change_cur_df = pd.concat([change_cur_df, change2_df])

        last2_df = pd.DataFrame(currency_df.iloc[len(currency_df.index)-1]).T
        last3_df = pd.DataFrame(
            {
                'symbol': currency['name'],
                'Date': last2_df.index,
                'Close': last2_df.Close, 
                'rate': last2_df.cs,
                }
        )
        last_cur_df = pd.concat([last_cur_df, last3_df])

change_cur_df, last_cur_df = load_eco_data(currencies)

# st.write(f""" ### 📈 주요환율 {dt_range} 변동률 """)
base = alt.Chart(change_cur_df).encode(x='Date:T')
columns = sorted(change_cur_df.symbol.unique())
selection = alt.selection_point(
    fields=['Date'], nearest=True, on='mouseover', empty=False, clear='mouseout'
)
# lines = base.mark_line().encode(y='rate:Q', color='symbol:N')
lines_curr = base.mark_line().encode(
    x = alt.X('Date:T', title=''),
    y = alt.Y('rate:Q', title=''),
    color = alt.Color('symbol:N', title='지표', legend=alt.Legend(
        orient='bottom', 
        direction='horizontal',
        titleAnchor='end'))
)
points_curr = lines_curr.mark_point().transform_filter(selection)

rule_curr = base.transform_pivot(
    'symbol', value='Close', groupby=['Date']
    ).mark_rule().encode(
    opacity=alt.condition(selection, alt.value(0.3), alt.value(0)),
    tooltip=[alt.Tooltip(c, type='quantitative') for c in columns]
).add_params(selection)

text_data = last_cur_df
text_data.reset_index(drop=True, inplace=True)
text_sort_cur = text_data.sort_values(by=['rate'], ascending=False)
text_sort_cur.reset_index(drop=True, inplace=True)
text_data3 = pd.DataFrame(text_sort_cur.loc[0]).T
if len(text_sort_cur.index) > 1:
    text_data3.loc[1] = text_sort_cur.loc[len(text_sort_cur.index)-1]

labels_curr = alt.Chart(text_data3).mark_text(
    # point=True,
    fontWeight=600,
    fontSize=15,
    # color='white',
    align='left',
    dx=15,
    dy=-8
).encode(
    x = alt.X('Date:T', title=''),
    # y = alt.Y('rate:Q', title=rate_text),
    y = alt.Y('rate:Q', title=''),
    # y = 'rate:Q',
    text=alt.Text('rate:Q', format='.1f'),
    color = alt.Color('symbol:N', title='')
)

labels2_curr = alt.Chart(text_data3).mark_text(
    # point=True,
    fontWeight=600,
    fontSize=15,
    # color='white',
    align='left',
    dx=15,
    dy=10
).encode(
    x = alt.X('Date:T', title=''),
    # y = alt.Y('rate:Q', title=rate_text),
    y = alt.Y('rate:Q', title=''),
    text=alt.Text('symbol:N', title=''),
    color = alt.Color('symbol:N', title='')
)

# st.altair_chart(lines_curr + rule_curr + points_curr + labels_curr + labels2_curr, 
#                 use_container_width=True)

##########################################################################
### 3. 동종사 주가 변동 ###################################################
##########################################################################
status_Text = '3/3 주가 정보를 불러오는 중입니다...'
progress_stock.progress(0)
status_stock.text(f"{status_Text}")
stocks = [
    {'name': ' 대우건설', 'symbol': '047040.KS'}
    ]
multi_stocks = st.sidebar.multiselect(
    "동종사를 선택하세요",
    [
        # "인선이엔티 060150.KQ",
        # "코웨이 021240.KS",
        "삼성물산 028260.KS",
        "현대건설 000720.KS",
        "DL이앤씨 375500.KS",
        "GS건설 006360.KS",
        "삼성엔지니어링 028050.KS",
        "HDC현대산업개발 294870.KS",
        "금호건설 002990.KS"
        ],
    [ #초기 선택
        # "인선이엔티 060150.KQ",
        # "코웨이 021240.KS",
        # "삼성물산 028260.KS",
        "HDC현대산업개발 294870.KS",
        "GS건설 006360.KS",
        "현대건설 000720.KS",
        "DL이앤씨 375500.KS"
        ]
    )
for stock in multi_stocks:
    words = stock.split()
    stocks.append({'name': words[0], 'symbol': words[1]})

@st.cache_data
def load_stock_data(stocks):
    change_stocks_df = pd.DataFrame() # 주가 변동률
    info_stock_df = pd.DataFrame() # 주가 변동률

    for i, stock in enumerate(stocks):
        get_stock_data = yf.Ticker(stock['symbol'])
        stock_df = get_stock_data.history(period='1d', start=start_date, end=end_date)
        # 일간변동률, 누적합계
        stock_df['dpc'] = (stock_df.Close/stock_df.Close.shift(1)-1)*100
        stock_df['cs'] = round(stock_df.dpc.cumsum(), 2)
        change2_df = pd.DataFrame(
            {
                'symbol': stock['name'],
                # 'Close': round(stock_df.Close, 2)[0],
                'Close': round(stock_df['Close'], 2).iloc[0],
                'rate': stock_df.cs,
                }
        )

        change2_df.reset_index(drop=False, inplace=True)
        change_stocks_df = pd.concat([change_stocks_df, change2_df])

        info_stock_df[stock['name']] = [
            get_stock_data.info['marketCap'],
            convert.get_kor_amount_string_no_change(get_stock_data.info['marketCap'], 3),
            get_stock_data.info['recommendationKey'],
            get_stock_data.info['currentPrice'],
            # convert.get_kor_amount_string_no_change(get_stock_data.info['currentPrice'], 1),
            get_stock_data.info['totalCash'], # 총현금액
            convert.get_kor_amount_string_no_change(get_stock_data.info['totalCash'], 3),
            get_stock_data.info['totalDebt'], # 총부채액
            get_stock_data.info['totalRevenue'], # 총매출액
            get_stock_data.info.get('grossProfits', 0), # 매출총이익
            # convert.get_kor_amount_string_no_change(get_stock_data.info.get('grossProfits', '')),
            get_stock_data.info['operatingMargins'] * 100, # 영업이익률
            round(change_stocks_df[-1:].iloc[0]['rate'], 1), # 변동률
            '']
        rate_text = f'{dt_range}변동률'
        info_stock_df.index = [
            '시가총액', 
            '시가총액(억)', 
            '매수의견', 
            '현재가', 
            '총현금액',
            '총현금액(억)',
            '총부채액',
            '총매출액',
            '매출총이익', 
            # '매출총이익(억)', 
            '영업이익률',
        #    '순이익률',
            rate_text,
            '비고'
            ]

    return change_stocks_df, info_stock_df

change_stocks_df, info_stock_df = load_stock_data(stocks)
status_stock.empty()
progress_stock.empty()

# st.write(f""" ### 🚀 동종사 {dt_range} 변동률 """)

base = alt.Chart(change_stocks_df).encode(x='Date:T')
columns = sorted(change_stocks_df.symbol.unique())
selection = alt.selection_point(
    fields=['Date'], nearest=True, on='mouseover', empty=False, clear='mouseout'
)
# lines = base.mark_line().encode(y='rate:Q', color='symbol:N')
lines_stock = base.mark_line().encode(
    x = alt.X('Date:T', title=''),
    y = alt.Y('rate:Q', title=''),
    color = alt.Color('symbol:N', title='동종사', legend=alt.Legend(
        orient='bottom', 
        direction='horizontal',
        titleAnchor='end'))
)
points_stock = lines_stock.mark_point().transform_filter(selection)

rule_stock = base.transform_pivot(
    'symbol', value='Close', groupby=['Date']
    ).mark_rule().encode(
    opacity=alt.condition(selection, alt.value(0.3), alt.value(0)),
    tooltip=[alt.Tooltip(c, type='quantitative') for c in columns]
).add_params(selection)

text_data = change_stocks_df.groupby('symbol', as_index=False).nth(-1)
text_data.reset_index(drop=True, inplace=True)
text_sort_stock = text_data.sort_values(by=['rate'], ascending=True)
text_sort_stock.reset_index(drop=True, inplace=True)
text_data3 = pd.DataFrame(text_data.loc[0]).T
# 대우건설만 남기고 삭제
# if len(text_sort_stock.index) > 1:
#     text_data3.loc[1] = text_sort_stock.loc[0]
# if len(text_sort_stock.index) > 2:
#     text_data3.loc[2] = text_sort_stock.loc[round(len(text_data3.index)/2)]

labels_stock = alt.Chart(text_data3).mark_text(
    # point=True,
    fontWeight=600,
    fontSize=15,
    # color='white',
    align='left',
    dx=15,
    dy=-10
).encode(
    x = alt.X('Date:T', title=''),
    # y = alt.Y('rate:Q', title='변동률'),
    y = alt.Y('rate:Q', title=''),
    # y = 'rate:Q',
    text=alt.Text('rate:Q', format='.1f'),
    color = alt.Color('symbol:N', title='')
)

labels2_stock = alt.Chart(text_data3).mark_text(
    # point=True,
    fontWeight=600,
    fontSize=15,
    # color='white',
    align='left',
    dx=15,
    dy=8
).encode(
    x = alt.X('Date:T', title=''),
    # y = alt.Y('rate:Q', title=rate_text),
    y = alt.Y('rate:Q', title=''),
    # y = 'rate:Q',
    text=alt.Text('symbol:N'),
    color = alt.Color('symbol:N', title='')
)
# st.altair_chart(lines_stock + rule_stock + points_stock + labels_stock + labels2_stock, 
#                 use_container_width=True)

##########################################################################
### 4. 시가총액 바차트 그리기 ##############################################
##########################################################################
# st.write(""" ### 🎙️ 시가총액 """)
# cap_df = info_stock_df.T
cap_df = info_stock_df.iloc[[0, 1]].T #시가총액, 시가총액(억)
cap_df.reset_index(drop=False, inplace=True)
cap_df.rename(columns={'index': '종목명'}, inplace=True)
bar_chart = alt.Chart(cap_df, title='').mark_bar().encode(
                x = alt.X('시가총액:Q', title='', axis=alt.Axis(labels=False)),
                y = alt.Y('종목명:O', title=''),
                color = alt.Color('종목명:N', title='종목', legend=None)   
            )

bar_text = alt.Chart(cap_df).mark_text(
    fontWeight=600,
    fontSize=14,
    align='left',
    dx=10,
    dy=1
    ).transform_calculate(
    text_mid = '(datum.b/2)').encode(
                x=alt.X('시가총액:Q', title='', axis=alt.Axis(labels=False)),
                y=alt.Y('종목명:O'),
                # detail='TERMS:N',
                # text=alt.Text('시가총액:Q', format='.0f')
                color = alt.Color('종목명:N', title=''),
                text=alt.Text('시가총액(억):N')
            )
# st.altair_chart(bar_chart + bar_text, use_container_width=True)

col1, col2 = st.columns(2)
with col1:
    st.write(f""" ### 📈 주요지표 {dt_range} 변동률 """)
    st.altair_chart(lines_eco + rule_eco + points_eco + labels_eco + labels2_eco, 
                    use_container_width=True)
with col2:
    st.write(f""" ### 📈 주요환율 {dt_range} 변동률 """)
    st.altair_chart(lines_curr + rule_curr + points_curr + labels_curr + labels2_curr, 
                    use_container_width=True)

col3, col4 = st.columns(2)
with col3:
    st.write(f""" ### 🚀 동종사 {dt_range} 변동률 """)
    st.altair_chart(lines_stock + rule_stock + points_stock + labels_stock + labels2_stock, 
                    use_container_width=True)
with col4:
    st.write(""" ### 🎙️ 시가총액 """)
    st.altair_chart(bar_chart + bar_text, use_container_width=True)
    info_stock_dft = info_stock_df.T

##########################################################################
### 5. AI 경제지표 브리핑 ##################################################
##########################################################################

sys_msg = '''
You're an economist like legendary investors Charlie Munger and Warren Buffett
'''
chatGPT_msg = [{'role': 'system', 'content': sys_msg}]

userq = '''
#task
I'll give you an article. please remember it for following requests.
summarize the above article with one sentence.
Please answer in Korean based on the following [context] [Persona] [Format] [Tone] [article]

#context
- Tell me the impact on the economy compared to past cases
- Tell me the correlation between economic indicators as well

#Persona
I want you to act as an investment guru  Charlie Munger and Warren Buffett.

#Format
Explain in simple terms

#Tone
Give me a clear and polite answer

#article
'''

userq += '거시경제 지표 \n'
userq += f'지표 현재가 {dt_range}변동률''\n'
text_sort_eco.columns = ['지표', '일자', '현재가', f'{dt_range}변동률']
text_sort_eco.index = text_sort_eco['지표']
text_sort_eco.drop(['지표'], axis=1, inplace=True)

for index, row in text_sort_eco.iterrows():
    Close = str(round(row['현재가']))
    rate = str(round(row[f'{dt_range}변동률'], 2))
    userq = userq + ' ' + index + ' ' + Close + " " + rate + ' ' + '\n'

user_message = {'role': 'user', 'content': f"{userq}"}

##########################################################################
### 3-2 AI 동종사 비교 ######################################################
##########################################################################
chat_df = info_stock_df.T # 주가정보는 대화에서 제외함
chat_df.drop(['시가총액'], axis=1, inplace=True)

# # 이어서 작성
# userq += '\n'
# userq += '건설회사 주가정보 \n'
# userq += f'회사명 현재가 매수의견 시가총액 {dt_range}변동률\n'
# # DataFrame의 각 행을 ChatCompletion messages에 추가
# rate_text = f'{dt_range}변동률'
# for index, row in chat_df.iterrows():
#     userq += index + ' ' + str(round(row['현재가'])) + ' ' + row['매수의견'] + ' ' 
#     userq += row['시가총액(억)'] + ' ' + str(row[rate_text]) + ' ' + '\n' 

user_message = {'role': 'user', 'content': f"{userq}"}
chatGPT_msg.extend([user_message])

streamText = ''
# get_respense = openai.chat.completions.create(
#     model=st.session_state["openai_model"],
#     messages = chatGPT_msg,
#     # max_tokens = chatGPT_max_tokens,
#     # temperature=0,
#     stream=True,
# )

# for response in get_respense:
#     for chunk in response.choices:
#         if chunk.finish_reason == 'stop':
#             break
#         streamText += chunk.delta.content
#     if streamText is not None:
#         ai_stock_text.success(f""" {streamText} """)       

user_message = {'role': 'assistant', 'content': f"{streamText}"}
chatGPT_msg.extend([user_message])

with st.expander("프롬프트 보기"):
    st.write(text_sort_eco) # 경제지표 변동률(수익률 높은 순)
    st.write(chat_df)       # 주가정보 info_stock_df
    st.write(last_cur_df)   # 환율정보
    st.write(chatGPT_msg)   # ChatGPT API용

st.write(change_eco_df)   # 환율정보
st.write(last_df)   # 환율정보

st.write(change_cur_df)   # 환율정보
st.write(last_cur_df)   # 환율정보

# change_cur_df.to_sql(table_name, con, if_exists='replace', index=False)

# df = pd.read_sql(f'SELECT * FROM {table_name}', con, index_col=None)
# st.write('==================')   # 환율정보
# st.write(df)   # 환율정보