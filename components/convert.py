##########################################################################
### 공통함수 ###############################################################
##########################################################################
import streamlit as st
import openai
import tiktoken
import requests
import base64
import json

def check_auth():

#----------------------Hide Streamlit footer----------------------------
    hide_st_style = """
        <style>
        MainMenu {visibility: show;}
        header {visibility: visible;}
        footer {visibility: hidden;}
        </style>
    """
    st.markdown(hide_st_style, unsafe_allow_html=True)
#--------------------------------------------------------------------
    
    st.markdown(""" 
        <style>
               .block-container {
                    padding-top: 1rem;
                    padding-bottom: 5rem;
                    # padding-left: 5rem;
                    # padding-right: 5rem;
                }
        </style>
        """, unsafe_allow_html=True)
    
    stChatFloatingInputContainer()    

    if "user_info" not in st.session_state:
        st.session_state.user_info = []

    if len(st.session_state.user_info) != 0:
        return True

    try:
        user = open("./db/local_user.json")
        user_info = json.load(user)
        st.session_state.user_info.append(user_info) # 사용자 정보
        st.session_state["openai_model"] = 'gpt-4-1106-preview'
        # st.session_state["openai_model"] = 'gpt-3.5-turbo-1106'
        openai.api_key = st.secrets["api_dw"]
        return True

    except Exception as e:

        query_param = st.query_params.to_dict()
        st.query_params.clear()
        if len(query_param) == 0:
            st.title("본인인증이 필요합니다. 🤔") 
            st.subheader("인증 후 재방문 🏃 해주세요 ")
            st.write("")
            st.write("")
            redirect_button(st.secrets["dwenc_sso"],"인증하기")
            return False
        else:
            api_url = st.secrets["dwenc_auth"] # 운영
            headers = {
                "content-type": "application/json+sua",
                "dwenc-token": st.secrets["dwenc_token"]  # 토큰을 prod 설정
            }

            # 인증 정보를 Base64로 인코딩
            auth_str = query_param[st.secrets["dwenc_user"]] + ':' + query_param[st.secrets["dwenc_pass"]]
            auth_bytes = auth_str.encode('utf-8')
            encoded_auth_str = base64.b64encode(auth_bytes).decode('utf-8')
            # POST 바디 생성
            data = {
                "_param": {
                    "value": encoded_auth_str
                }
            }
            try:
                # POST 요청
                response = requests.post(api_url, headers=headers, json=data)
                # 성공적인 응답 처리
                if response.status_code == 200:
                    st.session_state.user_info.append(response.json()) # 사용자 정보
                    openai.api_key = st.secrets["api_dw"]
                    st.session_state["openai_model"] = 'gpt-4-1106-preview'
                    return True
                else:
                    st.write(response.status_code, response.json()['message'])
                    return False

            except requests.exceptions.RequestException as e:
                # 요청 중 오류 발생시 예외 처리
                st.write('인증에 실패하였습니다.', e)
                return False
        
def check_password():
    #----------------------Hide Streamlit footer----------------------------
    hide_st_style = """
        <style>
        #MainMenu {visibility: show;}
        header {visibility: show;}
        footer {visibility: hidden;}
        </style>
    """
    st.markdown(hide_st_style, unsafe_allow_html=True)
    #--------------------------------------------------------------------

    """Returns `True` if the user had the correct password."""
    def password_entered():
        if "password_correct" in st.session_state:
           if st.session_state["password_correct"]:
               return True
        """Checks whether a password entered by the user is correct."""
        if st.session_state["adminpass"] == st.secrets["adminpass"]:
            st.session_state["password_correct"] = True
            del st.session_state["adminpass"]  # don't store password
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        # First run, show input for password.
        st.text_input("Password", type="password", on_change=password_entered, key="adminpass")
        return False
    elif not st.session_state["password_correct"]:
        # Password not correct, show input + error.
        st.text_input("Password", type="password", on_change=password_entered, key="adminpass")
        st.error("😕 Password incorrect")
        return False
    else:
        openai.api_key = st.secrets["api_dw"]
        st.session_state["openai_model"] = 'gpt-4-1106-preview'
        return True

def redirect_button(url: str, text: str= None, color="#D9675F"): #FD504D
    st.markdown(
    f"""
    <a href="{url}" target="_self">
        <div style="
            display: inline-block;
            padding: 0.5em 1em;
            color: #FFFFFF;
            background-color: {color};
            border-radius: 3px;
            text-decoration: none;">
            {text}
        </div>
    </a>
    """,
    unsafe_allow_html=True
    )

def get_kor_amount_string_no_change(num_amount, ndigits_keep):
    """잔돈은 자르고 숫자를 자릿수 한글단위와 함께 리턴한다 """
    result = get_kor_amount_string(num_amount, 
                                 -(len(str(num_amount)) - ndigits_keep))
    return result

def get_kor_amount_string(num_amount, ndigits_round=0, str_suffix='원'):
    if num_amount == 0 :
        return '0원'
    """숫자를 자릿수 한글단위와 함께 리턴한다 """
    assert isinstance(num_amount, int) and isinstance(ndigits_round, int)
    assert num_amount >= 1, '최소 1원 이상 입력되어야 합니다'
    ## 일, 십, 백, 천, 만, 십, 백, 천, 억, ... 단위 리스트를 만든다.
    maj_units = ['만', '억', '조', '경', '해', '자', '양', '구', '간', '정', '재', '극'] # 10000 단위
    units     = [' '] # 시작은 일의자리로 공백으로하고 이후 십, 백, 천, 만...
    for mm in maj_units:
        units.extend(['십', '백', '천']) # 중간 십,백,천 단위
        units.append(mm)
    
    list_amount = list(str(round(num_amount, ndigits_round))) # 라운딩한 숫자를 리스트로 바꾼다
    list_amount.reverse() # 일, 십 순서로 읽기 위해 순서를 뒤집는다
    
    str_result = '' # 결과
    num_len_list_amount = len(list_amount)
    
    for i in range(num_len_list_amount):
        str_num = list_amount[i]
        # 만, 억, 조 단위에 천, 백, 십, 일이 모두 0000 일때는 생략
        if num_len_list_amount >= 9 and i >= 4 and i % 4 == 0 and ''.join(list_amount[i:i+4]) == '0000':
            continue
        if str_num == '0': # 0일 때
            if i % 4 == 0: # 4번째자리일 때(만, 억, 조...)
                str_result = units[i] + str_result # 단위만 붙인다
        elif str_num == '1': # 1일 때
            if i % 4 == 0: # 4번째자리일 때(만, 억, 조...)
                str_result = str_num + units[i] + str_result # 숫자와 단위를 붙인다
            else: # 나머지자리일 때
                str_result = units[i] + str_result # 단위만 붙인다
        else: # 2~9일 때
            str_result = str_num + units[i] + str_result # 숫자와 단위를 붙인다
    str_result = str_result.strip() # 문자열 앞뒤 공백을 제거한다 
    if len(str_result) == 0:
        return None
    if not str_result[0].isnumeric(): # 앞이 숫자가 아닌 문자인 경우
        str_result = '1' + str_result # 1을 붙인다
    return str_result + str_suffix # 접미사를 붙인다

def calculate_rsi(data, window_length=14):
    data = data.copy()
    delta = data['Close'].diff()
    delta = delta[1:] 

    up, down = delta.copy(), delta.copy()
    up[up < 0] = 0
    down[down > 0] = 0

    avg_gain = up.rolling(window_length).mean()
    avg_loss = abs(down.rolling(window_length).mean())

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    data['RSI'] = rsi

    return data

# def get_df_from_password_excel(excelpath, password):
#     df = pd.DataFrame()
#     temp = io.BytesIO()
#     with open(excelpath, 'rb') as f:
#         excel = msoffcrypto.OfficeFile(f)
#         excel.load_key(password)
#         excel.decrypt(temp)
#         df = pd.read_excel(temp)
#         del temp
#     return df

def num_tokens_from_string(string: str, encoding_name: str) -> int:
    """Returns the number of tokens in a text string."""
    encoding = tiktoken.get_encoding(encoding_name)
    num_tokens = len(encoding.encode(string))
    return num_tokens

# def calculate_tokens(string: str, model: str) -> int:
def calculate_tokens(messages, model: str) -> int:
        
    tokenizer = tiktoken.get_encoding("cl100k_base")
    tokenizer = tiktoken.encoding_for_model(model)

    token_size = 0
    # if model == 'text-embedding-ada-002':
    if type(messages) == str:
        pricing = 0.0001

        encoding_result = tokenizer.encode(messages)
        token_size = token_size + len(encoding_result)

        # $0.0001 / 1K tokens        
        result = f"{token_size} 토큰을 사용하였습니다. 예상비용은 {round(token_size / 1000 * pricing, 4)}$ 입니다"

    elif type(messages) == list:
        pricing = 0.03
        # gpt-3.5-turbo-1106	$0.0010 / 1K tokens	$0.0020 / 1K tokens
        # Model	Input	Output
        # gpt-4-1106-preview	$0.01 / 1K tokens	$0.03 / 1K tokens
        message_cnt = 0
        for message in messages:
            if message[2] == 'system':
                continue
            encoding_result = tokenizer.encode(message[3])
            token_size = token_size + len(encoding_result)
            message_cnt = message_cnt + 1

        if token_size != 0:
            result = f"{message_cnt} 개의 대화에서 {token_size} 토큰을 사용하였습니다. 예상비용은 {round(token_size * 0.00001, 4)}$ 입니다"

    else:
    # elif model == 'gpt-4-1106-preview' :
        # st.write(messages)
        pricing = 0.03
        # gpt-3.5-turbo-1106	$0.0010 / 1K tokens	$0.0020 / 1K tokens
        # Model	Input	Output
        # gpt-4-1106-preview	$0.01 / 1K tokens	$0.03 / 1K tokens
    
        message_cnt = 0
        for message in messages:
            if message['role'] == 'system':
                continue
            encoding_result = tokenizer.encode(message['content'])
            token_size = token_size + len(encoding_result)
            message_cnt = message_cnt + 1

        if token_size != 0:
            result = f"{message_cnt} 개의 대화에서 {token_size} 토큰을 사용하였습니다. 예상비용은 {round(token_size * 0.00001, 4)}$ 입니다"

    return result

def stChatFloatingInputContainer():
    st.markdown(
        """
        <style>
            .stChatFloatingInputContainer {
                bottom: -40px;
                background-color: rgba(0, 0, 0, 0)
            }
        </style>
        """,
        unsafe_allow_html=True,
    )