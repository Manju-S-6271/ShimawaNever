"""./coapps/BookApps/ISBN.py
ISBNから書籍情報を取得するモジュール
"""

from models import Book
from coapps import settings

def design_isbn(book: Book) -> Book:
    """
    数字のみのISBN-13を、公式のRange Message XMLに基づいてハイフン区切りにする。
    """
    # 1. XMLパースの変数化
    root = settings.get_isbn_range_table()

    # 2. ISBNの正規化 (ハイフン除去など)
    isbn = str(book.isbn).replace("-", "").strip()
    if len(isbn) != 13:
        return "Invalid ISBN length"

    # --- ステップ1: 登録グループ(Registration Group)の特定 ---
    ean = isbn[:3]
    rest_after_ean = isbn[3:]
    group_len = 0
    
    # EAN.UCCPrefixes セクションを探索
    for ucc in root.findall(".//EAN.UCC"):
        if ucc.find("Prefix").text == ean:
            for rule in ucc.findall("./Rules/Rule"): # パスを正確に指定
                r_range = rule.find("Range").text.split("-")
                length = int(rule.find("Length").text)
                target = int(rest_after_ean[:7])
                if int(r_range[0]) <= target <= int(r_range[1]):
                    group_len = length
                    break
    
    if group_len == 0: return "Group not found"
    
    group_id = rest_after_ean[:group_len]
    full_group_prefix = f"{ean}-{group_id}"
    
    # --- ステップ2: 出版社記号(Registrant)の特定 ---
    rest_after_group = rest_after_ean[group_len:]
    registrant_len = 0
    
    # RegistrationGroups セクションを探索
    for group in root.findall(".//Group"):
        if group.find("Prefix").text == full_group_prefix:
            for rule in group.findall("./Rules/Rule"):
                r_range = rule.find("Range").text.split("-")
                length = int(rule.find("Length").text)
                # 書名記号部分を7桁で判定
                target_str = (rest_after_group[:7]).ljust(7, '0')
                target = int(target_str)
                if int(r_range[0]) <= target <= int(r_range[1]):
                    registrant_len = length
                    break
    
    # --- ステップ3: 組み立て ---
    registrant = rest_after_group[:registrant_len]
    # 残りからチェックデジット(1桁)を除いたものが書名記号(item)
    item = rest_after_group[registrant_len:-1]
    check_digit = isbn[-1]
    
    designed_isbn = f"{ean}-{group_id}-{registrant}-{item}-{check_digit}"

    book.isbn = designed_isbn

    return book