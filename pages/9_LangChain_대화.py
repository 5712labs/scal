import streamlit as st
import os
import re
import openai
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.retrievers import TimeWeightedVectorStoreRetriever
import pandas as pd
from components import convert

import faiss
from langchain_community.docstore import InMemoryDocstore
from langchain.retrievers import TimeWeightedVectorStoreRetriever
from langchain.schema import Document
from langchain_community.vectorstores import FAISS

title = 'RAG - LLM Chat Completions'
st.set_page_config(page_title=title, page_icon="🐍", layout="centered")

if convert.check_auth() == False:
    st.stop()

st.title(title)

clear_button = st.sidebar.button("새 대화 시작", type="primary", key="clear")
if clear_button:
    del st.session_state['lmessages']

if "lmessages" not in st.session_state:
    st.session_state['lmessages'] = [
        {"role": "system", "content": "", "hide": True}
    ]

for message in st.session_state.lmessages:
    if message["hide"] == False:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

os.environ['OPENAI_API_KEY'] = st.secrets["api_dw"]

persist_directory="db"
embedding = OpenAIEmbeddings()
vectordb = Chroma(
    embedding_function=embedding, 
    persist_directory=persist_directory)  

st.divider()

llm_db_type = st.radio(
    "대화 방식을 지정해주세요",
    ["GPT4", ":rainbow[Chroma]", "***Embedding***"],
    captions = ["내부문서를 사용하지 않아요", "내부 문서로 대화해보세요", "정확도가 높아요"], horizontal = True)

prompt = st.chat_input("Say something")

if prompt:

    def query_search_chroma(query, llm_db_type):
        if llm_db_type == ':rainbow[Chroma]':
            # retriever = vectordb.as_retriever(search_type="mmr")
            # docs = retriever.similarity_search_with_relevance_scores(query, score_threshold=0.7)
            docs = vectordb.similarity_search_with_relevance_scores(query, score_threshold=0.7)
            similarity = 0
        elif llm_db_type == '***Embedding***':
            res = openai.embeddings.create(
                model="text-embedding-ada-002", 
                input=prompt
                )
            wq = res.data[0].embedding
            docs = vectordb.similarity_search_by_vector_with_relevance_scores(
                embedding=wq,
                k=5,
            )
            similarity = 1
        elif llm_db_type == 'FAISS :movie_camera:':
            new_db = FAISS.load_local("faiss_index", embedding)
            docs = new_db.similarity_search_with_relevance_scores(query)
            similarity = 0

        elif llm_db_type == 'Time-weighted':
            embedding_size = 1536
            index = faiss.IndexFlatL2(embedding_size)
            vectorstore = FAISS(embedding, index, "faiss_index", {})
            retriever = TimeWeightedVectorStoreRetriever(
                vectorstore=vectorstore, decay_rate=0.999, k=1
            )
            docs = retriever.get_relevant_documents(query)
            st.write(docs)
            docs = retriever.similarity_search(query)
            st.write(docs)
            st.stop()

            
        docs_md = """
            ###### 유사문서 검색 결과입니다 """
        idx = 0
        docs_list = []
        for doc in docs:
            similarity_score = abs(round((similarity-doc[1])*100, 2)) # 유사도
            idx += 1
            # if idx != 1:
            if similarity_score < 70:
                continue
            if doc[0].page_content not in docs_list: # 중복제거
                docs_list.append(doc[0].page_content)
                # page_content = str(doc[0].page_content)
                page_content = re.sub("\n", "", doc[0].page_content)
                docs_md += f"""
* **```{similarity_score}%```**  {page_content} ```{doc[0].metadata['uptim']} / {doc[0].metadata['orgNm']} {doc[0].metadata['userNm']}```
                """
        if len(docs_list) == 0: 
            docs_md = """ ###### 유사문서를 찾지 못했습니다 """
        docs_df = pd.DataFrame()
        augmented_query = '' # 벡터DB 유사도
        for doc in docs:
            augmented_query += doc[0].page_content + '\n'
            re_df = pd.DataFrame([[doc[1], doc[0].page_content, doc[0].metadata['userNm'], doc[0].metadata['orgNm'], doc[0].metadata['uptim']]])
            query_df = pd.concat([docs_df, re_df])
        if len(docs_df) > 0 :
            docs_df.reset_index(drop=True, inplace=True)
            docs_df.columns = ['score', 'text', '등록자', '부서', '등록일']
        return docs_df, docs_md

    with st.chat_message("user"):
        st.markdown(prompt)

    score = ''
    if llm_db_type == 'GPT4':
        st.session_state.lmessages.append({"role": "user", "content": prompt, "hide": False})
        messages=[
            {"role": m["role"], "content": m["content"]}
            for m in st.session_state.lmessages
        ]
        docs_md = ""
    else:
        docs_df, docs_md = query_search_chroma(prompt, llm_db_type)
        st.session_state.lmessages.append({"role": "assistant", "content": docs_md, "hide": False})
        if len(docs_df) != 0:
            score = docs_df['score'][0] * 100
            score = f' `유사도 {round(score, 2)}%`'

        primer = f""" 
        당신은 Q&A 봇입니다
        각 질문 위의 사용자가 제공한 정보에 기반한 사용자 질문. 
        마지막에 질문에 답하려면 다음과 같은 맥락을 사용합니다.
        사용자가 제공한 정보에서 정보를 찾을 수 없는 경우 진실로 "모르겠습니다"라고 말합니다.
        한국어로 대답해줘
        (유사문서)
        """

        st.session_state.lmessages.append({"role": "user", "content": prompt, "hide": False})
        messages=[{"role": "user", "content": primer + docs_md + prompt}]

        with st.chat_message("assistant"):
            st.markdown(docs_md)

    with st.expander("프롬프트 보기"):
        st.write(st.session_state.lmessages)


    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        for response in openai.chat.completions.create(
            model=st.session_state["openai_model"],
            messages = messages,
            stream=True,
        ):
            for chunk in response.choices:
                if chunk.finish_reason == 'stop':
                    break
                full_response += chunk.delta.content
            message_placeholder.markdown(full_response + "▌")
        message_placeholder.markdown(full_response)
        full_response += f'{score}'
        message_placeholder.markdown(full_response)
        st.session_state.lmessages.append({"role": "assistant", "content": full_response, "hide": False})
        full_response = ''
        score = ''

        tokens = convert.calculate_tokens(docs_md + prompt, st.session_state["openai_model"])
        st.caption(tokens)