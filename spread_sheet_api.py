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
        self.sheet1 = os.environ['SHEET1']
        self.sheet2 = os.environ['SHEET2']
        self.insert_name_columns = int(os.environ['INSERT_NAME_COLUMNS'])
        self.insert_date_columns = int(os.environ['INSERT_DATE_COLUMNS'])
        self.insert_person_columns = int(os.environ['INSERT_PERSON_COLUMNS'])
        self.insert_cont_start_columns = int(os.environ['INSERT_CONT_START_COLUMNS'])
        self.insert_cont_end_columns = int(os.environ['INSERT_CONT_END_COLUMNS'])

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
        self.worksheet1 = gc.open_by_key(self.spreadsheet_key).worksheet(self.sheet1)
        self.worksheet2 = gc.open_by_key(self.spreadsheet_key).worksheet(self.sheet2)

        # 修正が手間なのでリターンとして以下を返す
        return self.worksheet1

    def ss_orthopaedy(self):
        """
        概要：SSのデータの形を整形
        """
        # SSの情報を取得
        ss_df = pd.DataFrame(self.get_ss_info().get_all_values())

        # 1行目をpadasのカラム名に変更
        ss_df.columns = list(ss_df.loc[0, :])
        # 上記対応で不要となった１行目を削除
        ss_df.drop(0, inplace=True)

        # index_noカラム追加
        index_columns = []
        for n in range(2, len(ss_df)+2):
            index_columns.append(n)
        ss_df['index_no'] = index_columns

        # pandasのindex番号をリセット
        ss_df = ss_df.reset_index(drop=True)

        return ss_df


    def name_insert(self, contact_non_name_df, ss_df):
        """
        概要：SSに名前データを追加、追加した名前の更新場所をリスト形式で返す
        """
        contact_row = len(contact_non_name_df)
        # 契約中だけれどSSに名前がない場合、名前を追加
        if contact_row > 0:
            index_no_list = []
            for n in range(contact_row):
                # insertする行数を取得
                insert_row = ss_df['index_no'].max() + n + 1
                index_no_list.append(insert_row)  # 日付データInsert用

                # insertする名前を取得
                name_tmp = contact_non_name_df['name'].values.tolist()
                insert_value = name_tmp[n]

                # SSに書き込み処理
                self.get_ss_info().update_cell(insert_row, self.insert_name_columns, insert_value)

        else:
            index_no_list = []

        return index_no_list


    def date_update(self, match_df, flag):
        """
        概要：SSに日付データを更新
             2021/05/22:最終連絡者情報の更新も追加
        """
        match_row = len(match_df)

        # 結合処理結果が存在する場合はSSに書込
        if match_row > 1:
            for n in range(match_row):
                # insertする行数を取得
                index_tmp = match_df['index_no']
                insert_row = index_tmp[n]

                # insertするデータとスプシ場所の取得
                if flag==0:
                    tmp_data = match_df['date'].values.tolist()
                    ss_place = self.insert_date_columns

                else:
                    tmp_data = match_df['person'].values.tolist()
                    ss_place = self.insert_person_columns

                insert_value = tmp_data[n]

                # SSに書込み処理
                self.get_ss_info().update_cell(insert_row, ss_place, insert_value)


    def update_cont_date(self, cont_df, args):
        """
        概要：契約日情報の更新
        引数：args=0:契約日の更新、args=1:契約終了日の更新
        """
        # update処理
        num = len(cont_df)
        for n in range(num):
            # insertする行数を取得
            index_tmp = cont_df['index_no']
            insert_row = index_tmp[n]

            if args == 0:
                # insertする日付データを取得
                date_tmp = cont_df['cont_start_date'].values.tolist()
                insert_value = date_tmp[n]

                # 契約日情報を更新
                self.get_ss_info().update_cell(insert_row, self.insert_cont_start_columns, insert_value)

            else:
                # insertする日付データを取得
                date_tmp = cont_df['cont_end_date'].values.tolist()
                insert_value = date_tmp[n]

                # 契約日情報を更新
                self.get_ss_info().update_cell(insert_row, self.insert_cont_end_columns, insert_value)


    def end_list_insert(self, end_lists):
        """
        概要：卒業生シートに契約終了者情報を追加
        """
        # insert処理
        for end_list in end_lists:
            self.worksheet2.append_row(end_list)


    def end_list_delete(self, end_list_rows):
        """
        概要：現役生シートから契約終了者情報の削除
        """
        # 削除処理
        for end_list_row in end_list_rows:
            self.worksheet1.delete_row(end_list_row)


if __name__ == "__main__":
    ss_api = SpreadSheetAPI()
    ss_info = ss_api.get_ss_info()
    ss_df = pd.DataFrame(ss_info.get_all_values())

    print("#############")
    print(ss_df)
    print("#############")
