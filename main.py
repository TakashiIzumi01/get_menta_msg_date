# -*- coding: utf-8 -*-

from menta_scraping import MentaScraping
from spread_sheet_api import SpreadSheetAPI
from kick_parts import Parts

# 外部ファイル読込
menta_html_client = MentaScraping()
def_parts = Parts()

page = 1
while page <= 100:
    # html情報を取得  TODO:本当はマルチスレッドを起動して複数ページに同時アクセスするようにしたい
    html = menta_html_client.get_msg_html_info(page)

    # menta情報を取得
    menta_df = menta_html_client.get_msg_data_info(html)

    # 情報取得できなかった時点で終了
    if len(menta_df) > 0:
        page += 1
    else:
        break

    # 契約中だけれど、SSに名前の無い方を追加
    def_parts.insert_name(menta_df)

    # SSに最終連絡日を更新
    def_parts.update_date(menta_df)

