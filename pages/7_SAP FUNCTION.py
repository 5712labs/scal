import streamlit as st
import json
import pyrfc
import pandas as pd
from components import convert

if convert.check_auth() == False:
    st.stop()

#-------------------
import_param = {
    'TYEAR':'2023',
    'FYEAR':'2017',
    'P_MONAT':'12',
    'P_BONBU':'AAHU0'
}

table_param = {
#     'ITAB':''
}

f = open("./db/sap_connect_dcd.json")
connect = json.load(f)

with pyrfc.Connection(**connect) as conn:
    result = conn.call('ZN_GET_CONST_COST', **import_param, **table_param)

data = []

for line in result["ITAB"]:
    data.append(line)

st.write(pd.DataFrame(data))