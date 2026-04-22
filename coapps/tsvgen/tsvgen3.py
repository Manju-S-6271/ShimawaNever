"""
TSVコードジェネレータ
ShimawaNever Webアプリケーション向けTSVコード体系定義書に基づく実装

対応コード:
  - TSVコード（完全記法）
  - S-TSV検証コード
  - S-TSVコード
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional


# ---------------------------------------------------------------------------
# 3.4. チェック数字（モジュール10 ウェイト3）
# ---------------------------------------------------------------------------

def calc_check_digit(validation_code: str) -> int:
    """
    S-TSV検証コード（12桁）からチェック数字を算出する。
    モジュール10 ウェイト3（GS1標準と同一）。

    Args:
        validation_code: 12桁の数字文字列

    Returns:
        チェック数字（0〜9）

    Raises:
        ValueError: 検証コードが12桁の数字でない場合
    """
    if len(validation_code) != 12 or not validation_code.isdigit():
        raise ValueError(
            f"S-TSV検証コードは12桁の数字列でなければなりません: '{validation_code}'"
        )

    odd_sum  = sum(int(validation_code[i]) for i in range(0, 12, 2))   # 1,3,5,...桁
    even_sum = sum(int(validation_code[i]) for i in range(1, 12, 2))   # 2,4,6,...桁

    total = odd_sum + even_sum * 3
    remainder = total % 10
    return 0 if remainder == 0 else 10 - remainder


# ---------------------------------------------------------------------------
# 内部ユーティリティ
# ---------------------------------------------------------------------------

def _build_codes(
    type_symbol: str,
    class_code: str,
    unique_number: str,
    hyphen_pattern: list[int],
) -> tuple[str, str, str]:
    """
    TSVコード・S-TSV検証コード・S-TSVコードをまとめて生成する。

    Args:
        type_symbol:    オブジェクト区分記号（例: "BK"）
        class_code:     オブジェクト区分コード（3桁、例: "200"）
        unique_number:  固有番号（9桁の連続数字文字列、例: "401000000"）
        hyphen_pattern: 固有番号内のハイフン挿入位置リスト（累積桁数）
                        例: [1, 3] → "X-XX-XXXXXX"

    Returns:
        (TSVコード, S-TSV検証コード, S-TSVコード)
    """
    if len(class_code) != 3 or not class_code.isdigit():
        raise ValueError(f"オブジェクト区分コードは3桁の数字でなければなりません: '{class_code}'")
    if len(unique_number) != 9 or not unique_number.isdigit():
        raise ValueError(f"固有番号は9桁の数字列でなければなりません: '{unique_number}'")

    # S-TSV検証コード（12桁）
    s_tsv_validation = class_code + unique_number

    # チェック数字
    check = calc_check_digit(s_tsv_validation)

    # S-TSVコード（13桁）
    s_tsv_code = s_tsv_validation + str(check)

    # 固有番号をハイフンで分割
    parts = []
    prev = 0
    for pos in hyphen_pattern:
        parts.append(unique_number[prev:pos])
        prev = pos
    parts.append(unique_number[prev:])
    unique_with_hyphens = "-".join(parts)

    # TSVコード
    tsv_code = f"TSV-{type_symbol}-{class_code}-{unique_with_hyphens}-{check}"

    return tsv_code, s_tsv_validation, s_tsv_code


# ---------------------------------------------------------------------------
# 2.2.1. TSV-BK（書籍）
# ---------------------------------------------------------------------------

def generate_bk_isbn13(isbn13: str) -> tuple[str, str, str]:
    """
    TSV-BK: 13桁ISBNを持つ書籍のTSVコードを生成する（特例 §2.2.1.1）。

    固有番号 = ISBN13の4〜12桁目（0-indexed: [3:12]）
    ハイフン位置 = ISBNのハイフン区切りをそのまま反映

    Args:
        isbn13: ハイフンを含む（または含まない）13桁のISBN文字列
                例: "978-4-01-000000-0" または "9784010000000"

    Returns:
        (TSVコード, S-TSV検証コード, S-TSVコード)

    Raises:
        ValueError: ISBNが不正な形式の場合
    """
    # ハイフンを取り除いた純数字列と、ハイフン位置を取得
    digits_only = isbn13.replace("-", "")
    if len(digits_only) != 13 or not digits_only.isdigit():
        raise ValueError(f"13桁ISBNの形式が不正です: '{isbn13}'")

    # 固有番号 = digits[3:12]（9桁）
    unique_number = digits_only[3:12]

    # ハイフン位置を固有番号内の相対位置に変換
    # ISBN例: 978-4-01-000000-0 → ["978","4","01","000000","0"]
    # 固有番号は全体の4〜12桁目 = groupsの2番目以降（"4","01","000000"）
    if "-" in isbn13:
        groups = isbn13.split("-")
        # グループ長さ（先頭978グループを除く、末尾チェックディジットグループを除く）
        middle_groups = groups[1:-1]  # ["4","01","000000"]
        positions = []
        cur = 0
        for g in middle_groups[:-1]:
            cur += len(g)
            positions.append(cur)
    else:
        # ハイフンなし → 3桁ごと
        positions = [3, 6]

    return _build_codes("BK", "200", unique_number, positions)


def generate_bk_isbn10(isbn10: str) -> tuple[str, str, str]:
    """
    TSV-BK: 10桁ISBNを持つ書籍のTSVコードを生成する（特例 §2.2.1.2）。

    固有番号 = ISBN10の1〜9桁目（0-indexed: [0:9]）
    ハイフン位置 = ISBNのハイフン区切りをそのまま反映

    Args:
        isbn10: ハイフンを含む（または含まない）10桁のISBN文字列
                例: "0-0000-0000-X" または "000000000X"

    Returns:
        (TSVコード, S-TSV検証コード, S-TSVコード)
    """
    digits_only = isbn10.replace("-", "").upper()
    if len(digits_only) != 10:
        raise ValueError(f"10桁ISBNの形式が不正です: '{isbn10}'")
    # 末尾はXの場合あり（チェックディジット）
    if not digits_only[:-1].isdigit():
        raise ValueError(f"10桁ISBNの形式が不正です（数字部分）: '{isbn10}'")

    unique_number = digits_only[:9]
    if not unique_number.isdigit():
        raise ValueError(f"10桁ISBNの固有番号部分が数字でありません: '{isbn10}'")

    if "-" in isbn10:
        groups = isbn10.split("-")
        # 末尾グループ（チェックディジット）を除いた部分
        content_groups = groups[:-1]  # ["0","0000","0000"]
        positions = []
        cur = 0
        for g in content_groups[:-1]:
            cur += len(g)
            positions.append(cur)
    else:
        positions = [1, 5]

    return _build_codes("BK", "201", unique_number, positions)


def generate_bk_no_isbn(unique_number: str) -> tuple[str, str, str]:
    """
    TSV-BK: ISBNなし書籍のTSVコードを生成する（§2.2.1通常）。

    固有番号 = 000000000〜999999999 の任意の9桁数字
    ハイフン = 3桁ごと

    Args:
        unique_number: 9桁の固有番号文字列

    Returns:
        (TSVコード, S-TSV検証コード, S-TSVコード)
    """
    return _build_codes("BK", "202", unique_number, [3, 6])


# ---------------------------------------------------------------------------
# 2.2.2. TSV-BG（書籍グループ）
# ---------------------------------------------------------------------------

def generate_bg(unique_number: str) -> tuple[str, str, str]:
    """
    TSV-BG: 書籍グループのTSVコードを生成する（§2.2.2）。

    Args:
        unique_number: 9桁の固有番号文字列

    Returns:
        (TSVコード, S-TSV検証コード, S-TSVコード)
    """
    return _build_codes("BG", "205", unique_number, [3, 6])


# ---------------------------------------------------------------------------
# 2.2.3. TSV-RE（記録資料等）
# ---------------------------------------------------------------------------

def generate_re(issuer_number: str, doc_number: str) -> tuple[str, str, str]:
    """
    TSV-RE: 記録資料等のTSVコードを生成する（§2.2.3）。

    固有番号 = issuer_number(5桁) + doc_number(4桁)

    Args:
        issuer_number: 発行者番号（5桁、例: "00001"）
        doc_number:    発行者別資料番号（4桁、例: "0001"）

    Returns:
        (TSVコード, S-TSV検証コード, S-TSVコード)
    """
    if len(issuer_number) != 5 or not issuer_number.isdigit():
        raise ValueError(f"発行者番号は5桁の数字でなければなりません: '{issuer_number}'")
    if len(doc_number) != 4 or not doc_number.isdigit():
        raise ValueError(f"発行者別資料番号は4桁の数字でなければなりません: '{doc_number}'")

    unique_number = issuer_number + doc_number
    return _build_codes("RE", "210", unique_number, [5])


# ---------------------------------------------------------------------------
# 2.2.4. TSV-IS（資料発行者）
# ---------------------------------------------------------------------------

def generate_is(issuer_number: str, reserved: bool = False) -> tuple[str, str, str]:
    """
    TSV-IS: 資料発行者のTSVコードを生成する（§2.2.4）。

    通常:   固有番号 = "0000" + issuer_number(5桁)  → ハイフン: "0000-XXXXX"
    予約済み: 固有番号 = "0001" + issuer_number(5桁)  → ハイフン: "0001-XXXXX"
             (システム発行者=00000, デフォルト発行者=00001)

    Args:
        issuer_number: 発行者番号（5桁、例: "00002"）
        reserved:      予約済みオブジェクトの場合True（固有番号前半が"0001"になる）

    Returns:
        (TSVコード, S-TSV検証コード, S-TSVコード)
    """
    if len(issuer_number) != 5 or not issuer_number.isdigit():
        raise ValueError(f"発行者番号は5桁の数字でなければなりません: '{issuer_number}'")

    prefix = "0001" if reserved else "0000"
    unique_number = prefix + issuer_number
    return _build_codes("IS", "215", unique_number, [4])


def generate_is_system() -> tuple[str, str, str]:
    """TSV-IS システム発行者（予約済み §2.2.4.1）"""
    return generate_is("00000", reserved=True)


def generate_is_default() -> tuple[str, str, str]:
    """TSV-IS デフォルト発行者（予約済み §2.2.4.2）"""
    return generate_is("00001", reserved=True)


# ---------------------------------------------------------------------------
# 2.2.5. TSV-SH（書架）
# ---------------------------------------------------------------------------

def generate_sh(shelf_number: str, column_number: str = "00") -> tuple[str, str, str]:
    """
    TSV-SH: 書架のTSVコードを生成する（§2.2.5）。

    固有番号 = shelf_number(7桁) + column_number(2桁)

    Args:
        shelf_number:  書架番号（7桁、例: "0000001"）
        column_number: 設置列番号（2桁、デフォルト"00"）
                       通常書架="00"、設置列特例="01"〜"99"、予約済み="00"

    Returns:
        (TSVコード, S-TSV検証コード, S-TSVコード)
    """
    if len(shelf_number) != 7 or not shelf_number.isdigit():
        raise ValueError(f"書架番号は7桁の数字でなければなりません: '{shelf_number}'")
    if len(column_number) != 2 or not column_number.isdigit():
        raise ValueError(f"設置列番号は2桁の数字でなければなりません: '{column_number}'")

    unique_number = shelf_number + column_number
    return _build_codes("SH", "220", unique_number, [7])


def generate_sh_system() -> tuple[str, str, str]:
    """TSV-SH システムデータ書架（予約済み §2.2.5.2）"""
    return generate_sh("0000000", "00")


def generate_sh_default() -> tuple[str, str, str]:
    """TSV-SH デフォルト書架（予約済み §2.2.5.3）"""
    return generate_sh("0000000", "01")


# ---------------------------------------------------------------------------
# バリデーション
# ---------------------------------------------------------------------------

def validate_tsv_code(tsv_code: str) -> bool:
    """
    TSVコードの絶対要件（§3.1）を検証する。

    Args:
        tsv_code: 検証対象のTSVコード文字列

    Returns:
        True: 有効 / False: 無効
    """
    try:
        if not tsv_code.startswith("TSV-"):
            return False

        # ハイフン区切りで分解（"TSV", type, class_code, *unique_parts, check）
        parts = tsv_code.split("-")
        if len(parts) < 5:
            return False

        type_symbol = parts[1]
        class_code  = parts[2]
        check_str   = parts[-1]
        unique_parts = parts[3:-1]

        valid_types = {"BK": ["200","201","202"], "BG": ["205"],
                       "RE": ["210"], "IS": ["215"], "SH": ["220"]}
        if type_symbol not in valid_types:
            return False
        if class_code not in valid_types[type_symbol]:
            return False

        unique_number = "".join(unique_parts)
        if len(unique_number) != 9 or not unique_number.isdigit():
            return False
        if not check_str.isdigit() or len(check_str) != 1:
            return False

        validation_code = class_code + unique_number
        expected_check = calc_check_digit(validation_code)
        return int(check_str) == expected_check

    except Exception:
        return False


def validate_s_tsv_code(s_tsv_code: str) -> bool:
    """
    S-TSVコードの絶対要件（§3.3）を検証する。

    Args:
        s_tsv_code: 13桁の数字文字列

    Returns:
        True: 有効 / False: 無効
    """
    s_tsv_code = s_tsv_code.replace(" ", "")
    if len(s_tsv_code) != 13 or not s_tsv_code.isdigit():
        return False

    validation_code = s_tsv_code[:12]
    check_str       = s_tsv_code[12]
    expected        = calc_check_digit(validation_code)
    return int(check_str) == expected


# ---------------------------------------------------------------------------
# 結果表示ヘルパー
# ---------------------------------------------------------------------------

def print_codes(label: str, tsv: str, validation: str, s_tsv: str) -> None:
    print(f"  [{label}]")
    print(f"    TSVコード        : {tsv}")
    print(f"    S-TSV検証コード  : {validation}")
    print(f"    S-TSVコード      : {s_tsv}")
    print(f"    検証(TSV)        : {'OK' if validate_tsv_code(tsv) else 'NG'}")
    print(f"    検証(S-TSV)      : {'OK' if validate_s_tsv_code(s_tsv) else 'NG'}")
    print()


# ---------------------------------------------------------------------------
# デモ / メイン
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 60)
    print("TSVコードジェネレータ デモ")
    print("=" * 60)

    # --- TSV-BK ---
    print("\n【TSV-BK 書籍】")

    tsv, val, stv = generate_bk_isbn13("978-4-01-000000-0")
    print_codes("13桁ISBN: 978-4-01-000000-0", tsv, val, stv)

    tsv, val, stv = generate_bk_isbn10("0-0000-0000-X")
    print_codes("10桁ISBN: 0-0000-0000-X", tsv, val, stv)

    tsv, val, stv = generate_bk_no_isbn("000000001")
    print_codes("ISBNなし: 000000001", tsv, val, stv)

    # --- TSV-BG ---
    print("【TSV-BG 書籍グループ】")
    tsv, val, stv = generate_bg("000000001")
    print_codes("書籍グループ: 000000001", tsv, val, stv)

    # --- TSV-RE ---
    print("【TSV-RE 記録資料等】")
    tsv, val, stv = generate_re("00001", "0001")
    print_codes("発行者=00001, 資料番号=0001", tsv, val, stv)

    # --- TSV-IS ---
    print("【TSV-IS 資料発行者】")
    tsv, val, stv = generate_is("00002")
    print_codes("通常発行者: 00002", tsv, val, stv)

    tsv, val, stv = generate_is_system()
    print_codes("予約済み: システム発行者", tsv, val, stv)

    tsv, val, stv = generate_is_default()
    print_codes("予約済み: デフォルト発行者", tsv, val, stv)

    # --- TSV-SH ---
    print("【TSV-SH 書架】")
    tsv, val, stv = generate_sh("0000001", "00")
    print_codes("通常書架: 0000001-00", tsv, val, stv)

    tsv, val, stv = generate_sh("0000001", "01")
    print_codes("設置列特例: 0000001-01", tsv, val, stv)

    tsv, val, stv = generate_sh_system()
    print_codes("予約済み: システムデータ書架", tsv, val, stv)

    tsv, val, stv = generate_sh_default()
    print_codes("予約済み: デフォルト書架", tsv, val, stv)

    # --- バリデーションテスト ---
    print("【バリデーションテスト】")
    invalid = "TSV-BK-202-000-000-000-9"  # チェック数字を故意に改ざん
    print(f"  改ざんコード '{invalid}': {'OK' if validate_tsv_code(invalid) else 'NG (期待通り)'}")