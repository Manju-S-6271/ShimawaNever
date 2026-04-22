"""tsv_code_generator.py
TSVコード生成モジュール

TSVコード体系定義書（TSV Code Specification）に基づき、
TSVコード・S-TSV検証コード・S-TSVコードを生成する。

対応オブジェクト区分:
    TSV-BK  書籍              (区分コード 200 / 201 / 202)
    TSV-BG  書籍グループ      (区分コード 205)
    TSV-RE  記録資料等        (区分コード 210)
    TSV-IS  資料発行者        (区分コード 215)
    TSV-SH  書架              (区分コード 220)
"""

from __future__ import annotations
import re
import sys
import os
from typing import Optional

# DB参照のためパスを通す
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import database
from models import Book, BookGroup, Record, Issuer, Shelf


# ══════════════════════════════════════════════════════════════
#  § 3.4  チェック数字算出 — モジュール10 ウェイト3
# ══════════════════════════════════════════════════════════════

def calc_check_digit(validation_code: str) -> int:
    """S-TSV検証コード（12桁数字列）からチェック数字を算出する。

    アルゴリズム（モジュール10 ウェイト3 / 仕様 §3.4）:
        1. 左から1桁目を奇数桁とする。
        2. 奇数桁の総和 + 偶数桁の総和×3 を計算する。
        3. 合計を10で割った余り r を求める。
        4. r == 0 → チェック数字 = 0、そうでなければ 10 - r。

    Args:
        validation_code: 12桁の純数字列（S-TSV検証コード）

    Returns:
        チェック数字 (0–9)

    Raises:
        ValueError: 12桁の純数字列でない場合
    """
    if not re.fullmatch(r"\d{12}", validation_code):
        raise ValueError(
            f"S-TSV検証コードは12桁の数字列でなければなりません: {validation_code!r}"
        )

    odd_sum  = sum(int(validation_code[i]) for i in range(0, 12, 2))   # 奇数桁（0-indexed偶数位置）
    even_sum = sum(int(validation_code[i]) for i in range(1, 12, 2))   # 偶数桁（0-indexed奇数位置）
    total = odd_sum + even_sum * 3
    r = total % 10
    return 0 if r == 0 else 10 - r


def verify_check_digit(validation_code: str, check_digit: int) -> bool:
    """チェック数字の整合性を検証する。"""
    return calc_check_digit(validation_code) == check_digit


# ══════════════════════════════════════════════════════════════
#  § 1  コード組み立てユーティリティ
# ══════════════════════════════════════════════════════════════

def _build_tsv_code(
    symbol: str,
    class_code: str,
    unique_number_raw: str,
    separator_rule: str,
) -> str:
    """TSVコードを組み立てる内部関数。

    Args:
        symbol:            オブジェクト区分記号（例: "BK"）
        class_code:        オブジェクト区分コード3桁（例: "200"）
        unique_number_raw: ハイフンなしの9桁固有番号文字列
        separator_rule:    ハイフン挿入位置のリスト（各セグメント長）

    Returns:
        完全記法のTSVコード文字列（チェック数字付き）
    """
    # S-TSV検証コード = オブジェクト区分コード(3) + 固有番号(9)
    validation_code = class_code + unique_number_raw  # 12桁
    check = calc_check_digit(validation_code)

    # 固有番号をseparator_ruleに従ってハイフン区切りに整形
    parts = []
    pos = 0
    for length in separator_rule:
        parts.append(unique_number_raw[pos : pos + length])
        pos += length
    unique_formatted = "-".join(parts)

    return f"TSV-{symbol}-{class_code}-{unique_formatted}-{check}"


def _s_tsv_code(validation_code: str, check: int) -> str:
    """S-TSVコード（13桁純数字）を返す。"""
    return f"{validation_code}{check}"


def build_all_codes(
    symbol: str,
    class_code: str,
    unique_number_raw: str,
    separator_rule: list[int],
) -> dict:
    """TSVコード・S-TSV検証コード・S-TSVコードをまとめて返す。

    Returns:
        {
            "tsv_code":        str,  # 完全記法
            "validation_code": str,  # S-TSV検証コード（12桁）
            "s_tsv_code":      str,  # S-TSVコード（13桁）
            "check_digit":     int,
        }
    """
    validation_code = class_code + unique_number_raw
    check = calc_check_digit(validation_code)
    tsv_code = _build_tsv_code(symbol, class_code, unique_number_raw, separator_rule)
    return {
        "tsv_code":        tsv_code,
        "validation_code": validation_code,
        "s_tsv_code":      _s_tsv_code(validation_code, check),
        "check_digit":     check,
    }


# ══════════════════════════════════════════════════════════════
#  § 2.2.1  TSV-BK  書籍
# ══════════════════════════════════════════════════════════════

def _isbn13_to_raw_and_sep(isbn13: str) -> tuple[str, list[int]]:
    """ISBN-13から固有番号(9桁)とセパレータルールを抽出する。

    ISBN-13の4桁目〜12桁目（0-indexed: [3:12]）の9桁を固有番号とする。
    また、ISBN-13のハイフン区切りをそのまま字区切りに使う（§2.3）。

    Args:
        isbn13: ハイフンなし13桁 or ハイフン付きISBN-13

    Returns:
        (unique_9桁, separator_rule)
    """
    digits = isbn13.replace("-", "").replace(" ", "")
    if not re.fullmatch(r"\d{13}", digits):
        raise ValueError(f"ISBN-13は13桁の数字列でなければなりません: {isbn13!r}")

    unique_raw = digits[3:12]  # 4桁目〜12桁目（0-indexed 3〜11）

    # ハイフン付きの場合は区切り位置を利用する（なければデフォルト）
    if "-" in isbn13:
        # 先頭の978/979プレフィックス部分（3桁）を除いた残りのセグメントを取得
        # ISBN-13: 978-[group]-[publisher]-[title]-[check]
        # 固有番号 = [group][publisher][title] 計9桁
        raw_parts = isbn13.split("-")
        # raw_parts[0] = "978"/"979", raw_parts[-1] = checkdigit
        middle_parts = raw_parts[1:-1]  # group, publisher, title の各セグメント
        sep_rule = [len(p) for p in middle_parts]
        if sum(sep_rule) == 9:
            return unique_raw, sep_rule
    # フォールバック: 区切りなし（9桁まとめ）
    return unique_raw, [9]


def _isbn10_to_raw_and_sep(isbn10: str) -> tuple[str, list[int]]:
    """ISBN-10から固有番号(9桁)とセパレータルールを抽出する。

    ISBN-10の1桁目〜9桁目（0-indexed: [0:9]）の9桁を固有番号とする。

    Args:
        isbn10: ハイフンなし10桁 or ハイフン付きISBN-10

    Returns:
        (unique_9桁, separator_rule)
    """
    digits = isbn10.replace("-", "").replace(" ", "")
    if not re.fullmatch(r"\d{10}", digits):
        raise ValueError(f"ISBN-10は10桁の数字列でなければなりません: {isbn10!r}")

    unique_raw = digits[0:9]  # 1桁目〜9桁目

    if "-" in isbn10:
        raw_parts = isbn10.split("-")
        # ISBN-10: [group]-[publisher]-[title]-[check]
        middle_parts = raw_parts[:-1]  # checkを除く
        sep_rule = [len(p) for p in middle_parts]
        if sum(sep_rule) == 9:
            return unique_raw, sep_rule
    return unique_raw, [9]


def generate_bk_code(
    isbn13: Optional[str] = None,
    isbn10: Optional[str] = None,
    unique_number: Optional[str] = None,
) -> dict:
    """TSV-BK（書籍）のTSVコードを生成する。

    優先度: ISBN-13 > ISBN-10 > unique_number（手動）

    ISBN-13を指定した場合、区分コード200を使用。
    ISBN-10を指定した場合、区分コード201を使用。
    どちらも指定しない場合、区分コード202を使用し unique_number が必要。

    Args:
        isbn13:        ISBN-13文字列（ハイフンあり/なし）
        isbn10:        ISBN-10文字列（ハイフンあり/なし）
        unique_number: 区分コード202用の9桁固有番号（数字のみ）

    Returns:
        build_all_codes() と同じ辞書 + "class_code" キー

    Raises:
        ValueError: 入力不正または重複チェック失敗
    """
    session = database.SessionLocal()
    try:
        if isbn13:
            raw, sep = _isbn13_to_raw_and_sep(isbn13)
            class_code = "200"
            # 重複チェック
            prefix = f"TSV-BK-{class_code}-"
            existing = [b.tsv_code for b in session.query(Book).filter(Book.tsv_code.like(prefix + "%")).all()]
            result = build_all_codes("BK", class_code, raw, sep)
            if result["tsv_code"] in existing:
                # 特例を受けない扱い → 区分コード202へフォールバック
                return _generate_bk_202(session)
            result["class_code"] = class_code
            return result

        if isbn10:
            raw, sep = _isbn10_to_raw_and_sep(isbn10)
            class_code = "201"
            prefix = f"TSV-BK-{class_code}-"
            existing = [b.tsv_code for b in session.query(Book).filter(Book.tsv_code.like(prefix + "%")).all()]
            result = build_all_codes("BK", class_code, raw, sep)
            if result["tsv_code"] in existing:
                return _generate_bk_202(session)
            result["class_code"] = class_code
            return result

        if unique_number is not None:
            if not re.fullmatch(r"\d{9}", unique_number):
                raise ValueError(f"固有番号は9桁の数字列でなければなりません: {unique_number!r}")
            # 3桁ごと区切り
            sep = [3, 3, 3]
            result = build_all_codes("BK", "202", unique_number, sep)
            result["class_code"] = "202"
            return result

        # ISBN なし & unique_number なし → DB上の次の未使用番号を割り当て
        return _generate_bk_202(session)

    finally:
        session.close()


def _generate_bk_202(session) -> dict:
    """区分コード202の書籍TSVコードを自動採番して返す。"""
    prefix = "TSV-BK-202-"
    existing_codes = {b.tsv_code for b in session.query(Book).filter(Book.tsv_code.like(prefix + "%")).all()}
    for n in range(1_000_000_000):
        raw = f"{n:09d}"
        candidate = build_all_codes("BK", "202", raw, [3, 3, 3])
        if candidate["tsv_code"] not in existing_codes:
            candidate["class_code"] = "202"
            return candidate
    raise RuntimeError("TSV-BK-202 の未使用番号が枯渇しました。")


# ══════════════════════════════════════════════════════════════
#  § 2.2.2  TSV-BG  書籍グループ
# ══════════════════════════════════════════════════════════════

def generate_bg_code(unique_number: Optional[str] = None) -> dict:
    """TSV-BG（書籍グループ）のTSVコードを生成する。

    unique_number を指定しない場合、DBを参照して次の未使用番号を自動採番する。

    Args:
        unique_number: 9桁固有番号（省略時は自動採番）

    Returns:
        build_all_codes() と同じ辞書
    """
    session = database.SessionLocal()
    try:
        prefix = "TSV-BG-205-"
        existing = {bg.tsv_code for bg in session.query(BookGroup).filter(BookGroup.tsv_code.like(prefix + "%")).all()}

        if unique_number is not None:
            if not re.fullmatch(r"\d{9}", unique_number):
                raise ValueError(f"固有番号は9桁の数字列でなければなりません: {unique_number!r}")
            result = build_all_codes("BG", "205", unique_number, [3, 3, 3])
            if result["tsv_code"] in existing:
                raise ValueError(f"TSVコードが既に使用されています: {result['tsv_code']}")
            return result

        for n in range(1_000_000_000):
            raw = f"{n:09d}"
            candidate = build_all_codes("BG", "205", raw, [3, 3, 3])
            if candidate["tsv_code"] not in existing:
                return candidate
        raise RuntimeError("TSV-BG-205 の未使用番号が枯渇しました。")
    finally:
        session.close()


# ══════════════════════════════════════════════════════════════
#  § 2.2.3  TSV-RE  記録資料等
# ══════════════════════════════════════════════════════════════

def generate_re_code(issuer_tsv_code: str) -> dict:
    """TSV-RE（記録資料等）のTSVコードを生成する。

    固有番号 = 発行者番号(5桁) + 発行者別資料番号(4桁)
    発行者別資料番号は、同一発行者内で最小の未使用番号を割り当てる。
    字区切りは「発行者番号-資料番号」。

    Args:
        issuer_tsv_code: 関連付けるTSV-ISオブジェクトのTSVコード

    Returns:
        build_all_codes() と同じ辞書 + "issuer_number", "doc_number" キー

    Raises:
        ValueError: 発行者TSVコードが不正または発行者番号が取得できない場合
    """
    session = database.SessionLocal()
    try:
        issuer = session.query(Issuer).get(issuer_tsv_code)
        if issuer is None:
            raise ValueError(f"発行者が見つかりません: {issuer_tsv_code!r}")

        # 発行者番号を TSVコードから抽出する
        # フォーマット: TSV-IS-215-XXXX-YYYYY-C
        #   XXXX = 4桁プレフィックス（0000 or 0001）
        #   YYYYY = 発行者番号5桁
        m = re.match(
            r"TSV-IS-215-(\d{4})-(\d{5})-\d",
            issuer_tsv_code,
        )
        if m is None:
            raise ValueError(
                f"発行者TSVコードのフォーマットが不正です: {issuer_tsv_code!r}"
            )
        issuer_number_str = m.group(2)  # 5桁の発行者番号

        # 同一発行者に関連付けられた記録資料の資料番号一覧を取得
        existing_records = (
            session.query(Record)
            .filter(Record.issuer_tsv_code == issuer_tsv_code)
            .all()
        )
        used_doc_numbers: set[int] = set()
        for rec in existing_records:
            m2 = re.match(r"TSV-RE-210-\d{5}-(\d{4})-\d", rec.tsv_code)
            if m2:
                used_doc_numbers.add(int(m2.group(1)))

        # 最小の未使用資料番号（0000〜9999）を採番
        doc_number: Optional[int] = None
        for n in range(10_000):
            if n not in used_doc_numbers:
                doc_number = n
                break
        if doc_number is None:
            raise RuntimeError(
                f"発行者 {issuer_tsv_code} の発行者別資料番号が枯渇しました。"
            )

        issuer_number_raw = issuer_number_str              # "00001" など
        doc_number_raw    = f"{doc_number:04d}"            # "0001" など
        unique_raw        = issuer_number_raw + doc_number_raw  # 9桁

        # 字区切り: 発行者番号(5桁) + 資料番号(4桁)
        sep = [5, 4]
        result = build_all_codes("RE", "210", unique_raw, sep)
        result["issuer_number"] = issuer_number_raw
        result["doc_number"]    = doc_number_raw
        return result

    finally:
        session.close()


# ══════════════════════════════════════════════════════════════
#  § 2.2.4  TSV-IS  資料発行者
# ══════════════════════════════════════════════════════════════

# システム予約番号
_ISSUER_RESERVED_NUMBERS = {"00000", "00001"}

def generate_is_code(unique_number: Optional[str] = None) -> dict:
    """TSV-IS（資料発行者）のTSVコードを生成する。

    固有番号 = "0000" + 発行者番号(5桁)
    通常オブジェクトの発行者番号は 00002〜99999 の未使用番号から採番。
    字区切りは "0000-YYYYY"。

    Args:
        unique_number: 5桁の発行者番号（省略時は自動採番）

    Returns:
        build_all_codes() と同じ辞書 + "issuer_number" キー
    """
    session = database.SessionLocal()
    try:
        prefix = "TSV-IS-215-"
        existing_issuers = session.query(Issuer).filter(
            Issuer.tsv_code.like(prefix + "%")
        ).all()

        # 使用済み発行者番号セット（5桁文字列）
        used_numbers: set[str] = set()
        for iss in existing_issuers:
            m = re.match(r"TSV-IS-215-\d{4}-(\d{5})-\d", iss.tsv_code)
            if m:
                used_numbers.add(m.group(1))

        if unique_number is not None:
            if not re.fullmatch(r"\d{5}", unique_number):
                raise ValueError(f"発行者番号は5桁の数字でなければなりません: {unique_number!r}")
            if unique_number in _ISSUER_RESERVED_NUMBERS:
                raise ValueError(f"発行者番号 {unique_number} はシステム予約番号です。")
            issuer_number = unique_number
        else:
            # 00002 から順に未使用番号を探す
            issuer_number = None
            for n in range(2, 100_000):
                candidate = f"{n:05d}"
                if candidate not in used_numbers:
                    issuer_number = candidate
                    break
            if issuer_number is None:
                raise RuntimeError("TSV-IS の発行者番号が枯渇しました。")

        # 固有番号 = "0000" + 5桁発行者番号
        unique_raw = "0000" + issuer_number
        sep = [4, 5]  # "0000-YYYYY"
        result = build_all_codes("IS", "215", unique_raw, sep)
        result["issuer_number"] = issuer_number
        return result

    finally:
        session.close()


def generate_is_reserved_code(kind: str) -> dict:
    """システム予約済みTSV-ISコードを返す（生成ではなく定数返却）。

    Args:
        kind: "system"（システム発行者）または "default"（デフォルト発行者）

    Returns:
        build_all_codes() と同じ辞書
    """
    if kind == "system":
        unique_raw = "000100000"  # "0001" + "00000"
    elif kind == "default":
        unique_raw = "000100001"  # "0001" + "00001"
    else:
        raise ValueError(f"kind は 'system' または 'default' でなければなりません: {kind!r}")

    sep = [4, 5]  # "0001-00000" or "0001-00001"
    result = build_all_codes("IS", "215", unique_raw, sep)
    result["issuer_number"] = unique_raw[4:]
    return result


# ══════════════════════════════════════════════════════════════
#  § 2.2.5  TSV-SH  書架
# ══════════════════════════════════════════════════════════════

def generate_sh_code(
    parent_shelf_tsv_code: Optional[str] = None,
    shelf_number: Optional[str] = None,
) -> dict:
    """TSV-SH（書架）のTSVコードを生成する。

    parent_shelf_tsv_code を指定した場合:
        → 設置列番号の割り当てを受ける書架オブジェクトの特例を適用。
        　 親書架の書架番号を引き継ぎ、設置列番号を 01〜99 で採番。
    指定しない場合:
        → 通常書架。書架番号は shelf_number または自動採番。設置列番号は 00。

    Args:
        parent_shelf_tsv_code: 既存の親書架のTSVコード（特例適用時に指定）
        shelf_number:          7桁の書架番号文字列（省略時は自動採番）

    Returns:
        build_all_codes() と同じ辞書 + "shelf_number", "column_number" キー
    """
    session = database.SessionLocal()
    try:
        if parent_shelf_tsv_code is not None:
            # ─── 設置列番号の割り当てを受ける特例 ───
            parent = session.query(Shelf).get(parent_shelf_tsv_code)
            if parent is None:
                raise ValueError(f"親書架が見つかりません: {parent_shelf_tsv_code!r}")

            # 親書架番号を抽出
            m = re.match(r"TSV-SH-220-(\d{7})-(\d{2})-\d", parent_shelf_tsv_code)
            if m is None:
                raise ValueError(
                    f"親書架TSVコードのフォーマットが不正です: {parent_shelf_tsv_code!r}"
                )
            parent_shelf_num = m.group(1)

            # 同じ書架番号を持つ子書架の設置列番号を列挙
            prefix = f"TSV-SH-220-{parent_shelf_num}-"
            sibling_shelves = session.query(Shelf).filter(
                Shelf.tsv_code.like(prefix + "%")
            ).all()
            used_cols: set[int] = set()
            for s in sibling_shelves:
                m2 = re.match(r"TSV-SH-220-\d{7}-(\d{2})-\d", s.tsv_code)
                if m2:
                    used_cols.add(int(m2.group(1)))

            # 01〜99 で最小未使用
            col_number: Optional[int] = None
            for c in range(1, 100):
                if c not in used_cols:
                    col_number = c
                    break
            if col_number is None:
                raise RuntimeError(
                    f"書架 {parent_shelf_num} の設置列番号が枯渇しました（01〜99）。"
                )

            col_str        = f"{col_number:02d}"
            unique_raw     = parent_shelf_num + col_str  # 9桁
            sep            = [7, 2]
            result         = build_all_codes("SH", "220", unique_raw, sep)
            result["shelf_number"]  = parent_shelf_num
            result["column_number"] = col_str
            return result

        else:
            # ─── 通常書架（設置列番号 = 00）───
            # システム予約: 書架番号 0000000 は予約済み
            existing_shelves = session.query(Shelf).filter(
                Shelf.tsv_code.like("TSV-SH-220-%")
            ).all()
            used_shelf_numbers: set[str] = set()
            for s in existing_shelves:
                m = re.match(r"TSV-SH-220-(\d{7})-\d{2}-\d", s.tsv_code)
                if m:
                    used_shelf_numbers.add(m.group(1))

            if shelf_number is not None:
                if not re.fullmatch(r"\d{7}", shelf_number):
                    raise ValueError(f"書架番号は7桁の数字でなければなりません: {shelf_number!r}")
                if shelf_number == "0000000":
                    raise ValueError("書架番号 0000000 はシステム予約番号です。")
                sn = shelf_number
            else:
                sn = None
                for n in range(1, 10_000_000):
                    candidate = f"{n:07d}"
                    if candidate not in used_shelf_numbers:
                        sn = candidate
                        break
                if sn is None:
                    raise RuntimeError("TSV-SH の書架番号が枯渇しました。")

            col_str    = "00"
            unique_raw = sn + col_str  # 9桁
            sep        = [7, 2]
            result     = build_all_codes("SH", "220", unique_raw, sep)
            result["shelf_number"]  = sn
            result["column_number"] = col_str
            return result

    finally:
        session.close()


def generate_sh_reserved_code(kind: str) -> dict:
    """システム予約済みTSV-SHコードを返す。

    Args:
        kind: "system_data"（システムデータ書架）または "default"（デフォルト書架）

    Returns:
        build_all_codes() と同じ辞書
    """
    if kind == "system_data":
        col = "00"
    elif kind == "default":
        col = "01"
    else:
        raise ValueError(f"kind は 'system_data' または 'default' でなければなりません: {kind!r}")

    unique_raw = "0000000" + col  # 9桁
    sep = [7, 2]
    result = build_all_codes("SH", "220", unique_raw, sep)
    result["shelf_number"]  = "0000000"
    result["column_number"] = col
    return result


# ══════════════════════════════════════════════════════════════
#  TSVコード検証
# ══════════════════════════════════════════════════════════════

def validate_tsv_code(tsv_code: str) -> tuple[bool, str]:
    """TSVコードの絶対要件（§3.1）を検証する。

    Returns:
        (is_valid: bool, message: str)
    """
    # 要件1: 完全記法
    # 要件4: 上位4桁が "TSV-"
    if not tsv_code.startswith("TSV-"):
        return False, "先頭が 'TSV-' でありません。"

    # 要件5: 区分記号・区分コードの整合性
    VALID_SYMBOLS = {"BK", "BG", "RE", "IS", "SH"}
    VALID_CLASS_CODES = {
        "BK": {"200", "201", "202"},
        "BG": {"205"},
        "RE": {"210"},
        "IS": {"215"},
        "SH": {"220"},
    }

    parts = tsv_code.split("-")
    if len(parts) < 4:
        return False, "ハイフン区切りが不足しています。"

    symbol     = parts[1]
    class_code = parts[2]

    if symbol not in VALID_SYMBOLS:
        return False, f"不正なオブジェクト区分記号: {symbol!r}"
    if class_code not in VALID_CLASS_CODES[symbol]:
        return False, f"不正なオブジェクト区分コード: {class_code!r}（{symbol} には {VALID_CLASS_CODES[symbol]} が有効）"

    # 要件6: "2"以降の数字列が13桁、末尾1桁がチェック数字として有効
    # TSVコードから純数字列を抽出（ハイフンを除去し、区分コード以降）
    # TSV-[TT]-[2SS]-...-C の [2SS] 以降のハイフンなし数字列を取得
    numeric_part = "".join(c for c in tsv_code[4 + len(symbol) + 1:] if c.isdigit())
    if len(numeric_part) != 13:
        return False, f"区分コード以降の数字列が13桁ではありません（実際: {len(numeric_part)}桁）。"

    validation_code = numeric_part[:12]
    check_digit     = int(numeric_part[12])
    if not verify_check_digit(validation_code, check_digit):
        expected = calc_check_digit(validation_code)
        return False, f"チェック数字が不正です（期待値: {expected}、実際: {check_digit}）。"

    return True, "OK"


# ══════════════════════════════════════════════════════════════
#  S-TSVコード検証
# ══════════════════════════════════════════════════════════════

def validate_s_tsv_code(s_tsv_code: str) -> tuple[bool, str]:
    """S-TSVコードの絶対要件（§3.3）を検証する。"""
    # 要件1: 英数字を含まない13桁の数字列
    if not re.fullmatch(r"\d{13}", s_tsv_code):
        return False, f"S-TSVコードは13桁の純数字列でなければなりません: {s_tsv_code!r}"

    validation_code = s_tsv_code[:12]
    check_digit     = int(s_tsv_code[12])

    # 要件4: 下位1桁がチェック数字として有効
    if not verify_check_digit(validation_code, check_digit):
        expected = calc_check_digit(validation_code)
        return False, f"チェック数字が不正です（期待値: {expected}、実際: {check_digit}）。"

    return True, "OK"


# ══════════════════════════════════════════════════════════════
#  公開API サマリ
# ══════════════════════════════════════════════════════════════

__all__ = [
    # チェック数字
    "calc_check_digit",
    "verify_check_digit",
    # コード生成
    "generate_bk_code",
    "generate_bg_code",
    "generate_re_code",
    "generate_is_code",
    "generate_is_reserved_code",
    "generate_sh_code",
    "generate_sh_reserved_code",
    # ユーティリティ
    "build_all_codes",
    # 検証
    "validate_tsv_code",
    "validate_s_tsv_code",
]
