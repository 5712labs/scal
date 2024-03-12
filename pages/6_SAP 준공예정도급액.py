import streamlit as st
import json
import pyrfc
import pandas as pd
from datetime import datetime
from dateutil.relativedelta import relativedelta
from pandas.tseries.offsets import MonthEnd, MonthBegin
import altair as alt
from components import convert

st.set_page_config(page_title="AI DW", page_icon="🐍", layout='wide')
if convert.check_auth() == False:
    st.stop()

st.write(""" ### 준공예정원가율 누적변동율 """)
layout_01 = st.container()
layout_04 = st.container()
st.write(""" ### 준공예정원가율 분포""")
layout_02 = st.container()
st.write(""" ### 준공예정도급액 (단위: 천억)""")
layout_03 = st.container()

open_json = "./db/sap_connect_dcp.json"
f = open(open_json)
connect = json.load(f)

## 테이블 READ : 테이블명-ZAACFRM
with pyrfc.Connection(**connect) as conn:
    fields = ['SITPRT', 'CONFROM', 'CONTO']

    if open_json == "./db/sap_connect_dcp.json":
        today = datetime.today()
    else :
        today = datetime.today() - relativedelta(month=1)
    rst01 = conn.call("RFC_READ_TABLE", QUERY_TABLE = "ZTYF91", OPTIONS = [{'TEXT' : "BUKRS EQ '1000'"}, {'TEXT' : f"AND CONTO > '{today}'"}, {'TEXT' : f"AND CONTO NE '99991231'"}], FIELDS = fields, DELIMITER = "|")
    
    # fields = ['SITPRT', 'SEQ', 'APPROVEDATE', 'PLNRATE', 'DGAMT', 'SUM_COST', 'WAERS']
    fields = ['SITPRT', 'APPROVEDATE', 'PLNRATE', 'DGAMT', 'SUM_COST', 'WAERS']
    rst02 = conn.call("RFC_READ_TABLE", QUERY_TABLE = "ZFGT0510",  OPTIONS = [{'TEXT' : "BUKRS EQ '1000'"}], FIELDS = fields, DELIMITER = "|")

    fields = ['PRCTR', 'KTEXT']
    opt01 = "SPRAS = '3'"
    # opt02 = "AND KTEXT = '공정설계팀'"
    # opt02 = "AND KTEXT LIKE '%불광동%'"
    opt02 = ''
    options = [{'TEXT' : opt01}, {'TEXT' : opt02}]
    # rst03 = conn.call("RFC_READ_TABLE", QUERY_TABLE = "CEPCT", OPTIONS = options, FIELDS = fields, DELIMITER = "|")
    rst03 = conn.call("RFC_READ_TABLE", QUERY_TABLE = "CEPCT", OPTIONS = options, FIELDS = fields, DELIMITER = "|")


data = []
columns = []
for line in rst01["DATA"]:
    raw_data = line["WA"].strip().split("|")
    data.append(raw_data)
for line in rst01["FIELDS"]:
    columns.append(line['FIELDTEXT'])
rst01_df = pd.DataFrame(data)
rst01_df.columns = columns
rst01_df.columns = ['현장코드', '시작일', '종료일']
rst01_df['시작일'] = pd.to_datetime(rst01_df['시작일'])
rst01_df['종료일'] = pd.to_datetime(rst01_df['종료일'])
rst01_df['현장코드'] = rst01_df['현장코드'].str.replace(" ", "")

data = []
columns = []
for line in rst03["DATA"]:
    raw_data = line["WA"].strip().split("|")
    data.append(raw_data)
rst03_df = pd.DataFrame(data)
rst03_df.columns = ['현장코드', '현장명']
rst03_df['현장코드'] = rst03_df['현장코드'].str.replace(" ", "")

data = []
for line in rst02["DATA"]:
    raw_data = line["WA"].strip().split("|")
    data.append(raw_data)
rst02_df = pd.DataFrame(data)
rst02_df.columns = ['현장코드', '결재일', '준공예정원가율', '준공예정도급액', '계(사업예정원가)', '통화']
rst02_df['결재일'] = pd.to_datetime(rst02_df['결재일'])
rst02_df['준공예정원가율'] = rst02_df['준공예정원가율'].str.replace('*','10')
rst02_df['준공예정원가율'] = rst02_df['준공예정원가율'].astype('float64')
rst02_df['준공예정도급액'] = rst02_df['준공예정도급액'].str.replace('*','10') #12가 될수도 있음
rst02_df['준공예정도급액'] = rst02_df['준공예정도급액'].astype('float64')
rst02_df['준공예정도급액'] = rst02_df['준공예정도급액'] * 100
rst02_df['계(사업예정원가)'] = rst02_df['계(사업예정원가)'].astype('float64')
rst02_df['현장코드'] = rst02_df['현장코드'].str.replace(" ", "")
rst02_df.drop(rst02_df[(rst02_df['준공예정도급액'] == 0)].index, inplace=True)

# # rst01_df = pd.merge(rst01_df, rst03_df, how='left', on=None)
# rst01_df = pd.merge(rst03_df, rst01_df, how='inner', on='현장코드')
# # merge_df = pd.merge(left=rst02_df, right=rst01_df, how='inner', on='현장코드')
# merge_df = pd.merge(left=rst01_df, right=rst02_df, how='inner', on='현장코드')

merge_df = pd.merge(left=rst03_df, right=rst02_df, how='inner', on='현장코드')
merge_df = pd.merge(left=merge_df, right=rst01_df, how='inner', on='현장코드')
merge_df.sort_values(by=['현장코드', '결재일'], inplace=True)
merge_df.reset_index(drop=True, inplace=True)

last_df = merge_df.loc[merge_df.groupby(['현장코드'])['결재일'].idxmax()]

##########################################################################
### 준공예정도급액 (단위: 천억) ################################################
##########################################################################
bar_chart = alt.Chart(last_df).mark_bar().encode(
    y = alt.X("준공예정도급액", bin=alt.Bin(step=100000000000)), #천억
    x = 'count(*):Q',
)
# layout_03.altair_chart(bar_chart, use_container_width=True)

##########################################################################
### 준공예정원가율 분포 #######################################################
##########################################################################
bar_chart = alt.Chart(last_df).mark_bar().encode(
    alt.X("준공예정원가율:Q", bin=alt.Bin(step=5)), #백억
    y='count()',
)
# layout_02.altair_chart(bar_chart, use_container_width=True)

##########################################################################
### 준공예정원가율 누적변동율 ###################################################
##########################################################################

# change_eco_df = pd.DataFrame() # 변동률
# last_df = pd.DataFrame() # 변동률
# grouped_df = merge_df.groupby('현장코드')
# for key, data in grouped_df :
#     sort_data = data.sort_values(by=['결재일'], ascending=True)
#     sort_data['dpc'] = (sort_data.준공예정원가율/sort_data.준공예정원가율.shift(1)-1)*100
#     sort_data['변동률'] = round(sort_data.dpc.cumsum(), 2)
    
#     change_eco_df = pd.concat([change_eco_df, sort_data])

#     last3_df = pd.DataFrame(change_eco_df.iloc[len(change_eco_df.index)-1]).T
#     last_df = pd.concat([last_df, last3_df])

# change_eco_df = pd.DataFrame()  # 변동률
# grouped_df = merge_df.groupby('현장코드')
# for _, data in grouped_df:
#     sort_data = data.sort_values(by=['결재일'])
#     sort_data['dpc'] = (sort_data['준공예정원가율'].pct_change()) * 100
#     sort_data['변동률'] = round(sort_data['dpc'].cumsum(), 2)
#     change_eco_df = pd.concat([change_eco_df, sort_data])

# change_eco_df = change_eco_df.fillna(0)

# last_df = last_df.fillna(0)
# dpc_zero = last_df[(last_df['변동률'] < 10) & (last_df['변동률'] > -10)]['현장코드']
# last_df = last_df[~last_df['현장코드'].isin(dpc_zero)]
# change_eco_df = change_eco_df[change_eco_df['현장코드'].isin(last_df['현장코드'])]
# merge_df = change_eco_df

# df = change_eco_df
# min_date = pd.to_datetime(df['결재일'].min())
# earliest_dates = df.groupby('현장코드')['결재일'].min().reset_index() # 각 symbol별로 가장 이른 Date 찾기
# new_rows = pd.DataFrame(columns=merge_df.columns) # Preparing DataFrame to collect new rows
# for _, row in earliest_dates.iterrows():
#     symbol_data = df[df['현장코드'] == row['현장코드']]
#     earliest_row = symbol_data[symbol_data['결재일'] == row['결재일']].iloc[0].copy()
#     earliest_row['결재일'] = min_date
#     new_rows = new_rows.append(earliest_row, ignore_index=True)
# merge_df = pd.concat([merge_df, new_rows], axis=0)

# merge_df = merge_df[merge_df['현장코드'] == 'HLDQA']

merge_df['결재일'] = merge_df['결재일'] + MonthEnd()

# min_df = merge_df.loc[merge_df.groupby(['현장코드'])['결재일'].idxmin()]
# min_df['결재일'] = merge_df['결재일'].min()
# max_df = merge_df.loc[merge_df.groupby(['현장코드'])['결재일'].idxmax()]
# max_df['결재일'] = merge_df['결재일'].max()
# merge_df = pd.concat((merge_df, min_df, max_df))
# merge_df = merge_df.drop_duplicates()
# merge_df.sort_values(by=['현장코드', '결재일'], inplace=True)
# merge_df = merge_df.reset_index(drop=True)

option = layout_01.selectbox(
    '',
    ('전체 기간', '최근 3개월', '최근 6개월', '최근 12개월'))
if option == '전체 기간':
    period = datetime.today() - relativedelta(years=30)
elif option == '최근 3개월':
    period = datetime.today() - relativedelta(months=6)
elif option == '최근 6개월':
    period = datetime.today() - relativedelta(months=3)
elif option == '최근 12개월':
    period = datetime.today() - relativedelta(years=1)

merge_df = merge_df[merge_df['결재일'] > period]

min_df = merge_df.loc[merge_df.groupby(['현장코드'])['결재일'].idxmin()]
min_df['결재일'] = merge_df['결재일'].min()
max_df = merge_df.loc[merge_df.groupby(['현장코드'])['결재일'].idxmax()]
max_df['결재일'] = merge_df['결재일'].max()
merge_df = pd.concat((merge_df, min_df, max_df))
merge_df = merge_df.drop_duplicates()


merge_df.sort_values(by=['현장코드', '결재일'], inplace=True)
merge_df = merge_df.reset_index(drop=True)

change_eco_df = pd.DataFrame()  # 변동률
grouped_df = merge_df.groupby('현장코드')
for key, data in grouped_df :
    sort_data = data.sort_values(by=['결재일'], ascending=True)
    # sort_data['dpc'] = (sort_data.준공예정원가율/sort_data.준공예정원가율.shift(1)-1)*100
    sort_data['dpc'] = (sort_data['준공예정원가율'].pct_change()) * 100
    sort_data['변동률'] = round(sort_data.dpc.cumsum(), 2)
    change_eco_df = pd.concat([change_eco_df, sort_data])

last_df = change_eco_df.loc[change_eco_df.groupby(['현장코드'])['결재일'].idxmax()]
last_df = last_df.fillna(0)
dpc_zero = last_df[(last_df['변동률'] < 5) & (last_df['변동률'] > -5)]['현장코드']
last_df = last_df[~last_df['현장코드'].isin(dpc_zero)]
change_eco_df = change_eco_df[change_eco_df['현장코드'].isin(last_df['현장코드'])]
# merge_df = change_eco_df

change_eco_df = change_eco_df.fillna(0)
last_df = last_df.fillna(0)
last_df.sort_values(by=['변동률'], ascending=False, inplace=True)
last_wr = last_df.sort_values('변동률', ascending=False)[['현장코드','현장명','변동률','준공예정원가율','준공예정도급액','종료일']].reset_index(drop=True)
st.write(last_wr)

lines = alt.Chart(change_eco_df).mark_line().encode(
    x = alt.X('결재일:T', title=''),
    # y = alt.Y('준공예정원가율:Q', title=''),
    y = alt.Y('변동률:Q', title=''),
    color = alt.Color('현장명:N', title='지표', legend=alt.Legend(
        orient='bottom', 
        direction='horizontal',
        titleAnchor='end'))
)

text_data = last_df
text_data.reset_index(drop=True, inplace=True)
text_data3 = pd.DataFrame(text_data.loc[0].T)
text_data3 = text_data[:1].copy()
if len(text_data.index) > 1:
    text_data3.loc[1] = text_data.loc[len(text_data.index)-1]
if len(text_data.index) > 2:
    text_data3.loc[2] = text_data.loc[round(len(text_data.index)/2)]

labels = alt.Chart(text_data3).mark_text(
    # point=True,
    fontWeight=600,
    fontSize=15,
    # color='white',
    align='left',
    dx=15,
    dy=-8
).encode(
    x = alt.X('결재일:T', title=''),
    # y = alt.Y('rate:Q', title=rate_text),
    y = alt.Y('변동률:Q', title=''),
    # y = 'rate:Q',
    text=alt.Text('변동률:Q', format='.1f'),
    # text=alt.TextValue(text_data3['현장명'][0] + text_data3['현장명'][0]),
    color = alt.Color('현장명:N', title='')
)

labels2 = alt.Chart(text_data3).mark_text(
    # point=True,
    fontWeight=600,
    fontSize=15,
    # color='white',
    align='left',
    dx=15,
    dy=10
).encode(
    x = alt.X('결재일:T', title=''),
    # y = alt.Y('rate:Q', title=rate_text),
    y = alt.Y('변동률:Q', title=''),
    # y = 'rate:Q',
    text=alt.Text('현장명:N'),
    # text=alt.TextValue(text_data3['현장명'][0] + text_data3['현장명'][0]),
    color = alt.Color('현장명:N', title='')
)

columns = sorted(change_eco_df.현장명.unique())
selection = alt.selection_point(
    fields=['결재일'], nearest=True, on='mouseover', empty=False, clear='mouseout'
)
points = lines.mark_point().transform_filter(selection)

base = alt.Chart(change_eco_df).encode(x='결재일:T')
rule = base.transform_pivot(
    '현장명', value='변동률', groupby=['결재일']
    ).mark_rule().encode(
    opacity=alt.condition(selection, alt.value(0.3), alt.value(0)),
    tooltip=[alt.Tooltip(c, type='quantitative') for c in columns]
).add_params(selection)

layout_04.altair_chart(lines + rule + points + labels + labels2, 
                use_container_width=True)