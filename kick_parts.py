from dotenv import load_dotenv
import os

from spread_sheet_api import SpreadSheetAPI

class Parts():
    def __init__(self):
        # .envファイルの内容を読込
        load_dotenv()

        # os.environを用いて環境変数を取得
        self.insert_name_columns = int(os.environ['INSERT_NAME_COLUMNS'])
        self.insert_date_columns = int(os.environ['INSERT_DATE_COLUMNS'])

        # 外部ファイル読込
        self.ss_info = SpreadSheetAPI()


    def ss_orthopaedy(self, ss_df):
        """
        概要：SSのデータの形を整形
        """
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
                self.ss_info.get_ss_info().update_cell(insert_row, self.insert_name_columns, insert_value)

        else:
            index_no_list = []

        return index_no_list

    def date_update(self, match_df):
        """
        概要：SSに日付データを更新
        """
        match_row = len(match_df)

        # 結合処理結果が存在する場合はSSに書込
        if match_row > 1:
            for n in range(match_row):
                # insertする行数を取得
                index_tmp = match_df['index_no']
                insert_row = index_tmp[n]

                # insertする日付データを取得
                date_tmp = match_df['date'].values.tolist()
                insert_value = date_tmp[n]

                # SSに書込み処理
                self.ss_info.get_ss_info().update_cell(insert_row, self.insert_date_columns, insert_value)
