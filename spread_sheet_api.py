from dotenv import load_dotenv
import gspread
import os
import pandas as pd
from oauth2client.service_account import ServiceAccountCredentials

class SpreadSheetAPI():
    def __init__(self):
        # .envファイルの内容を読込
        load_dotenv()

        # os.environを用いて環境変数を取得
        self.json_file = os.environ['JSON_FILE']
        self.spreadsheet_key = os.environ['SPREADSHEET_KEY']
        self.sheet = os.environ['SHEET']

    def get_ss_info(self):
        """
        概要：スプレットシートにアクセスするための情報を取得
        """
        #2つのAPIを記述しないとリフレッシュトークンを3600秒毎に発行し続けなければならない
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']

        #認証情報設定
        #ダウンロードしたjsonファイル名をクレデンシャル変数に設定（秘密鍵、Pythonファイルから読み込みしやすい位置に置く）
        path = os.getcwd() + '/'
        credentials = ServiceAccountCredentials.from_json_keyfile_name(path + self.json_file, scope)

        #OAuth2の資格情報を使用してGoogle APIにログインします。
        gc = gspread.authorize(credentials)

        #共有設定したスプレッドシートのシートを開く
        worksheet = gc.open_by_key(self.spreadsheet_key).worksheet(self.sheet)

        return worksheet


if __name__ == "__main__":
    ss_api = SpreadSheetAPI()
    ss_info = ss_api.get_ss_info()
    ss_df = pd.DataFrame(ss_info.get_all_values())

    print("#############")
    print(ss_df)
    print("#############")
