import streamlit as st
# import openai
from openai import OpenAI # openai==1.2.0
from components import convert
from components.db_manager import DBManager
from datetime import datetime

st.set_page_config(page_title="AI DW", page_icon="🐍", layout='centered', initial_sidebar_state='auto')

if convert.check_auth() == False:
    st.stop()

########################################################################
# Initialize database and chat manager
########################################################################
db = DBManager()
userInfo = st.session_state.user_info[0]

if 'current_chat' not in st.session_state: # 현재 선택 대화
    st.session_state.current_chat = None
if 'chats' not in st.session_state: # 대화 목록
    st.session_state.chats = db.get_chats(userInfo['userId'])
if 'chat_messages' not in st.session_state:
    st.session_state.chat_messages = [] # 대화 내용

dateYmd = datetime.now().strftime("%Y년%m월%d일")

with st.sidebar:
    if st.button("새 대화 시작하기", key="new_chat", type="primary"):
        # 연속 새 대화 생성 방지
        # if len(st.session_state.chats) == 0 or st.session_state.chats[0][1][:11] != dateYmd:
        if len(st.session_state.chats) == 0 or st.session_state.chats[0][1] != 'New Chat':
            # chat_title = datetime.now().strftime("%Y년%m월%d일 %H시%M분%S초")
            chat_title = 'New Chat'
            chat_id = db.save_chat(userInfo, chat_title)
            st.session_state.current_chat = db.get_chat(chat_id)
            st.session_state.chats = db.get_chats(userInfo['userId'])
    # 사이드바 대화 목록 표시
    rradio = st.empty()
    st.session_state.current_chat = rradio.radio("최근 대화", st.session_state.chats, format_func=lambda x: x[8][5:7] +'.' + x[8][8:10] + ". " + x[1])
    # 모델 선택하기
    llms = st.radio(
        "LLM 모델",
        ["gpt-4-1106-preview", "solar-1-mini-chat", "gemma:2b"], #"gemma:7b", "mixtral:8x7b", "ob-llama2-13b", "solar:10.7b", "mistral"
        captions = ["Laugh out loud.", "Upstage Solar is a compact yet powerful large-language model", "Gemma is a family of lightweight, state-of-the-art open models built by Google DeepMind."])
    if llms == 'gpt-4-1106-preview':
        client = OpenAI(
            api_key=st.secrets["api_dw"]
        )
        # = f"gpt-4-1106-preview"
        # f"https://api.openai.com/v1"
    elif llms == 'solar-1-mini-chat':
        client = OpenAI(
            api_key = st.secrets['api_solar'],
            base_url = "https://api.upstage.ai/v1/solar"
        )
    else:
        client = OpenAI(
            api_key = st.secrets['api_solar'],
            base_url = st.secrets['localLLM']
        )
    st.session_state['openai_model'] = llms

st.title(f"{st.session_state['openai_model']} 👋")


########################################################################
# Welcome Message
########################################################################
if "welcome" in st.session_state:
    for welcome in st.session_state.welcome:
        st.info(st.session_state.welcome[0])
else:
    st.session_state.welcome = []
    welcome_contens = '''
    이름 : 정대우
    삼행시 : 
    정직한 마음으로
    대우하며 서로 존중하는 문화 속에서
    우리 모두 함께 성장하는 대우건설이 되길 바랍니다.

    이름 : 오창원
    삼행시 :
    오늘의 노력이 창의적인 결과를 낳고
    창의력이 매력으로
    원대한 꿈을 대우건설에서 펼치시길 바랍니다
    '''
    welcome_placeholder = st.empty()
    welcome_message = st.session_state['user_info'][0]['orgNm'] + ' ' + st.session_state['user_info'][0]['userNm'] + '님 반갑습니다 🤗 '

    for response in client.chat.completions.create(
        model=st.session_state["openai_model"],
        messages= [ { 'role': "system", 'content' : '이름으로 삼행시를 지어주고 대우건설 직원으로서 희망차고 긍정적인 내용으로 응원의 글을 만들어줘'},
                    { 'role': "assistant", 'content' : welcome_contens},
                    { 'role': "user", 'content' : '이름 : ' + st.session_state['user_info'][0]['userNm'] + '삼행시 :'} ],
        stream=True,
    ):
        for chunk in response.choices:
            if chunk.finish_reason == 'stop':
                break
            welcome_message += chunk.delta.content
        welcome_placeholder.info(welcome_message + "▌")
    welcome_placeholder.info(welcome_message)
    st.session_state.welcome.append(welcome_message)

    # img_response = openai.images.generate(
    #     model="dall-e-2",
    #     prompt=welcome_message,
    #     n=1,
    #     size="256x256"
    # )
    # st.image(img_response.data[0].url)



if st.session_state.current_chat is None:
    st.subheader("👈 왼쪽 메뉴에서 [새 대화 시작하기]를 눌러주세요.")
    st.stop()

chat_id = st.session_state.current_chat[0]
chat_title = st.session_state.current_chat[1]
st.session_state.chat_messages = db.get_chat_messages(chat_id)

# header_container = st.container()
# with header_container:
#     new_chat_title = st.text_input("", value=chat_title)
#     if st.button("대화명 변경하기"):
#         db.update_chat_title(chat_id, new_chat_title)
#         st.session_state.current_chat = db.get_chat_userId(chat_id)
#         st.session_state.chats = db.get_chats_userId(userInfo['userId'])

for chat_message in st.session_state.chat_messages:
    chat_message_id = chat_message[0]
    category = chat_message[2]
    content = chat_message[3]
    if category == 'user':
        with st.chat_message("user"):
            st.markdown(content)
    else:
        with st.chat_message("assistant"):
            st.markdown(content)
            # Display file download buttons
            # files = db.get_generated_files(chat_message_id)
            # for file in files:
            #     data = file[3]
            #     file_name = file

if prompt := st.chat_input("What is up?"):
    # if chat_title[:11] == dateYmd:
    if chat_title[:11] == 'New Chat':
        db.update_chat_title(chat_id, prompt[:20])
        st.session_state.current_chat = db.get_chat(chat_id)
        st.session_state.chats = db.get_chats(userInfo['userId'])
        rradio.radio("최근 대화", st.session_state.chats, format_func=lambda x: x[8][5:7] +'.' + x[8][8:10] + ". " + x[1])

    with st.chat_message("user"):
        message_id = db.save_message(chat_id, "user", prompt, userInfo)
        st.session_state.chat_messages.append(db.get_chat_message(message_id))
        st.markdown(prompt)

    with st.chat_message("assistant"):
        messages = []
        for chat_message in st.session_state.chat_messages:
            messages.append({"role": chat_message[2], "content": chat_message[3]})

        message_placeholder = st.empty()
        full_response = ""
        for response in client.chat.completions.create(
            model=st.session_state["openai_model"],
            messages = messages,
            stream=True,
        ):
            # for chunk in response.choices:
            #     if chunk.finish_reason == 'stop':
            #         break
            #     full_response += chunk.delta.content
            for chunk in response.choices:
                if chunk.finish_reason == 'stop':
                    break
                full_response += chunk.delta.content
            message_placeholder.markdown(full_response + "▌")
        message_placeholder.markdown(full_response)
    message_id = db.save_message(chat_id, "assistant", full_response, userInfo)
    st.session_state.chat_messages.append(db.get_chat_message(message_id))
    # tokens = convert.calculate_tokens(st.session_state.chat_messages, st.session_state["openai_model"])
    # st.caption(tokens)

with st.expander('') :
    st.session_state.chat_messages

st.stop()

# from streamlit_extras.stylable_container import stylable_container
# with stylable_container(
#     key="bottom_content",
#     css_styles="""
#         {
#             position: fixed;
#             bottom: 10px;
#         }
#         """,
# ):
#     uploaded_file = st.file_uploader("Upload PDF ⬆️", type="pdf")

# css = '''
# <style>
# [data-testid='stFileUploader'] {
#     display: flex;
#     align-items: center;
# }
# [data-testid='stFileUploader'] section {
#     padding: 0;
# }
# [data-testid='stFileUploader'] section > input + div {
#     display: none;
# }
# [data-testid='stFileUploader'] section + div {
#     margin-left: 1cm; /* Adjust spacing for browse button */
#     margin-right: auto; /* Push uploaded file name to the right */
# }
# </style>
# '''

# st.markdown(css, unsafe_allow_html=True)

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