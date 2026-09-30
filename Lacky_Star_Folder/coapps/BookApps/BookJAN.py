"""./coapps/BookApps/BookJAN.py
書籍JANコードから書籍情報を取得するモジュール
"""

from models import Book

def _fetch_jan_code(book: Book) -> Book:
    if book.book_jan and len(book.book_jan) == 13 and book.book_jan.startswith("192"):
        c_code_part = book.book_jan[3:7]  # Cコード部分（4桁）
        price_part = book.book_jan[7:12]    # 販売額部分（5桁）

        if c_code_part.isdigit() and price_part.isdigit():
            book.c_code = f"C{c_code_part}"
            book.price = int(price_part) if price_part != "00000" else None
        else:
            raise ValueError("無効な書籍JANコードです。Cコードと販売額は数字で構成されている必要があります。")
    else:
        raise ValueError("無効な書籍JANコードです。正しい形式のコードを指定してください。")
    
    return book

def _parse_c_code(book: Book) -> Book:
    """Cコードから対象、形態、内容の分類を解析して属性にセットする関数
    """
    c_code = book.c_code

    if c_code.startswith("C"):
        c_code = c_code[1:]

    if len(c_code) != 4 or not c_code.isdigit():
        raise ValueError("CコードはCから始まる5桁のコードまたは4桁の数字である必要があります")

    target_map = {
        "0": "一般",
        "1": "教養",
        "2": "実用",
        "3": "専門",
        "4": "検定教科書・非課税品等",
        "5": "婦人",
        "6": "学参I（小中）",
        "7": "学参II（高校）",
        "8": "児童",
        "9": "雑誌扱い",
    }

    form_map = {
        "0": "単行本",
        "1": "文庫",
        "2": "新書",
        "3": "全集・双書",
        "4": "ムック・その他",
        "5": "事典・辞典",
        "6": "図鑑",
        "7": "絵本",
        "8": "磁性媒体など",
        "9": "コミック",
    }

    content_map = {
        "00": "総記", "01": "百科事典", "02": "年鑑・雑誌", "04": "情報科学",
        "10": "哲学", "11": "心理学", "12": "倫理学", "14": "宗教", "15": "仏教", "16": "キリスト教",
        "20": "歴史総記", "21": "日本歴史", "22": "外国歴史", "23": "伝記", "25": "地理", "26": "旅行",
        "30": "社会科学総記", "31": "政治・軍事", "32": "法律", "33": "経済・統計", "34": "経営",
        "36": "社会", "37": "教育", "39": "民族・風習",
        "40": "自然科学総記", "41": "数学", "42": "物理学", "43": "化学",
        "44": "天文・地学", "45": "生物学", "47": "医学・歯学・薬学",
        "50": "工学総記", "51": "土木", "52": "建築", "53": "機械", "54": "電気",
        "55": "電子通信", "56": "海事", "57": "採鉱・冶金", "58": "その他工業",
        "60": "産業総記", "61": "農林業", "62": "水産業", "63": "商業", "65": "交通・通信",
        "70": "芸術総記", "71": "絵画・彫刻", "72": "写真・工芸", "73": "音楽・舞踊",
        "74": "演劇・映画", "75": "体育・スポーツ", "76": "娯楽", "77": "家事",
        "78": "日記・手帳", "79": "コミックス・劇画",
        "80": "語学総記", "81": "日本語", "82": "英語", "84": "ドイツ語", "85": "フランス語", "87": "各国語",
        "90": "文学総記", "91": "日本文学総記", "92": "日本文学詩歌",
        "93": "日本文学（小説・物語）", "95": "日本文学（評論・随筆）",
        "97": "外国文学小説", "98": "外国文学その他",
    }

    target = target_map.get(c_code[0], "不明")
    form = form_map.get(c_code[1], "不明")
    content = content_map.get(c_code[2:4], "不明")

    book.target = target
    book.form = form
    book.content = content

    return book

def fetch_data(book: Book) -> Book:
    book = _fetch_jan_code(book)
    book = _parse_c_code(book)
    return book