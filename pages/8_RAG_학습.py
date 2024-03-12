import streamlit as st
from components import convert
import os
import pandas as pd
from datetime import datetime, timedelta
from langchain.text_splitter import CharacterTextSplitter
# from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_community.document_loaders import WebBaseLoader
from langchain_openai import OpenAIEmbeddings
from langchain_community.embeddings.sentence_transformer import (
    SentenceTransformerEmbeddings,
)

title = 'RAG - LLM Learning'
st.set_page_config(page_title=title, page_icon="🐍", layout="wide")
st.title(title)

if convert.check_auth() == False:
    st.stop()

os.environ['OPENAI_API_KEY'] = st.secrets["api_dw"]

persist_directory="db"
embeddings = OpenAIEmbeddings()

tab1, tab2 = st.tabs(
    [
        "전체목록",
        "🗃 학습하기"
    ]
    )

#########################################################################
### 전체목록_Chroma #######################################################
#########################################################################
with tab1:

    vectordb = Chroma(
        embedding_function=embeddings,
        persist_directory=persist_directory)  

    input_user_query = st.text_input("이름", "", key="input_user_query")

    datte = int(datetime.today().strftime('%Y%m%d'))
    
    input_updt_query = st.number_input(f'일자: 년월일 8자리 {datetime.today().strftime("%Y%m%d")}(전체일자 조회 시 0)', value=datte, format='%d')
    if input_user_query:
        ids_df = vectordb.get(where = {"userNm": input_user_query} )
    if input_updt_query:
        updat = str(input_updt_query)[:4]
        updat = str(input_updt_query)[4:6]
        updat = str(input_updt_query)[6:8]
        updat = str(input_updt_query)[:4] + '년 ' + str(input_updt_query)[4:6] + '월 ' + str(input_updt_query)[6:8] + '일'
        ids_df = vectordb.get(where = {"updat": updat} )

    else:
        ids_df = pd.DataFrame(vectordb.get())

    if len(ids_df) > 0:
        delete_all_ids_button = st.button("전체값 제거", type='primary')
        if delete_all_ids_button:
            check_df = pd.DataFrame()
            if type(ids_df) == type(check_df):
                all_ids = ids_df['ids'].values.tolist()
            else :
                all_ids = ids_df['ids']
            vectordb.delete(ids=all_ids)
            
    st.dataframe(
        data=ids_df,

        height=2000,
        width=2000,
        hide_index=False,
        column_config={
            "documents": st.column_config.TextColumn(
                width=900,
                # help="Streamlit **widget** commands 🎈",
                # default="st.",
                # max_chars=500,
                # validate="^st\.[a-z_]+$",
            ),
            "widgets": st.column_config.Column(
                width='large'
            )
        }
    )

#########################################################################
### 학습_Chroma #########################################################
#########################################################################
with tab2:

    def chunk_documents(documents):

        documents_chroma = [documents]
        chunk_size = 1000
        text_chroma_splitter = CharacterTextSplitter(
            chunk_size=chunk_size, 
            chunk_overlap=20,
            add_start_index = True,
            )
        date = datetime.today().strftime('%Y년 %m월 %d일 %H시%M분')

        metadata = [{'orgNm': st.session_state.user_info[0]['orgNm'],
                    'userNm': st.session_state.user_info[0]['userNm'],
                    'orgCd': st.session_state.user_info[0]['orgCd'],
                    'userId': st.session_state.user_info[0]['userId'],
                    'email': st.session_state.user_info[0]['email'],
                    'updat': datetime.today().strftime('%Y년 %m월 %d일'),
                    'uptim': date}]
        documents_chroma = text_chroma_splitter.create_documents(documents_chroma, metadatas = metadata )

        tokens = convert.calculate_tokens(documents_chroma[0].page_content, 'text-embedding-ada-002')

        st.info(f""" 
                {len(documents_chroma)}개의 문서에 포함된 {len(documents_chroma[0].page_content)}개의 단어를 {chunk_size} 청크 단위로 {len(documents_chroma)}개의 문서로 분할 하였습니다.
                {convert.num_tokens_from_string(documents_chroma[0].page_content, encoding_name="cl100k_base")} 토큰이 예상됩니다
                {tokens}
                """)

        with st.expander('학습 자료 상세보기'):
            st.write(documents_chroma)
        return documents_chroma
    
    def save_documents(documents):
        vectordb_up = Chroma.from_documents(
            documents=documents,
            embedding=embeddings, 
            persist_directory=persist_directory)  
            # vectordb_up.persist()
            # vectordb_up = None
        # vectordb_faiss = FAISS.from_documents(documents, embeddings)
        # vectordb_faiss.save_local("faiss_index")

        st.info(f"""
        ### 업로드를 완료하였습니다.
        #### Chroma
        [https://docs.trychroma.com/getting-started/](https://docs.trychroma.com/getting-started/)
        """)

    input_url = st.text_input("(첫번째 학습 방법) url을 입력하세요",'', key='llm_InputUrl')
    if input_url:
        loader = WebBaseLoader(input_url)
        data = loader.load()
        documents = chunk_documents(data[0].page_content)
        def clear_url():
            del st.session_state["llm_InputUrl"]
        clear_url_button = st.button(label="학습 자료 다시 입력하기", type='primary', on_click=clear_url, key='clearUrl')
        upsert_ui_url = st.empty()
        upsert_url = upsert_ui_url.button("Upsert to Chroma Local DB", type='primary', key='upsertUrl') #, , disabled= False)
        if upsert_url :
            upsert_ui_url.empty()
            with st.spinner('Wait for it...') :
                save_documents(documents)

    st.divider()

    input_file = st.file_uploader("(두번째 학습 방법) 파일을 선택하세요", accept_multiple_files=False, key='llm_InputFile')
    if input_file:
        bytes_data = input_file.read().decode('utf-8')
        documents = chunk_documents(bytes_data)
        upsert_ui_file = st.empty()
        upsert_file = upsert_ui_file.button("Upsert to Chroma Local DB", type='primary', key='upsertFile')
        if upsert_file :
            upsert_ui_file.empty()
            with st.spinner('Wait for it...') :
                save_documents(documents)
    st.divider()

    input_user = st.text_area("(세번째 학습 방법) 학습 데이터를 직접 입력하세요",'', height= 200, key='llm_InputUser')
    if input_user:
        documents = chunk_documents(input_user)
        def clear_user():
            del st.session_state["llm_InputUser"]
        clear_user_button = st.button(label="학습 자료 다시 입력하기", type='primary', on_click=clear_user, key='clearUser')
        upsert_ui_user = st.empty()
        upsert_user = upsert_ui_user.button("Upsert to Chroma Local DB", type='primary', key='upsertUser')
        if upsert_user :
            upsert_ui_user.empty()
            with st.spinner('Wait for it...') :
                save_documents(documents)