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
        # .envファイルの内容を読込
        load_dotenv()

        # os.environを用いて環境変数を取得
        self.userid = os.environ['USERID']
        self.passwd = os.environ['PASSWD']
        self.login_url = os.environ['LOGIN_URL']
        self.msg_url = os.environ['MSG_URL']

    def get_msg_html_info(self, page_num):
        """
        概要：MENTAメッセージページHTML情報を取得
        """
        # セッションを開始
        session = requests.session()
        response = session.get(self.login_url)

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
        res = session.post(self.login_url, data=login_info)
        res.raise_for_status() # エラーならここで例外を発生させる

        # message page
        target_res = session.get(self.msg_url + str(page_num))
        target_res.raise_for_status()
        
        # get name and date
        html_info = BeautifulSoup(target_res.text, 'html.parser')

        return html_info


    def get_msg_data_info(self, html_info):
        """
        概要：MENTAメッセージページHTMLから名前と最終やりとり日付情報を取得
        """
        msgs = html_info.findAll('div', class_='msg_box__head')

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

if __name__ == "__main__":
    get_menta_info = MentaScraping()
    html_info = get_menta_info.get_msg_html_info(1)

    # 単体テスト用
    html_info = BeautifulSoup(open('MENTA_20200915.html'), 'html.parser')

    contact_list_df = get_menta_info.get_msg_data_info(html_info)
#    contact_list_df.to_csv('/Users/horiuchitakashi/Desktop/python/MENTA_message_date_get/check.csv')
    print(contact_list_df)
