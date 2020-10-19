# -*- coding: utf-8 -*-

from menta_scraping import MentaScraping
from spread_sheet_api import SpreadSheetAPI
from kick_parts import Parts

# 外部ファイル読込
menta_html_info = MentaScraping()
def_parts = Parts()

# menta login
session = menta_html_info.menta_login()

page = 1
while page <= 100:
    # html情報を取得
    from bs4 import BeautifulSoup
    html = BeautifulSoup(open('MENTA_20200915.html'), 'html.parser')

    # menta情報を取得
    menta_df = menta_html_info.get_msg_data_info(html)

    # 情報取得できなかった時点で終了
    if page == 1:
        pass
    else:
        break

    # 契約中だけれど、SSに名前の無い方を追加
    def_parts.isnert_name(menta_df)

    # SSに最終連絡日を更新
    def_parts.update_date(menta_df)

