import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import re
import pandas as pd
import datetime
import os
from dotenv import load_dotenv

import gspread
import json
from oauth2client.service_account import ServiceAccountCredentials 

class MentaMsgDate():
    def __init__(self):
        # .envファイルの内容を読込
        load_dotenv()

        # os.environを用いて環境変数を取得
        self.user = os.environ['USER']
        self.password = os.environ['PASSWORD']
        self.login_url = os.environ['LOGIN_URL']
        self.message_url = os.environ['MESSAGE_URL']
        self.page_num = int(os.environ['PAGE_NUM'])  # 最大ページネーション数
        self.json_file = os.environ['JSON_FILE']
        self.spreadsheet_key = os.environ['SPREADSHEET_KEY']
        self.delta_date = int(os.environ['DELTA_DATE'])  # 何日まえの情報まで取得するか
        self.insert_columns = int(os.environ['INSERT_COLUMNS'])  # 8：H列

    def main_process(self):
        # date filter
        date_filter = datetime.date.today() + datetime.timedelta(days=self.delta_date)

        page = 1
        while page <= self.page_num:
            df = self.message_html_info(page)
            if len(df) < 1: # 日付情報取得できなかった時点で終了
                break
            else:
                page += 1

            input_list_df = df[df['date'] > str(date_filter)]

            # add index columns number
            ss_df = self.ss_read()
            index_columns = []
            for n in range(2, len(ss_df) + 2):
                index_columns.append(n)
            ss_df['index_no'] = index_columns

            # Union
            union_df = pd.merge(ss_df, input_list_df, left_on='受講生', right_on='name')
            union_row = len(union_df)

            # non target data : pass
            if union_row < 1:
                pass

            # exist target data : write SpreadSheet
            else:
                for n in range(union_row):
                    union_df_tmp = union_df['index_no']
                    insert_row = union_df_tmp[n]

                    union_df_tmp2 = union_df['date']
                    insert_value = union_df_tmp2[n]

                    # spreadsheet update
                    self.ss_info().update_cell(insert_row, self.insert_columns, insert_value)


    # menta message page html info
    def message_html_info(self, page):
        # セッションを開始
        session = requests.session()
        response = session.get(self.login_url)

        # ログイン情報
        login_info = {
            "email":self.user,
            "password":self.password,
        }

        # BeautifulSoupオブジェクト作成(token取得の為)
        bs = BeautifulSoup(response.text, 'html.parser')
        _token = bs.find(attrs={'name':'_token'}).get('value')

        login_info["_token"] = _token

        # login
        res = session.post(self.login_url, data=login_info)
        res.raise_for_status() # エラーならここで例外を発生させる

        # message page
        target_res = session.get(self.message_url + str(page))
        target_res.raise_for_status()
        

        # get name and date
        soup = BeautifulSoup(target_res.text, 'html.parser')
#        soup = BeautifulSoup(open('MENTA.html'), 'html.parser')  # test

        # nameデータを取得
        elems = soup.findAll('div', class_='name')
        name_list = []
        for elem in elems:
            name_tmp = elem.text
            name_tmp = name_tmp.strip()  # 空白削除
            name_list.append(name_tmp)

        # dateデータを取得
        elems = soup.findAll('div', class_='date')
        date_list = []
        for elem in elems:
            date_tmp = elem.text
            date_tmp = re.sub(r'\未読\s\d+', '', date_tmp)
            date_tmp = date_tmp.strip()  # 空白削除
            date_list.append(date_tmp)

        context_df = pd.DataFrame({'name':name_list ,
                                   'date':date_list})

        return context_df


    # get SpreadSheet info
    def ss_info(self):
        #2つのAPIを記述しないとリフレッシュトークンを3600秒毎に発行し続けなければならない
        scope = ['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive']

        #認証情報設定
        #ダウンロードしたjsonファイル名をクレデンシャル変数に設定（秘密鍵、Pythonファイルから読み込みしやすい位置に置く）
        path = os.getcwd()
        credentials = ServiceAccountCredentials.from_json_keyfile_name(path + self.json_file, scope)

        #OAuth2の資格情報を使用してGoogle APIにログインします。
        gc = gspread.authorize(credentials)

        #共有設定したスプレッドシートのシート1を開く
        worksheet = gc.open_by_key(self.spreadsheet_key).sheet1

        return worksheet

    def ss_read(self):
        ss_df = pd.DataFrame(self.ss_info().get_all_values())
        ss_df.columns = list(ss_df.loc[0, :])
        ss_df.drop(0, inplace=True)
        ss_df.reset_index(inplace=True)
        ss_df.drop('index', axis=1, inplace=True)

        return ss_df


# 実行処理
menta_msg_date = MentaMsgDate()
menta_msg_date.main_process()

