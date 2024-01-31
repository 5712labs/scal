import streamlit as st
import openai
import json
import pyrfc
import pandas as pd
from components import convert
from pygwalker.api.streamlit import StreamlitRenderer, init_streamlit_comm

st.set_page_config(page_title="AI DW", page_icon="🐍", layout='wide')

if convert.check_auth() == False:
    st.stop()

clear_button = st.sidebar.button("Clear Conversation", type="primary", key="clear_newss")
if clear_button:
    st.session_state['sap1messages'] = [
        {"role": "system", "content": "You are a helpful assistant."}
    ]

st.subheader('Step 1. 테이블명을 입력하세요 😚')
table_input = st.text_input('대소문자는 관계가 없어요. STANDARD나 CBO도 가능해요', placeholder='BKPF')

if table_input == '':
    st.stop()

f = open("./db/sap_connect_dcd.json")
connect = json.load(f)

table_DDTEXT = ''

with pyrfc.Connection(**connect) as conn:
    fields = ['DDTEXT']
    result = conn.call("RFC_READ_TABLE", QUERY_TABLE = "DD02T", OPTIONS = [{'TEXT' : f"TABNAME = '{table_input.upper()}'"}, {'TEXT' : "AND DDLANGUAGE = '3'"}], FIELDS = fields, DELIMITER = "," , ROWCOUNT=1)
    table_DDTEXT = result['DATA'][0]['WA']

## 테이블 필드목록 가져오기
import_param = {
    'TABNAME': table_input.upper()
}
table_param = {
    # 'ITAB':''
}
with pyrfc.Connection(**connect) as conn:
    result = conn.call('DDIF_FIELDINFO_GET', **import_param, **table_param)
result_df = pd.DataFrame(result["DFIES_TAB"])
fields_df =  result_df[['FIELDNAME', 'FIELDTEXT', 'LENG', 'DATATYPE', 'INTTYPE']]
st.info(f'{table_input.upper()} ({table_DDTEXT}) 테이블에 {str(fields_df.shape[0])}개의 필드가 존재합니다.')
st.write(fields_df.T)

st.subheader('Step 2. 필드를 선택하세요')
fields = []
fields_select = st.multiselect("필드를 선택하세요",
                                fields_df['FIELDNAME'] + ' ' + fields_df['FIELDTEXT'], 
                                fields_df['FIELDNAME'] + ' ' + fields_df['FIELDTEXT'])

import_param = {
    'I_QUERY_TABLE':table_input.upper()
}
table_param = {
    # 'ITAB':''
}

for field in fields_select:
    words = field.split()
    fields.append(words[0])
    # fields.append({'name': words[0], 'text': words[1]})
st.code(fields)

st.subheader('Step 3. 필드명을 직접 입력하실수도 있어요')
fields_input = st.text_input('필드명', fields)
if fields_input :
    # 문자열 하나에 들어 있는 텍스트를 리스트로 만들기
    text = fields_input.strip("[]")  # 대괄호([])를 제거
    fields = [item.strip(" '") for item in text.split(",")]

st.code(fields)
# st.write(fields)
## 테이블 필드목록 가져오기
# with pyrfc.Connection(**connect) as conn:
#     result = conn.call('ZN_RFC_READ_TABLE', **import_param, **table_param)
# fields_df = pd.DataFrame(result["ITAB"])
# st.write(fields_df.T)

# fields = []
# for line in result["ITAB"]:
#     fields.append(line['FIELDNAME'])
# fields_select = st.multiselect("필드를 선택하세요", fields, fields)

st.subheader('Step 3. 데이터가 조회되지 않을 경우 청크 수를 낮춰보세요')
chunk_size = st.text_input('청크 사이즈', '100')
chunks = []
# for i in range(0, len(fields_select), int(chunk_size)):
#     st
#     chunks.append(fields_select[i:i+int(chunk_size)])
for i in range(0, len(fields), int(chunk_size)):
    chunks.append(fields[i:i+int(chunk_size)])

results_df = pd.DataFrame()

columns = []
for chunk in chunks:
    with pyrfc.Connection(**connect) as conn:
        result = conn.call("RFC_READ_TABLE", QUERY_TABLE = table_input.upper(), OPTIONS = [], FIELDS = chunk, DELIMITER = "|", ROWCOUNT=3)

# ## 테이블 READ : 테이블명-ZAACFRM
# with pyrfc.Connection(**connect) as conn:
# # st.write(result['FIELDS'][0]['FIELDTEXT'])
#     # fields = ['BUKRS', 'ZBYBP', 'ZISSID', 'ZARAP', 'SUPNO', 'ZSPCN', 'BUYNO', 'ZBYCN', 'HWBAS', 'HWSTE']
#     # fields = ['MANDT', 'BUKRS', 'ZISSID', 'ZARAP', 'BUZEI', 'BUPLA', 'ZASPC', 'ZMKDT', 'ZSGDT', 'ZTRDT', 'SUPNO', 'ZSPBP', 'ZSPCN', 'ZSPNM', 'ZSPAR', 'ZSPIT', 'ZSPBT', 'ZSPRP', 'ZSPRN', 'ZSPRE', 'BUYNO', 'ZBYBP', 'ZBYCN', 'ZBYNM', 'ZBYAR', 'ZBYIT', 'ZBYBT', 'ZBYRP', 'ZBYRN', 'ZBYRE', 'ZBKNO', 'ZBKBP', 'ZBKCN', 'ZBKNM', 'ZBKAR', 'ZBKIT', 'ZBKBT', 'ZBKRE', 'HWAER', 'HWBAS', 'HWSTE', 'ZTTAT', 'ZREMK', 'ZISTP', 'ZTPDS', 'ZTPCD', 'ZAMEND', 'ZPMMC', 'DMBTR', 'DMBTR2', 'DMBTR3', 'DMBTR4', 'ZRPTP', 'ZBYRE2', 'ZCRDT', 'ZCRTM', 'ZLCUS', 'ZLCDT', 'ZLCTM', 'ZFLSQ', 'ZDELE', 'ZORG_ID']
#     # fields = ['MANDT', 'BUKRS', 'ZISSID', 'ZARAP', 'BUZEI', 'BUPLA', 'ZASPC', 'ZMKDT']
#     result = conn.call("RFC_READ_TABLE", QUERY_TABLE = "ZDTI_NTS_HEADER", OPTIONS = [], FIELDS = fields_select, DELIMITER = "|", ROWCOUNT=1)
#     # result = conn.call("RFC_READ_TABLE", QUERY_TABLE = "ZDTI_NTS_HEADER", OPTIONS = [{'TEXT' : "BUKRS = '1000'"}, {'TEXT' : "AND ZCRDT = '20140529'"}], FIELDS = fields_select, DELIMITER = "|", ROWCOUNT=3) # ROWCOUNT = 10 ,ROWSKIPS=2""

    data = []
    for line in result["DATA"]:
        raw_data = line["WA"].strip().split("|")
        data.append(raw_data)
    for line in result["FIELDS"]:
        columns.append(line['FIELDTEXT'] + ' ' + line['FIELDNAME'])
    result_df = pd.DataFrame(data)
    results_df = pd.concat([results_df, result_df], axis=1, ignore_index=True)

results_df.columns = columns
st.write(results_df)

init_streamlit_comm()
st.subheader('Step5. 탐색적 데이터를 볼 수 있어요 by Pygwalker')

renderer = StreamlitRenderer(results_df, env='Streamlit',
                             spec="./gw_config.json",
                             dark='light',
                             debug=False,
                             show_cloud_tool=True,
                             return_html=True)
renderer.render_explore()

st.subheader('Step 4. ChatGPT에게 물어보세요')

if "sap1messages" not in st.session_state:
    st.session_state.sap1messages = []

for message in st.session_state.sap1messages:
    if message["role"] != "system": #시스템은 가리기
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

txts = '''
#명령문

당신은 데이터 분석 전문가 입니다. 아래의 제약 조건을 참고하여 입력문을 출력형식에 맞게 출력해 주세요.

#제약조건

요점을 명확히 한다
문장은 간결하게 알기 쉽게 쓴다

#입력문

'''
txts += results_df.to_string()
txts += '''
\n\n
#출력형식
분석아이디어 1: 내용
파이썬 코드 1: 코드

분석아이디어 2: 내용
파이썬 코드 2: 코드

분석아이디어 3: 내용
파이썬 코드 3: 코드

    '''

st.code(txts)
prompt = st.chat_input("Say something")

if prompt:
    st.session_state.sap1messages.append({"role": "user", "content": prompt})
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
                for m in st.session_state.sap1messages
            ],
            stream=True,
        ):
            for chunk in response.choices:
                if chunk.finish_reason == 'stop':
                    break
                full_response += chunk.delta.content
            message_placeholder.markdown(full_response + "▌")
        message_placeholder.markdown(full_response)
    st.session_state.sap1messages.append({"role": "assistant", "content": full_response})