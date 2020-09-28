# -*- coding: utf-8 -*-

import datetime
from dotenv import load_dotenv
import os
import pandas as pd
import sys

from menta_scraping import MentaScraping
from spread_sheet_api import SpreadSheetAPI
from kick_parts import Parts

# .envファイルの内容を読込
load_dotenv()

# os.environを用いて環境変数を取得
delta_date = int(os.environ['DELTA_DATE'])  # 何日前の日付データまで取得するか
page_num = int(os.environ['PAGE_NUM'])  # 最大ページネーション数

# 外部ファイル読込
menta_html_info = MentaScraping()
ss_info = SpreadSheetAPI()
def_parts = Parts()

# 日付フィルターを取得
date_filter = datetime.date.today() + datetime.timedelta(days=delta_date)

# TODO:whileではなくスレッドでHTML情報を取得するように修正した方が早いため、修正する
page = 1
while page <= page_num:

    if len(sys.argv) < 2:  # 通常モード
        html = menta_html_info.get_msg_html_info(page)

    else:  # テストモード
        from bs4 import BeautifulSoup
        html = BeautifulSoup(open(sys.argv[1]), 'html.parser')

    # menta情報を取得
    menta_df = menta_html_info.get_msg_data_info(html)

    # 契約中のリストを別途取得
    menta_contract_df = menta_df[menta_df['contract'] == '契約中']

    if len(menta_df) > 0: # 日付情報取得できなかった時点で終了
        page += 1
    else:
        break

    # ss情報取得
    ss_df = pd.DataFrame(ss_info.get_ss_info().get_all_values())
    ss_df = def_parts.ss_orthopaedy(ss_df)  # 整形処理

    # 契約中だけれど、SSにないリストの抽出
    contact_non_name_df = pd.merge(ss_df, menta_contract_df, left_on='受講生', right_on='name', how='outer', indicator='check')
    contact_non_name_df = contact_non_name_df[contact_non_name_df['check'] == 'right_only']

    # SSに契約中だけれど、SSに無い方の名前追加＋追加した方のSS挿入場所情報の取得
    index_no_list = def_parts.name_insert(contact_non_name_df, ss_df)
    contact_non_name_df['index_no'] = index_no_list

    # 一致するリストの抽出
    match_df = pd.merge(ss_df, menta_df, left_on='受講生', right_on='name')
    # 一定以上前日付のデータは更新しない
    input_list_df = match_df[match_df['date'] > str(date_filter)]

    # 契約中だけれどSSに名前が無いリストと一致するリストを結合
    match_df = pd.concat([match_df, contact_non_name_df])
    match_df = match_df[['name', 'date', 'index_no']]
    match_df = match_df.reset_index(drop=True)

    # SSの日付情報を更新
    def_parts.date_update(match_df)
