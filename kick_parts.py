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

        # ss情報取得
        self.ss_df = self.ss_api.ss_orthopaedy()


    def insert_name(self, menta_df):
        """
        概要：契約中の方をSSに追加する処理
        """
        # 契約中のリストを別途取得
        menta_contract_df = menta_df[menta_df['contract'] == '契約中']

        # 契約中だけれど、SSにないリストの抽出
        print('SSのデータは？')
        print(self.ss_df)
        print('契約者のデータは？')
        print(menta_contract_df)
        contact_non_name_df = pd.merge(self.ss_df, menta_contract_df, left_on='受講生', right_on='name', how='outer', indicator='check')
        contact_non_name_df = contact_non_name_df[contact_non_name_df['check'] == 'right_only']
        print('入力データどうなってる？？')
        print(contact_non_name_df)

        # SSに契約中だけれど、SSに無い方の名前追加＋追加した方のSS挿入場所情報の取得
        index_no_list = self.ss_api.name_insert(contact_non_name_df, self.ss_df)
        contact_non_name_df['index_no'] = index_no_list

        # SS挿入場所についてインスタンス化する
        self.contact_non_name_delv_df = contact_non_name_df

        # 新規契約者が追加になるケースがあるため、ss情報を更新
        self.ss_df = self.ss_api.ss_orthopaedy()



    def update_date(self, menta_df):
        """
        概要：最終連絡日をSSに追加する処理
             2021/05/22：最終連絡者も情報も追加
        """
        # 一致するリストの抽出
        match_df = pd.merge(self.ss_df, menta_df, left_on='受講生', right_on='name')
        # 一定以上前日付のデータは更新しない
        input_list_df = match_df[match_df['date'] > str(self.date_filter)]

        # 契約中だけれどSSに名前が無いリストと一致するリストを結合
        update_df = pd.concat([input_list_df, self.contact_non_name_delv_df], sort=True)
        update_df = update_df[['name', 'date', 'person', 'index_no']]
        update_df = update_df.reset_index(drop=True)

        # SSの日付情報を更新
        self.ss_api.date_update(update_df, 0)

        # SSの最終連絡者情報を更新
        self.ss_api.date_update(update_df, 1)

    def add_cont_date(self, cont_df):
        """
        概要：契約中の方の契約日と契約終了日をスプシに追加
        """
        # 契約中の方のリストを取得
        current_cont_df = pd.merge(self.ss_df, cont_df, left_on='受講生', right_on='name', how='inner')

        # 既に日時情報が最新で更新不要なリストを取得
        unnecessary_df = pd.merge(self.ss_df, cont_df, left_on=['受講生', '契約日', '契約終了日'], right_on=['name', 'cont_start_date', 'cont_end_date'])
        unnecessary_df = unnecessary_df['受講生']

        # 更新が必要なリスト情報を取得
        update_cont_df = pd.merge(current_cont_df, unnecessary_df, on=['受講生'], how='outer', indicator='check')
        update_cont_df = update_cont_df[update_cont_df['check'] == 'left_only']
        update_cont_df = update_cont_df.reset_index(drop=True)  # indexを0から再付与
        update_row_num = len(update_cont_df)

        # 更新対象があれば下記を実施
        if update_row_num > 0:
            cont_start_df = update_cont_df[['name', 'cont_start_date', 'index_no']]
            cont_end_df = update_cont_df[['name', 'cont_end_date', 'index_no']]

            # 契約日更新
            self.ss_api.update_cont_date(cont_start_df, 0)

            # 契約終了日更新
            self.ss_api.update_cont_date(cont_end_df, 1)

        else:
            print('更新対象なし')

    def move_data(self, cont_df):
        """
        概要：契約終了者を現役生から卒業生に移動する処理
        """
        # 契約終了者のリストを取得
        cont_match_df = pd.merge(self.ss_df, cont_df, left_on='受講生', right_on='name', how='outer', indicator='check')
        end_list_df = cont_match_df[cont_match_df['check'] == 'left_only']

        # 契約終了者のindex情報を取得
        end_list_no_df = end_list_df['index_no']
        end_list_rows = end_list_no_df.values.tolist()
        end_list_rows.sort(reverse=True)  # (注)削除行数を降順にしないとデータがどんどん消えるので削除場所を間違う

        # 契約終了者の元々のスプシの情報を取得(mergeで付与された不要カラムを削除)
        end_list_df = end_list_df.drop('index_no', axis=1)
        end_list_df = end_list_df.drop('name', axis=1)
        end_list_df = end_list_df.drop('cont_start_date', axis=1)
        end_list_df = end_list_df.drop('cont_end_date', axis=1)
        end_list_df = end_list_df.drop('check', axis=1)
        end_lists = end_list_df.values.tolist()

        # 契約終了者を卒業生に追加
        self.ss_api.end_list_insert(end_lists)

        # 契約終了者を現役生から削除
        self.ss_api.end_list_delete(end_list_rows)

