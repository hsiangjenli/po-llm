# Table ------------------------------------------------------------------------------------------ #
# https://github.com/python/python-docs-zh-tw/wiki/術語列表
# https://zh.wikibooks.org/zh/大陆台湾计算机术语对照表

# Non-Table -------------------------------------------------------------------------------------- #
# https://docs.python.org/zh-tw/3/glossary.html
# https://hackmd.io/@l10n-tw/glossaries

import re
import urllib
from io import StringIO

import pandas as pd
import requests
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

csv_path = __file__.replace("glossary.py", "glossary.csv")


def get_glossary_table(url: str):
    encoded_url = urllib.parse.quote(url, safe="/:")  # 確保 URL 正確編碼
    return pd.read_html(encoded_url, encoding="utf-8")


def get_glossary_from_python_docs_zh_tw():
    url = "https://docs.python.org/zh-tw/3/glossary.html"
    r = requests.get(url)
    r.encoding = "utf-8"
    soup = BeautifulSoup(r.text, "html.parser")
    translated = soup.find_all("dt", class_="translated")

    glossary = []
    pattern = r"([a-zA-Z\s-]+)（([^）]+)）"

    for dt in translated:
        matches = re.findall(pattern, dt.text)

        if matches:
            glossary.extend(matches)

    df = pd.DataFrame(glossary, columns=["原文", "翻譯"])
    return df


def get_glossary_from_hackmd():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()

        page.goto("https://hackmd.io/@l10n-tw/glossaries")
        page.wait_for_load_state("load")

        soup = BeautifulSoup(page.content(), "html.parser")
        df = pd.read_html(StringIO(soup.prettify()), encoding="utf-8")[0]
        df = df[["英文", "臺灣用語"]]
        df.columns = ["原文", "翻譯"]

        return df


if __name__ == "__main__":
    python_docs_zh_tw_df = get_glossary_table(
        url="https://github.com/python/python-docs-zh-tw/wiki/術語列表"
    )[0]
    taiwan_china_computer_terms_df = get_glossary_table(
        url="https://zh.wikibooks.org/zh/大陆台湾计算机术语对照表"
    )[0]
    python_docs_zh_tw_df_official = get_glossary_from_python_docs_zh_tw()
    hackmd_df = get_glossary_from_hackmd()

    # merge two dataframes by columns
    python_docs_zh_tw_df = python_docs_zh_tw_df[["原文", "翻譯"]]
    taiwan_china_computer_terms_df = taiwan_china_computer_terms_df[["English", "臺灣"]]

    # rename columns
    taiwan_china_computer_terms_df.columns = python_docs_zh_tw_df.columns
    df = pd.concat(
        [
            python_docs_zh_tw_df,
            taiwan_china_computer_terms_df,
            python_docs_zh_tw_df_official,
            hackmd_df,
        ],
        axis=0,
    )

    # drop duplicates
    df["原文"] = df["原文"].str.lower()
    df = df.sort_values("原文")

    # if 原文 contains ", " then split it
    df = df.assign(原文=df["原文"].str.split(", ")).explode("原文")

    # remove dashes or symbols in 原文
    df["原文"] = df["原文"].str.replace("[^a-zA-Z0-9]", " ", regex=True)

    # only keep single space
    df["原文"] = df["原文"].str.replace(" +", " ", regex=True)

    df = df.drop_duplicates()
    df.reset_index(drop=True, inplace=True)

    # save to csv
    df.to_csv(csv_path, index=False)
