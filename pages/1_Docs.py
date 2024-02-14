import streamlit as st
from components import convert

st.set_page_config(page_title="AI DW", page_icon="🐍", layout='centered', initial_sidebar_state='auto')

if convert.check_auth() == False:
    st.stop()

helpdown = '''

# Documentation
######

## 알아두면 좋은 지식들
---
* **파이썬** - [python](https://www.python.org) 
* **파이썬 시각화 웹 애플리케이션** - [Streamlit](https://streamlit.io/) 
* **챗지피티** - [ChatGPT](https://chat.openai.com), [OpenAI API](https://platform.openai.com/docs/introduction)
* **마크다운** - [Markdown Live Preview](https://markdownlivepreview.com/)
* **RAG(Retrieval Augmented Generation)**- [Chroma](https://www.trychroma.com), [Langchain](https://www.langchain.com) 

#

## What's new *이런 것들을 할 수 있어요*
---
* **챗GPT-4 사용해보기** `#GPT4` `#Few Shot`
* **경제 지표 분석 및 동종사 비교** `#GPT4` `#yfinance`
* **글로벌 실시간 뉴스 요약 및 분석** `#GPT4` `#feedparser` `#MarkDown`
* **AI 주가 예측** `#prophet`
* **RAG / 문서 임베딩(Embeddings)** `#Chroma` `#Langchain`
* **SAP 데이터 분석** `#PyRFC` `#PyGWalker`
* **개인PC에서 직접 해볼 수 있어요**- [GitHub](https://github.com/5712labs/scal)

#

## Prompt Technique
---
##### 1. 가이드라인
* **작업 (Task) - 필수:**  _단순한 용어로 (주제)를 설명해줘_
* **맥락 (Context) - 중요:**  _내가 초보자라고 생각하고 설명해줘_
* **예시 (Example) - 중요:**  _단순한 용어로 (주제)를 설명해줘_
* **페르소나 (Persona) - 선택:** _너는 (주제) 관련분야의 전문가야_
* **형식 (Format) - 선택:** _단순한 용어로 (주제)를 설명해줘_
* **어조 (Tone) - 선택:** _내가 신입사원이라고 생각하고 (맥락) 그 수준에 맞는 용어와 어조를 사용해줘_

```
chatgpt에게 훌륭한 프롬프트를 만들어서 질문하고 싶어
내가 건설회사의 신입사원이라고 생각하고 설명해줘
[작업] [맥락] [예시] [페르소나] [형식] [어조] 순으로 상세하고 설명해주고
예를 들어서 알려줘
```

```
작업: 건설프로젝트에서 일정과 예산을 관리하는 방법에 대해 설명해주세요.
맥락: 저는 건설회사의 신입사원으로서, 처음으로 큰 규모의 프로젝트 일정과 예산을 관리하는 책임을 맡게 되었습니다.
예시: 프로젝트 초기 단계에서 리소스를 계획하고 할당하는 방법, 예상치 못한 지출에 대응하는 전략, 프로젝트 과정 중에 일정을 조정하는 방법 등
페르소나: 저를 경험이 풍부한 프로젝트 관리자로 생각해 주시고 조언해주시면 감사하겠습니다.
형식: 단계별 가이드 형식으로 상세한 절차와 팁을 제공해주세요.
어조: 상황을 잘 이해할 수 있도록 교육적이고 지원적인 어조로 설명해주시면 좋겠습니다.
```

#####

##### 2. Few Shot 기법
* **Zero Shot:**  _아무런 예시도 주지 않는 것_
```
Add 2+2:

다음과 같은 텍스트는 어떤 카테고리에 속할까요? 
예시: 고양이는 사람에게 인기 있는 애완동물입니다
```
* **One Shot:**  _예시를 하나만 준 것_
```
Add 3+3: 6
Add 2+2:

다음과 같은 텍스트는 어떤 카테고리에 속할까요? 
예시: 고양이는 사람에게 인기 있는 애완동물입니다
카테고리: 동물
예시: 어제 새로운 혜성이 발견되었습니다
```

* **Few Shot:**  _두 개 이상의 예시를 준 것_
```
Add 3+3: 6
Add 5+5: 10
Add 2+2:

다음과 같은 텍스트는 어떤 카테고리에 속할까요?
예시: 고양이는 사람에게 인기 있는 애완동물입니다
카테고리: 동물
예시: 어제 새로운 혜성이 발견되었습니다
카테고리: 천문학
예시: 런던 대극장에서 셰익스피어 연극이 상연됩니다.
카테고리:
```

#####

##### 3. 형식 지정 기법
```
#명령문
당신은 경험이 풍부한 프로젝트 관리자입니다. 
이하의 제약조건과 입력문을 바탕으로 건설 프로젝트의 일정과 예산 관리에 관한 단계별 가이드를
교육적이고 지원적인 어조로 상세하게 설명해주십시오.

#제약조건
- 프로젝트 초기 리소스 계획 및 할당 방법을 포함한다
- 예상치 못한 지출에 대응하는 전략을 포함한다
- 일정 조정 방법을 포함한다
- 신입사원이 이해하고 실행할 수 있도록 명확하고 실질적인 팁을 제공한다

#입력문
- 건설프로젝트에서 일정과 예산을 관리하는 방법에 대해 설명해주세요

#출력문

```

#####
## 이렇게도 활용해요
---
* **[CHATGPT에게] GPT와 관련된 초대장 이미지 만들어줘**
* **[PHOTOSHOP에서] 모니터 사이즈 크게해줘**
'''

# ## Tables
# ---
# | Left columns  | Right columns |
# | ------------- |:-------------:|
# | left foo      | right foo     |
# | left bar      | right bar     |
# | left baz      | right baz     |

# #

# #

# ## 행복하세요
# ### 행복하세요
# #### 행복하세요
# ##### 행복하세요
# ###### 행복하세요
# 행복하세요

st.markdown(helpdown)

cols = st.columns(2)
with cols[0]:
    st.image('./images/240215_p01.webp')
with cols[1]:
    st.image('./images/240215_p02.webp')