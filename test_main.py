# -*- coding: utf-8 -*-
import pandas as pd
from menta_scraping import MentaScraping
from spread_sheet_api import SpreadSheetAPI
from kick_parts import Parts

# 外部ファイル読込
menta_html_client = MentaScraping()
def_parts = Parts()

# menta情報を格納するDataFrame
menta_df = pd.DataFrame()

# Scripingするページ数
page = 1
while page <= 1:
    # html情報を取得
    from bs4 import BeautifulSoup
    msg_html_info = BeautifulSoup(open('MENTA_msg.html'), 'html.parser')

    # menta情報を取得
    menta_df_tmp = menta_html_client.get_msg_data_info(msg_html_info)

    # 情報取得できなかった時点で終了
    if page == 1:
        menta_df = pd.concat([menta_df, menta_df_tmp])
        page += 1
    else:
        break

# 契約中だけれど、SSに名前の無い方を追加
def_parts.insert_name(menta_df)

# SSに最終連絡日を更新
def_parts.update_date(menta_df)

# MENTA CONTRACT HTMLを取得
from bs4 import BeautifulSoup
cont_html_info = BeautifulSoup(open('MENTA_cont.html'), 'html.parser')
# 契約者情報を取得
cont_df = menta_html_client.get_cont_data_info(cont_html_info)

# 契約日情報の更新
def_parts.add_cont_date(cont_df)

# 契約終了者のシートを移動
def_parts.move_data(cont_df)
