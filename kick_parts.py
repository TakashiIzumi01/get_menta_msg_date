# -*- coding: utf-8 -*-

import datetime
from dotenv import load_dotenv
import os
import pandas as pd
import sys

from spread_sheet_api import SpreadSheetAPI

class Parts():
    def __init__(self):
        # .envファイルの内容を読込
        load_dotenv()

        # 何日まえの日付データまで取得するか
        delta_date = int(os.environ['DELTA_DATE'])
        self.date_filter = datetime.date.today() + datetime.timedelta(days=delta_date)

        # 外部ファイル読込
        self.ss_api = SpreadSheetAPI()

    def isnert_name(self, menta_df):
        # 契約中のリストを別途取得
        menta_contract_df = menta_df[menta_df['contract'] == '契約中']

        # ss情報取得
        self.ss_df = self.ss_api.ss_orthopaedy()  # 整形処理

        # 契約中だけれど、SSにないリストの抽出
        contact_non_name_df = pd.merge(self.ss_df, menta_contract_df, left_on='受講生', right_on='name', how='outer', indicator='check')
        contact_non_name_df = contact_non_name_df[contact_non_name_df['check'] == 'right_only']

        # SSに契約中だけれど、SSに無い方の名前追加＋追加した方のSS挿入場所情報の取得
        index_no_list = self.ss_api.name_insert(contact_non_name_df, self.ss_df)
        contact_non_name_df['index_no'] = index_no_list

        # SS挿入場所についてインスタンス化する
        self.contact_non_name_delv_df = contact_non_name_df


    def update_date(self, menta_df):
        # 一致するリストの抽出
        match_df = pd.merge(self.ss_df, menta_df, left_on='受講生', right_on='name')
        # 一定以上前日付のデータは更新しない
        input_list_df = match_df[match_df['date'] > str(self.date_filter)]

        # 契約中だけれどSSに名前が無いリストと一致するリストを結合
        update_df = pd.concat([input_list_df, self.contact_non_name_delv_df])
        update_df = update_df[['name', 'date', 'index_no']]
        update_df = update_df.reset_index(drop=True)

        # SSの日付情報を更新
        self.ss_api.date_update(update_df)
