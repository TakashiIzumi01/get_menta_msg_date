# -*- coding: utf-8 -*-

from bs4 import BeautifulSoup
from dotenv import load_dotenv
import pandas as pd
import os
import requests
import re

import configparser
config = configparser.ConfigParser()

class MentaScraping():
    def __init__(self):
        # url info
        self.login_url = "https://menta.work/login"
        self.msg_url = "https://menta.work/member/message?page="
        self.cont_url = "https://menta.work/member/mentee/monthly/contracting"

        # .envファイルの内容を読込
        load_dotenv()

        # os.environを用いて環境変数を取得
        self.userid = os.environ['USERID']
        self.passwd = os.environ['PASSWD']

        # セッションを開始
        self.session = requests.session()
        response = self.session.get(self.login_url)

        # ログイン情報
        login_info = {
            "email":self.userid,
            "password":self.passwd,
        }

        # BeautifulSoupオブジェクト作成(token取得の為)
        bs = BeautifulSoup(response.text, 'html.parser')
        _token = bs.find(attrs={'name':'_token'}).get('value')

        login_info["_token"] = _token

        # login
        res = self.session.post(self.login_url, data=login_info)
        res.raise_for_status() # エラーならここで例外を発生させる

    def get_msg_html_info(self, page_num):
        """
        概要：MENTAメッセージページHTMLを取得
        """
        # message page
        target_res = self.session.get(self.msg_url + str(page_num))
        target_res.raise_for_status()
        
        # get html
        msg_html_info = BeautifulSoup(target_res.text, 'html.parser')

        return msg_html_info

    def get_cont_html_info(self):
        """
        概要：MENTA 契約者HTMLを取得
        """
        # contract page
        target_res = self.session.get(self.cont_url)
        target_res.raise_for_status()
        
        # get html
        cont_html_info = BeautifulSoup(target_res.text, 'html.parser')

        return cont_html_info

    def get_msg_data_info(self, msg_html_info):
        """
        概要：MENTAメッセージページHTMLから名前と最終やりとり日付情報を取得
        """
        msgs = msg_html_info.findAll('div', class_='msg_box__head')

        df = pd.DataFrame(index=[], columns=['name', 'contract', 'date'])
        for msg in msgs:
            elems1 = msg.find('div', class_='name')
            elems2 = msg.find('span', class_='keiyaku_plan contracting')
            elems3 = msg.find('div', class_='date')

            # name
            text1 = elems1.get_text()
            text1 = text1.strip()  # 空白削除

            # contract
            text2 = elems2.get_text() if elems2 is not None else None
            text2 = text2.strip() if text2 is not None else None # 空白削除

            # date
            text3 = elems3.get_text()
            text3 = re.sub(r'\未読\s\d+', '', text3)  # 未読情報削除
            text3 = text3.strip()  # 空白削除

            df = df.append(pd.Series([text1, text2, text3], index=df.columns), ignore_index=True)

        return df

    def get_cont_data_info(self, cont_html_info):
        """
        概要：MENTA契約者ページHTMLから名前と契約日情報を取得
        """
        msgs = cont_html_info.findAll('a', href=re.compile('https://menta.work/user/'))

        name = []
        for msg in msgs:
            text = msg.get_text()
            text = text.strip()  # 空白削除

            name.append(text)

        # 契約日取得
        dates = cont_html_info.findAll('td', class_="whitespace-no-wrap text-center")

        con_start_date = []
        con_end_date = []

        get_count = 0

        for date in dates:
            tmp_text = date.get_text()
            print('scraping_result')
            print(tmp_text)
            if get_count % 2 == 0:
                text2 = tmp_text.strip()  # 空白削除
                con_start_date.append(text2)
                get_count += 1

            else:
                text3 = tmp_text.strip()  # 空白削除
                text3 = text3.split('日')[0]  # ”日”以降の文字を削除
                text3 = text3 + '日'  # カッコ悪いのでいい方法があれば、、
                con_end_date.append(text3)
                get_count += 1

        # 確認用
        print('契約開始日')
        print(con_start_date)
        print('契約終了日')
        print(con_end_date)

        # nameの最初の方に不要データがあるため、降順に並び替えて名前と契約日を結合する
        name = name[::-1]
        con_start_date = con_start_date[::-1]
        con_end_date = con_end_date[::-1]

        summary_data = [name, con_start_date, con_end_date]
        df_result = pd.DataFrame(summary_data).T  # 行列入れ替え
        df_result.columns = ['name', 'cont_start_date', 'cont_end_date']  # カラム追加
        print('### scraping result ###')
        print(df_result)

        return df_result

if __name__ == "__main__":
    get_menta_client = MentaScraping()

    # 単体テスト用 メッセージ取得
    msg_html_info = get_menta_client.get_msg_html_info(1)
    # msg_html_info = BeautifulSoup(open('MENTA_20200915.html'), 'html.parser')
    # msg_list_df = get_menta_client.get_msg_data_info(msg_html_info)
    # print(msg_list_df)

    # 単体テスト用 契約者情報取得
    # cont_html_info = get_menta_client.get_cont_html_info()
    cont_html_info = BeautifulSoup(open('MENTA_20210107.htm'), 'html.parser')
    cont_list_df = get_menta_client.get_cont_data_info(cont_html_info)
    print(cont_list_df)
