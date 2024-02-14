import streamlit as st
from components import convert, apigpt
import openai
import json
import altair as alt
import pandas as pd

title = 'ChatGPT With Function'
st.set_page_config(page_title=title, page_icon="🐍", layout='centered', initial_sidebar_state='auto')
st.title(title)

if convert.check_auth() == False:
    st.stop()

info_help = '무엇을 할 수 있나요?\n\n'
info_help += '* 회의실 예약 현황 알려줘\n\n'
info_help += '* 최근 3개월 경제지표 브리핑 해줘\n\n'
info_help += '* 서울 날씨 어때\n\n'
info_help += '* (준비 중)최근 3개월 동종사 주가 비교 해줘\n\n'
info_help += '* (준비 중)최근 3개월 주요 환율 비교 해줘\n\n'

st.info(info_help, icon="😍")

# agree = st.sidebar.checkbox('사내문서 연동')
agree = False

# 대화 초기화 
clear_button = st.sidebar.button("새 대화 시작", type="primary", key="clear")
if clear_button:
    del st.session_state.fmessages

if "fmessages" not in st.session_state:
    st.session_state.fmessages = []

# 대화 이력 보기
for message in st.session_state.fmessages:
    if message["hide"] == False:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

# 사용자 질문 입력
if prompt := st.chat_input("What is up?"):

    st.session_state.fmessages.append({"role": "user", "content": prompt, "hide": False})
    with st.chat_message("user"):
        st.markdown(prompt)

    messages = []
    messages.append({"role": "user", "content": prompt})

    # if agree: # 사내문서 연동
    # # 벡터DB에서 유사 문서 가져오기
    #     similarity_data = []
    #     similar_datas = pd.DataFrame()
    #     similarity_data, similar_datas = apigpt.get_vector_chroma(prompt)

    #     with st.chat_message("assistant"):
    #         # st.write(similarity_data) # 유사문서 내용
    #         if len(similarity_data) != 0 :
    #             st.write('사내 유사문서가 존재합니다.') # 유사문서 리스트
    #             st.write(similar_datas) # 유사문서 리스트
    #             tool_choice='none'
    #             messages.append({"role": "user", "content": similarity_data})
    #         else:        
    #             st.write('유사 답변을 찾을수 없습니다.')
    #             tool_choice='auto'
    # else: 
    #     tool_choice='auto'

    tool_choice='auto'
    tools = apigpt.get_tools_list()

    with st.chat_message("assistant"):
        message_response = st.container()
        message_placeholder = st.empty()
        message_chart = st.empty()
        message_placeholder = st.empty()
        full_response = "" # 함수 호출이 없을 경우
        func_response = "" # 함수 호출이 있는 경우
        full_funcname = "" # 펑션 이름
        full_funcargu = "" # 펑션 파라메터

        response = openai.chat.completions.create(
            # model=st.session_state["openai_model"],
            model="gpt-3.5-turbo-0125",
            messages=messages,
            tools=tools,
            tool_choice=tool_choice
        )

        response_message = response.choices[0].message
        tool_calls = response_message.tool_calls
        content = response_message.content

        if content:
            full_response = content
            message_placeholder.markdown(content)

        if tool_calls:
            # Step 3: call the function
            # Note: the JSON response may not always be valid; be sure to handle errors
            available_functions = {
                "get_current_weather": apigpt.get_current_weather,
                "get_meeting_rooms": apigpt.get_meeting_rooms,
                "get_economic_indicators": apigpt.get_economic_indicators,
            }
            messages.append(response_message)  # extend conversation with assistant's reply

            for tool_call in tool_calls:
                function_name = tool_call.function.name
                function_to_call = available_functions[function_name]
                function_args = json.loads(tool_call.function.arguments)
                st.write(tool_call.function)
                if function_name == 'get_current_weather':
                    function_response = function_to_call(
                        location=function_args.get("location"),
                        unit=function_args.get("unit"),
                    )
                elif function_name == 'get_meeting_rooms':
                    with st.spinner(full_funcname):
                        user_info = st.session_state.user_info[0]
                        function_response = function_to_call(
                            user_info = user_info,
                            floor=function_args.get("floor")
                        )
                    message_response.write(function_response)
                elif function_name == 'get_economic_indicators':
                    dt_range = 90
                    if function_args.get("num_days"):
                        dt_range = function_args.get("num_days")
                    with st.spinner(full_funcname):
                        change_eco_df, last_df = function_to_call(
                            num_days=int(dt_range),
                        )
                    full_response = f'###### 🤖 AI 경제지표 요약 브리핑입니다. (최근 {dt_range}일)\n\n'
                    message_placeholder.markdown(full_response)

                    base = alt.Chart(change_eco_df).encode(x='Date:T')
                    columns = sorted(change_eco_df.symbol.unique())
                    selection = alt.selection_point(
                        fields=['Date'], nearest=True, on='mouseover', empty=False, clear='mouseout'
                    )
                    lines = base.mark_line().encode(
                        x = alt.X('Date:T', title=''),
                        y = alt.Y('rate:Q', title=''),
                        color = alt.Color('symbol:N', title='지표', legend=alt.Legend(
                            orient='bottom', 
                            direction='horizontal',
                            titleAnchor='end'))
                    )
                    points = lines.mark_point().transform_filter(selection)

                    rule = base.transform_pivot(
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

                    labels = alt.Chart(text_data3).mark_text(
                        fontWeight=600,
                        fontSize=15,
                        align='left',
                        dx=15,
                        dy=-8
                    ).encode(
                        x = alt.X('Date:T', title=''),
                        y = alt.Y('rate:Q', title=''),
                        text=alt.Text('rate:Q', format='.1f'),
                        color = alt.Color('symbol:N', title='')
                    )

                    labels2 = alt.Chart(text_data3).mark_text(
                        fontWeight=600,
                        fontSize=15,
                        align='left',
                        dx=15,
                        dy=10
                    ).encode(
                        x = alt.X('Date:T', title=''),
                        y = alt.Y('rate:Q', title=''),
                        text=alt.Text('symbol:N', title=''),
                        color = alt.Color('symbol:N', title='')
                    )
                    message_chart.altair_chart(lines + rule + points + labels + labels2, use_container_width=True)
                    # st.altair_chart(lines + rule + points + labels + labels2, use_container_width=True)
                    
                    userq = '거시경제 지표 \n'
                    userq += f'지표 현재가 {dt_range}일변동률''\n'
                    text_sort_eco.columns = ['지표', '일자', '현재가', f'{dt_range}일변동률']
                    text_sort_eco.index = text_sort_eco['지표']
                    text_sort_eco.drop(['지표'], axis=1, inplace=True)
                    for index, row in text_sort_eco.iterrows():
                        Close = str(round(row['현재가']))
                        rate = str(round(row[f'{dt_range}일변동률'], 2))
                        userq = userq + ' ' + index + ' ' + Close + " " + rate + ' ' + '\n'

                    userq += '\n 거시경제 지표 요약하고 변동성이 큰 지표들을 과거 사례와 비교하여 경제에 미치는 영향 요약해줘'
                    function_response = userq
                messages.append(
                    {
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": function_name,
                        "content": function_response,
                    }
                )
                
            for second_response in openai.chat.completions.create(
                # model=st.session_state["openai_model"],
                model="gpt-3.5-turbo-0125",
                messages=messages,
                stream=True,
            ):
                for chunk in second_response.choices:
                    if chunk.finish_reason == 'stop':
                        break
                    if chunk.delta.content != None:
                        full_response += chunk.delta.content
                message_placeholder.markdown(full_response + "▌")
            message_placeholder.markdown(full_response)

        st.session_state.fmessages.append({"role": "assistant", "content": full_response, "hide": False})

        with st.expander('프롬프트 보기'):
                st.write(messages)
