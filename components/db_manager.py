import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

class DBManager:
    def __init__(self, db_name='./db/chat.db'):
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        self._initialize_database()

    def _initialize_database(self):
        # 대화 관련 데이터베이스
        self.execute_query('''
            CREATE TABLE IF NOT EXISTS chats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL DEFAULT 'New Chat',
                user_id TEXT,
                user_nm TEXT,
                org_cd TEXT,
                org_nm TEXT,
                email TEXT,
                created_at DATETIME NOT NULL,
                updated_at DATETIME NOT NULL
            )
        ''')
        self.execute_query('''
            CREATE TABLE IF NOT EXISTS chat_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER,
                category TEXT,
                content TEXT,
                user_id TEXT,
                user_nm TEXT,
                created_at DATETIME NOT NULL,
                updated_at DATETIME NOT NULL,
                FOREIGN KEY(chat_id) REFERENCES chats(id)
            )
        ''')
        self.execute_query('''
            CREATE TABLE IF NOT EXISTS generated_files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_message_id INTEGER,
                name TEXT,
                content BLOB,
                created_at DATETIME NOT NULL,
                updated_at DATETIME NOT NULL,
                FOREIGN KEY(chat_message_id) REFERENCES chat_messages(id)
            )
        ''')

    def execute_query(self, query, params=()):
        self.cursor.execute(query, params)
        self.conn.commit()

    def fetch_query(self, query, params=()):
        self.cursor.execute(query, params)
        return self.cursor.fetchall()

    # Chat Operations
    def save_chat(self, user_info, title):
        now = datetime.now()
        user_id = user_info['userId']
        user_nm = user_info['userNm']
        org_cd  = user_info['orgCd']
        org_nm  = user_info['orgNm']
        email   = user_info['email']
        self.execute_query('''
            INSERT INTO chats (title, user_id, user_nm, org_cd, org_nm, email, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (title, user_id, user_nm, org_cd, org_nm, email, now, now))
        return self.cursor.lastrowid

    def update_chat_title(self, chat_id, title):
        now = datetime.now()
        self.execute_query('''
            UPDATE chats
            SET title = ?, updated_at = ?
            WHERE id = ?
        ''', (title, now, chat_id))

    # 대화 목록 가져오기
    def get_chats(self, user_id):
        # return self.fetch_query("SELECT * FROM chats ORDER BY updated_at DESC")
        return self.fetch_query("SELECT * FROM chats WHERE user_id = ? ORDER BY updated_at DESC LIMIT 5", (user_id,))
        # return self.fetch_query("SELECT * FROM chats WHERE user_id = ? ORDER BY created_at DESC", (user_id,))

    # 아이디로 대화 내용 가져오기
    def get_chat(self, chat_id):
        return self.fetch_query("SELECT * FROM chats WHERE id = ?", (chat_id,))[0]

    # Chat Message Operations
    def save_message(self, chat_id, category, content, user_info):
        user_id = user_info['userId']
        user_nm = user_info['userNm']
        now = datetime.now()
        self.execute_query('''
            INSERT INTO chat_messages (chat_id, category, content, user_id, user_nm, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (chat_id, category, content, user_id, user_nm, now, now))
        return self.cursor.lastrowid

    def get_chat_messages(self, chat_id):
        return self.fetch_query("SELECT * FROM chat_messages WHERE chat_id = ?", (chat_id,))

    def get_chat_message(self, chat_message_id):
        return self.fetch_query("SELECT * FROM chat_messages WHERE id = ?", (chat_message_id,))[0]

    # File Operations
    def save_file(self, chat_message_id, name, content):
        now = datetime.now()
        self.execute_query('''
            INSERT INTO generated_files (chat_message_id, name, content, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (chat_message_id, name, content, now, now))

    def get_generated_files(self, chat_message_id):
        return self.fetch_query("SELECT * FROM generated_files WHERE chat_message_id = ?", (chat_message_id,))

    def get_chat_all_message(self):
        return self.fetch_query("SELECT * FROM chat_messages")

class DBManagerNews:
    def __init__(self, db_name='./db/news.db'):
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        self._initialize_database()

    def _initialize_database(self):
        # 뉴스 관련 데이터베이스
        self.execute_query('''
            CREATE TABLE IF NOT EXISTS news (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nation TEXT,
                conutry TEXT,
                title TEXT,
                deepl_ko TEXT,
                chatgpt_ko TEXT,
                papago_ko TEXT,
                google_ko TEXT,
                link TEXT,
                published DATETIME NOT NULL,
                updated_at DATETIME NOT NULL
            )
        ''')

    def execute_query(self, query, params=()):
        self.cursor.execute(query, params)
        self.conn.commit()

    def fetch_query(self, query, params=()):
        self.cursor.execute(query, params)
        return self.cursor.fetchall()

    # Chat Operations
    def save_news(self, feed, deepl, chatgpt, updated_at):
        nation = feed['nation']
        conutry = feed['conutry']
        title = feed['title']
        deepl_ko  = str(deepl)
        chatgpt_ko = chatgpt
        papago_ko = ''
        google_ko = ''
        link = feed['link']
        published = feed['published']
        self.execute_query('''
            INSERT INTO news (nation, conutry, title, deepl_ko, chatgpt_ko, papago_ko, google_ko, link, published, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (nation, conutry, title, deepl_ko, chatgpt_ko, papago_ko, google_ko, link, published, updated_at))
        return self.cursor.lastrowid

    def get_conutry_news(self, conutry):
        # conutry = feed['conutry']
        # published = feed['published']
        # title = feed['title']
        return self.fetch_query("SELECT * FROM news WHERE conutry = ? ORDER BY updated_at DESC", (conutry,))
        # return self.fetch_query("SELECT * FROM news WHERE title = ? ", (title,))
        # return self.fetch_query("SELECT * FROM chats WHERE user_id = ? ORDER BY created_at DESC", (user_id,))

    def get_news(self, feed):
        conutry = feed['conutry']
        published = feed['published']
        title = feed['title']
        return self.fetch_query("SELECT * FROM news WHERE title = ? ", (title,))
        # return self.fetch_query("SELECT * FROM chats WHERE user_id = ? ORDER BY created_at DESC", (user_id,))

    def del_news(self):
        # conutry = feed['conutry']
        # published = feed['published']
        # title = feed['title']
        return self.fetch_query("delete FROM news")
        # return self.fetch_query("SELECT * FROM chats WHERE user_id = ? ORDER BY created_at DESC", (user_id,))


class DBManagerEconomic:
    # db_name='./db/economic.db'
    # con = sqlite3.connect(db_name)
    # tbl = 'eco2'
    # product_df.to_sql(tbl, con, if_exists='replace', index=True)
    # chk_df = pd.read_sql(f'SELECT * FROM {tbl}', con, index_col=None)

    def __init__(self, db_name='./db/economic.db'):
        self.today = datetime.today()
        self.yesterday = self.today - relativedelta(days=1)
        self.now_ymdh = self.today.strftime("%Y-%m-%d %H:00:00")

        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        # self._initialize_database()
    
     # 경제지표 저장
    def save_eco(self, tbl, df, period='3mo'):
        tbl = tbl + '.' + period
        # st.write(f"save_eco 오늘은 {self.today}")
        # st.write(f"save_eco 어제는 {self.yesterday}")
        # st.write(f"save_eco 지금은 {self.now_ymdh}")
        df['updated_at'] = self.now_ymdh
        df.to_sql(tbl, self.conn, if_exists='replace', index=True)

    # 경제지표 불러오기
    def get_eco(self, tbl, period='3mo'):
        tbl = tbl + '.' + period
        try:
            # df = pd.read_sql(f'SELECT * FROM "{tbl}" where updated_at = "{self.now_ymdh}"', self.conn, index_col='Date')
            df = pd.read_sql(f'SELECT * FROM "{tbl}" where updated_at = "{self.now_ymdh}"', self.conn, index_col='Date')
            return df
        except:
            return []