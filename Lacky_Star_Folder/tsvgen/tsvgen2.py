from dataclasses import dataclass

# =========================
# チェック数字計算
# =========================
def calc_check_digit(validation_code: str) -> int:
    """
    モジュール10 ウェイト3 によるチェック数字算出
    """
    if len(validation_code) != 12 or not validation_code.isdigit():
        raise ValueError("S-TSV検証コードは12桁の数字である必要があります")

    odd_sum = 0
    even_sum = 0

    for i, digit in enumerate(validation_code):
        d = int(digit)
        if (i + 1) % 2 == 1:
            odd_sum += d
        else:
            even_sum += d

    total = odd_sum + even_sum * 3
    remainder = total % 10

    return 0 if remainder == 0 else (10 - remainder)


# =========================
# 共通生成ロジック
# =========================
def generate_codes(tt: str, ss: str, unique_number: str, formatted_unique: str):
    """
    TSV / S-TSV / 検証コードを一括生成
    """
    validation_code = ss + unique_number
    check_digit = calc_check_digit(validation_code)

    tsv_code = f"TSV-{tt}-{ss}-{formatted_unique}-{check_digit}"
    s_tsv_code = validation_code + str(check_digit)

    return {
        "TSV": tsv_code,
        "S-TSV": s_tsv_code,
        "Validation": validation_code,
        "CheckDigit": check_digit
    }


# =========================
# BK（書籍）
# =========================
def generate_bk_general(unique_number: int):
    """
    一般書籍（202）
    """
    ss = "202"
    tt = "BK"
    num = f"{unique_number:09d}"
    formatted = f"{num[0:3]}-{num[3:6]}-{num[6:9]}"
    return generate_codes(tt, ss, num, formatted)


def generate_bk_isbn13(isbn13: str):
    """
    ISBN13特例（200）
    """
    if len(isbn13) != 13 or not isbn13.isdigit():
        raise ValueError("ISBN13は13桁の数字")

    ss = "200"
    tt = "BK"
    num = isbn13[3:12]  # 4桁目〜12桁目
    formatted = f"{num[0]}-{num[1:3]}-{num[3:]}"
    return generate_codes(tt, ss, num, formatted)


def generate_bk_isbn10(isbn10: str):
    """
    ISBN10特例（201）
    """
    if len(isbn10) != 10 or not isbn10[:9].isdigit():
        raise ValueError("ISBN10は10桁（最後はX可）")

    ss = "201"
    tt = "BK"
    num = isbn10[:9]
    formatted = f"{num[0]}-{num[1:5]}-{num[5:]}"
    return generate_codes(tt, ss, num, formatted)


# =========================
# BG（書籍グループ）
# =========================
def generate_bg(unique_number: int):
    ss = "205"
    tt = "BG"
    num = f"{unique_number:09d}"
    formatted = f"{num[0:3]}-{num[3:6]}-{num[6:9]}"
    return generate_codes(tt, ss, num, formatted)


# =========================
# IS（発行者）
# =========================
def generate_is(publisher_number: int):
    ss = "215"
    tt = "IS"
    pub = f"{publisher_number:05d}"
    num = "0000" + pub
    formatted = f"0000-{pub}"
    return generate_codes(tt, ss, num, formatted)


def generate_is_reserved(system=True):
    ss = "215"
    tt = "IS"

    if system:
        num = "000100000"
    else:
        num = "000100001"

    formatted = f"{num[:4]}-{num[4:]}"
    return generate_codes(tt, ss, num, formatted)


# =========================
# RE（資料）
# =========================
def generate_re(publisher_number: int, doc_number: int):
    ss = "210"
    tt = "RE"

    pub = f"{publisher_number:05d}"
    doc = f"{doc_number:04d}"

    num = pub + doc
    formatted = f"{pub}-{doc}"

    return generate_codes(tt, ss, num, formatted)


# =========================
# SH（書架）
# =========================
def generate_sh(shelf_number: int, column_number: int = 0):
    ss = "220"
    tt = "SH"

    shelf = f"{shelf_number:07d}"
    col = f"{column_number:02d}"

    num = shelf + col
    formatted = f"{shelf}-{col}"

    return generate_codes(tt, ss, num, formatted)


# =========================
# 使用例
# =========================
if __name__ == "__main__":
    print(generate_bk_general(123))
    print(generate_bk_isbn13("9784012345678"))
    print(generate_bg(1))
    print(generate_is(2))
    print(generate_re(1, 1))
    print(generate_sh(1, 0))