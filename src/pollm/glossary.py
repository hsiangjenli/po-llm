# Table ------------------------------------------------------------------------------------------ #
# https://github.com/python/python-docs-zh-tw/wiki/術語列表
# https://zh.wikibooks.org/zh/大陆台湾计算机术语对照表
# https://github.com/python/python-docs-zh-tw/blob/3.13/terminology_dictionary.csv
# https://github.com/python/python-docs-zh-tw/blob/3.13/focused_terminology_dictionary.csv

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
import warnings
from urllib.error import URLError
from pandas.errors import ParserError, EmptyDataError

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


def get_glossary_from_python_docs_zh_tw_terminology_dictionary_csv(csv_path: str):
    """從 python-docs-zh-tw 取得 terminology CSV，並自動選擇最新數字分支。

    此函式會呼叫 GitHub Branches API，挑選形如 "X.Y" 的數字分支（例如 "3.13"），
    並以最高版本作為來源分支，然後從 raw.githubusercontent.com 讀取指定的 CSV 檔案。

    Parameters
    ----------
    csv_path : str
        倉庫中的 CSV 相對路徑（例如 ``"terminology_dictionary.csv"`` 或
        ``"focused_terminology_dictionary.csv"``）。

    Returns
    -------
    pandas.DataFrame
        讀取後的 DataFrame（欄位可能會在後續程式中重新命名）。

    Raises
    ------
    RuntimeError
        當從 raw.githubusercontent.com 取得 CSV 失敗且無可用備援時拋出，例外資訊會包含失敗原因。
    """

    def _get_latest_numeric_branch():
        api = "https://api.github.com/repos/python/python-docs-zh-tw/branches"
        try:
            resp = requests.get(api, timeout=10)
            resp.raise_for_status()
            branches = [b.get("name", "") for b in resp.json() if isinstance(b, dict)]

            # Filter branches like '3.13', '3.10', etc.
            numeric = [b for b in branches if re.match(r"^\d+\.\d+$", b)]
            if not numeric:
                return None

            def ver_key(s):
                return tuple(int(p) for p in s.split("."))

            return max(numeric, key=ver_key)
        except (requests.RequestException, ValueError) as exc:
            warnings.warn(
                f"Could not fetch branches from GitHub API, falling back to 'main'. Error: {exc}",
                RuntimeWarning,
            )
            return None

    branch = _get_latest_numeric_branch() or "main"

    raw_url = f"https://raw.githubusercontent.com/python/python-docs-zh-tw/{branch}/{csv_path}"

    try:
        df = pd.read_csv(
            raw_url,
            usecols=["source_term", "translated_term"],
            dtype=str,
        )

        # rename column
        df.rename(
            columns={"source_term": "原文", "translated_term": "翻譯"}, inplace=True
        )
        return df[["原文", "翻譯"]]
    except (ParserError, EmptyDataError, URLError) as exc:
        raise RuntimeError(f"Could not fetch terminology CSV from {raw_url}: {exc}")


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


def search_glossary(text: str):
    df = pd.read_csv(csv_path)

    text_lower = text.lower()
    df_filtered = df[df["原文"].str.lower().apply(lambda x: x in text_lower)]

    return df_filtered.drop_duplicates(subset=["原文"]).to_dict(orient="records")


if __name__ == "__main__":
    python_docs_zh_tw_df = get_glossary_table(
        url="https://github.com/python/python-docs-zh-tw/wiki/術語列表"
    )[0]
    taiwan_china_computer_terms_df = get_glossary_table(
        url="https://zh.wikibooks.org/zh/大陆台湾计算机术语对照表"
    )[0]
    python_docs_zh_tw_df_official = get_glossary_from_python_docs_zh_tw()
    python_docs_zh_tw_df_official_2 = (
        get_glossary_from_python_docs_zh_tw_terminology_dictionary_csv(
            csv_path="focused_terminology_dictionary.csv"
        )
    )
    python_docs_zh_tw_df_official_3 = (
        get_glossary_from_python_docs_zh_tw_terminology_dictionary_csv(
            csv_path="terminology_dictionary.csv"
        )
    )
    hackmd_df = get_glossary_from_hackmd()

    # merge two dataframes by columns
    python_docs_zh_tw_df = python_docs_zh_tw_df[["原文", "翻譯"]]
    taiwan_china_computer_terms_df = taiwan_china_computer_terms_df[["English", "臺灣"]]

    # rename columns
    taiwan_china_computer_terms_df.columns = python_docs_zh_tw_df.columns

    # tag sources so we can prefer certain sources when deduplicating
    python_docs_zh_tw_df["__source"] = "python_docs_zh_tw"
    taiwan_china_computer_terms_df["__source"] = "wikibooks"
    python_docs_zh_tw_df_official["__source"] = "official"
    python_docs_zh_tw_df_official_2["__source"] = "official_2"
    python_docs_zh_tw_df_official_3["__source"] = "official_3"
    hackmd_df["__source"] = "hackmd"

    df = pd.concat(
        [
            python_docs_zh_tw_df,
            taiwan_china_computer_terms_df,
            python_docs_zh_tw_df_official,
            python_docs_zh_tw_df_official_2,
            python_docs_zh_tw_df_official_3,
            hackmd_df,
        ],
        axis=0,
    )

    # normalize 原文 並根據來源優先順序去重（優先保留 official_2, official_3）
    priority = {
        "official_2": 0,  # focused_terminology_dictionary.csv
        "official_3": 1,  # terminology_dictionary.csv
        "official": 2,
        "python_docs_zh_tw": 3,
        "wikibooks": 4,
        "hackmd": 5,
    }

    df["__rank"] = df["__source"].map(priority).fillna(99).astype(int)

    # normalize text
    df.dropna(subset=["原文"], inplace=True)
    df["原文"] = df["原文"].astype(str).str.lower()
    # if 原文 contains ", " then split it and explode
    df = df.assign(原文=df["原文"].str.split(", ")).explode("原文")

    # remove unwanted symbols in 原文 but keep underscores (preserve __magic__ names), collapse spaces, strip
    df["原文"] = df["原文"].str.replace("[^a-zA-Z0-9_]", " ", regex=True)
    df["原文"] = df["原文"].str.replace(" +", " ", regex=True).str.strip()

    # sort by 原文 then rank so preferred sources come first
    df = df.sort_values(["原文", "__rank"])

    # drop duplicates by 原文, keeping the first (highest priority)
    df = df.drop_duplicates(subset=["原文"], keep="first")

    # cleanup helper columns
    df = df.drop(columns=["__source", "__rank"], errors="ignore")
    df.reset_index(drop=True, inplace=True)

    # save to csv
    df.to_csv(csv_path, index=False)
