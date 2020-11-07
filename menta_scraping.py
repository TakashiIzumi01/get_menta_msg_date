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
        概要：MENTA契約者ページHTMLから名前情報を取得
        """
        msgs = cont_html_info.findAll('a', href=re.compile('https://menta.work/user/'))

        df = pd.DataFrame(index=[], columns=['name'])
        for msg in msgs:
            text = msg.get_text()
            text = text.strip()  # 空白削除

            df = df.append(pd.Series([text], index=df.columns), ignore_index=True)

        return df


if __name__ == "__main__":
    get_menta_client = MentaScraping()

    # 単体テスト用 メッセージ取得
    msg_html_info = get_menta_client.get_msg_html_info(1)
    msg_html_info = BeautifulSoup(open('MENTA_20200915.html'), 'html.parser')
    msg_list_df = get_menta_client.get_msg_data_info(msg_html_info)
    print(msg_list_df)

    # 単体テスト用 契約者情報取得
    # cont_html_info = get_menta_client.get_cont_html_info()
    cont_html_info = BeautifulSoup(open('MENTA_cont_list.html'), 'html.parser')
    cont_list_df = get_menta_client.get_cont_data_info(cont_html_info)
    print(cont_list_df)
