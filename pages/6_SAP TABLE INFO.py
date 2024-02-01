import streamlit as st
import streamlit.components.v1 as components
import openai
import json
import pyrfc
import pandas as pd
from components import convert
from pygwalker.api.streamlit import StreamlitRenderer, init_streamlit_comm, get_streamlit_html

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
fields_select = st.sidebar.multiselect("필드를 선택하세요",
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
# st.code(fields)

# st.subheader('Step 3. 필드명을 직접 입력하실수도 있어요')
fields_input = st.text_input('필드명을 직접 입력 하실 수 있어요', fields)
if fields_input :
    # 문자열 하나에 들어 있는 텍스트를 리스트로 만들기
    text = fields_input.strip("[]")  # 대괄호([])를 제거
    fields = [item.strip(" '") for item in text.split(",")]

st.code(fields)

st.subheader('Step 3. 데이터가 조회되지 않을 경우 청크 수를 낮춰보세요')
chunk_size = st.text_input('청크 사이즈', '100')
chunks = []
for i in range(0, len(fields), int(chunk_size)):
    chunks.append(fields[i:i+int(chunk_size)])

results_df = pd.DataFrame()
columns = []

for chunk in chunks:
    with pyrfc.Connection(**connect) as conn:
        result = conn.call("RFC_READ_TABLE", QUERY_TABLE = table_input.upper(), OPTIONS = [], FIELDS = chunk, DELIMITER = "|", ROWCOUNT=3)
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

st.subheader('Step 4. 조회 조건을 규칙에 맟추어서 입력해주세요')
results_df = pd.DataFrame()
columns = []

options = []
options_input = st.text_input("입력규칙은 🎯 필드명 = '입력 값' 입니다. 💁🏻‍♀️ 예) GJAHR = '2023', BUKRS = '1000', BLART= 'HE', BLDAT='20230704'", "BUKRS = '1000', GJAHR = '2024'")
if options_input :
    options_input = options_input.replace('=', ' = ')
    options_input = options_input.replace('  ', ' ')
    # options = [{'TEXT' : "GJAHR = '2023'"}]
    # options = [{'TEXT' : "GJAHR = '2023'"}, {'TEXT' : "AND BUKRS = '1000'"}]
    inputs = options_input.strip().split(",")
    # st.write(inputs)
    for idx, input in enumerate(inputs):
        if idx == 0:
            options.append({'TEXT' : f"{input}"})
        else:
            options.append({'TEXT' : f"AND {input}"})
else:
    st.stop()

rowcount = 10
rowcount_input = st.text_input("최대 조회 라인수를 지정해 주세요", rowcount)
if rowcount_input :
    rowcount = int(rowcount_input)

for chunk in chunks:
    with pyrfc.Connection(**connect) as conn:
        result = conn.call("RFC_READ_TABLE", QUERY_TABLE = table_input.upper(), OPTIONS = options, FIELDS = chunk, DELIMITER = "|", ROWCOUNT=rowcount)
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
st.write(results_df.shape)

init_streamlit_comm()
st.subheader('Step5. 탐색적 데이터를 볼 수 있어요 by Pygwalker')

# When using `use_kernel_calc=True`, you should cache your pygwalker html, if you don't want your memory to explode
@st.cache_resource
def get_pyg_html(df: pd.DataFrame) -> str:
    # When you need to publish your application, you need set `debug=False`,prevent other users to write your config file.
    # If you want to use feature of saving chart config, set `debug=True`
    html = get_streamlit_html(df, spec="./db/gw0.json", use_kernel_calc=True, debug=False, dark='light')
    return html
components.html(get_pyg_html(results_df), width=1300, height=1000, scrolling=False)

# renderer = StreamlitRenderer(results_df, env='Streamlit',
#                              spec="./db/gw_config.json",
#                              dark='light',
#                              debug=False,
#                              show_cloud_tool=True,
#                              return_html=True)
# renderer.render_explore()

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
txts += results_df[:10].to_string()
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
tokens = convert.calculate_tokens(txts, st.session_state["openai_model"])
st.caption(tokens)

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