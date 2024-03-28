import streamlit as st
from components import convert
from datetime import datetime, timedelta
from PublicDataReader import TransactionPrice
import PublicDataReader as pdr

st.set_page_config(page_title="AI NEWS", page_icon="🐍", layout='centered', initial_sidebar_state='auto')

if convert.check_auth() == False:
    st.stop()

st.title("AI RIS 🌎")








# 조회 대상 목록 (사업자등록번호 리스트)
b_no = st.text_input('사업자등록번호를 -를 제외한 숫자만 입력해주세요', '1048158180')
api = pdr.Nts(st.secrets['api_public'])
# b_nos = ['b_no', '1111111111']
b_nos = [b_no]
df = api.status(b_nos) # 상태조회
st.write(df)

# 실거래가 조회
sigungu_name = st.text_input('시군구명을 입력해주세요', '중구')
api = TransactionPrice(st.secrets['api_public'])
code = pdr.code_bdong()
code.loc[(code['시군구명'].str.contains(sigungu_name)) &
         (code['읍면동명']=='')]

# 특정 년월 자료만 조회하기
df = api.get_data(
    property_type="아파트",
    trade_type="매매",
    sigungu_code="11140",
    year_month="202402",
    )

st.write(df)

# 특정 기간 자료 조회하기
# df = api.get_data(
#     property_type="아파트",
#     trade_type="매매",
#     sigungu_code="41135",
#     start_year_month="202212",
#     end_year_month="202301",
#     )

# st.write(df)