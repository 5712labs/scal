##########################################################################
### 공통함수 ###############################################################
##########################################################################
# streamlit_app.py
import streamlit as st
import pandas as pd
import requests
import json
import yfinance as yf
from datetime import datetime
from dateutil.relativedelta import relativedelta

def get_tools_list(): 
    tools = [
    {
        "type": "function",
        "function": {
            "name": "get_current_weather",
            "description": "Get the current weather in a given location",
            "parameters": {
                "type": "object",
                "properties": {
                "location": {
                    "type": "string",
                    "description": "The city and state, e.g. San Francisco, CA",
                },
                "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]},
                },
                "required": ["location"],
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_meeting_rooms",
            "description": "회의실 예약 현황",
            "parameters": {
                "type": "object",
                "properties": {
                    "floor": {
                        "type": "integer",
                        "description": "19층, 19F, 19Floors",
                    }
                    },
                "required": [],
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_economic_indicators",
            "description": "경제지표 브리핑",
            "parameters": {
                "type": "object",
                "properties": {
                    "num_days": {
                        "type": "integer",
                        "description": "The number of days",
                    }
                },
                "required": [],
            }
        }
    }
    ]
    return tools

def get_current_weather(location, unit="fahrenheit"):
    """Get the current weather in a given location"""
    weather_info = {
        "location": location,
        "temperature": "10",
        "unit": unit,
        "forecast": ["sunny", "windy"],
    }
    return json.dumps(weather_info)

def get_meeting_rooms(user_info, floor):
    """Get meeting room in a given floor"""
    headers = {
        'Accept': '*/*',
        'Content-Type': 'application/json+sua'
    }
    user_id = user_info['userId']
    meet_ymd = datetime.now().strftime("%Y%m%d")
    data = {
        "param": {
            "userId": user_id,
            "meetYmd": meet_ymd,
            "signStsCd": "02"
        }
    }
    
    cnfrrNm = str(floor)
    url = st.secrets["dwenc_meet"]
    response = requests.post(url, headers=headers, data = json.dumps(data))
    try:
        response_data = response.json()
        meet_header = '''
    |회의실명| 시간 | 팀명 | 예약자 |
    |:-------------:|:-------------:|:-------------:|:-------------:|
    '''
        meet_detail = ''    
        for res in response_data['result'][0]['cnfrrList']:
            # st.write(res)
            if len(res['meetAppnList']) == 0:
                continue
            # if floor != '':
            for meet in res['meetAppnList']:
                if cnfrrNm != 'None' and cnfrrNm != meet['cnfrrNm'][1:3]:
                    continue
                meet_detail = meet_detail + f'''{meet['cnfrrNm']} | {meet['meetStime'][:2]}:{meet['meetStime'][2:]} ~ {meet['meetEtime'][:2]}:{meet['meetEtime'][2:]}  | {meet['appantOrgNm']}  | {meet['appantNm']} {meet['appantPositCd']}|
    '''
        room_info = f'''{meet_header} {meet_detail}'''
        if len(meet_detail) == 0:
            room_info = '회의실 예약 내역이 없습니다.'
        # st.markdown(f'''{meet_header} {meet_detail}''')
    except json.JSONDecodeError:
        room_info = response.text
        # st.write(response.text)

    return room_info


def get_economic_indicators(num_days):

    products = [
        {'name': '달러인덱스', 'symbol': 'DX-Y.NYB'},
        {'name': '크루드오일', 'symbol': 'CL=F'},
        {'name': '금', 'symbol': 'GC=F'},
        {'name': 'S&P500', 'symbol': '^GSPC'},
        {'name': '천연가스', 'symbol': 'LNG'},
        {'name': '10년물', 'symbol': '^TNX'},
        {'name': '원자재', 'symbol': 'DBC'}
        ]
    
    change_eco_df = pd.DataFrame() # 변동률
    last_df = pd.DataFrame() # 변동률
    for idx, product in enumerate(products):

        get_product_data = yf.Ticker(product['symbol'])
        start_date = datetime.today() - relativedelta(days=num_days)
        product_df = get_product_data.history(period='1d', start=start_date, end=datetime.today())
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
        # change2_df.reset_index(drop=False, inplace=True)
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
