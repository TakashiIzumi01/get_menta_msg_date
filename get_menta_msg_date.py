import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import re
import pandas as pd
import datetime
import os

import gspread
import json
from oauth2client.service_account import ServiceAccountCredentials 

class MentaMsgDate():
    def __init__(self):
        self.user_id = "id"  # MENTA Login User ID
        self.password = "pass"  # MENTA Login Password
        self.login_url = "https://menta.work/login"
        self.message_url = "https://menta.work/member/message?page="
        self.page_num = 20  # 最大ページネーション数
        self.json_file = "/spereadsheet-test-a32d0a4b40d9.json"  # こちらのスクリプトに問題なければこちらのファイルもお渡しします。
        self.spreadsheet_key = "16EfYtDFZMHrf_0r7ylb-spYMbN8kduInzqCmEaRWS5A"
        self.delta_date = -3  # 何日前の情報まで取得するか
        self.insert_columns = 8  # 8：H列

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

                    self.ss_info().update_cell(insert_row, self.insert_columns, insert_value)


    # menta message page html info
    def message_html_info(self, page):
        # セッションを開始
        session = requests.session()
        response = session.get(self.login_url)

        # ログイン情報
        login_info = {
            "email":self.user_id,
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
        elems = soup.findAll('div', class_='msg_box__head')
        loop_count = 0
        context_df = pd.DataFrame(index=[], columns=['name','date'])
        for elem in elems:
            temp = elem.text
            tmp = temp.split()
            context_df.loc[loop_count] = tmp
            loop_count += 1

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

