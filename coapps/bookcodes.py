"""./coapps/bookcodes.py
ISBNコード及び書籍JANコードから書籍情報を取得するモジュール
"""

import requests
import json
from datetime import datetime, timezone
import yaml
from google import genai
import coapps.checkdigits as checkdigits
import xml.etree.ElementTree as ET
from coapps.scan import scan_multiple_barcodes_stable

class Book:
    def __init__(self, isbn, jan_code=None):
        # 引数で指定されたISBNコードと書籍JANコードを属性にセット
        self.isbn = isbn
        self.jan_code = jan_code

        # ISBNコードから取得する書籍情報の属性を初期化
        self.title = None
        self.volume = None
        self.series = None
        self.publisher = None
        self.pubdate = None
        self.cover = None
        self.author = None
        self.description = None

        # 書籍JANコードから取得する書籍情報の属性を初期化
        self.c_code = None
        self.price = None

        # 書籍JANコード内のCコードから解析される属性を初期化
        self.c_code_target = None
        self.c_code_form = None
        self.c_code_content = None

        # 情報の取得状態を示す属性を初期化
        self.is_openbd_fetched = False
        self.is_google_books_fetched = False
        self.is_ai_generated = False
        self.is_fetched = False

        # ISBNコードと書籍JANコードの有効性を示す属性を初期化
        self.is_isbn_valid = None
        self.is_jan_code_valid = None

        # 設定ファイルからAI生成とGoogle Cloud APIに関する設定を読み込む
        with open("./settings.yml", "r") as f:
            settings = yaml.safe_load(f)
            self._gemini_api_key = settings["ai_generation"]["google_gemini_api_key"]
            self._gemini_model = settings["ai_generation"]["google_gemini_model"]
            isbn_range_table_path = settings["book_info_entry"]["isbn_range_table_path"]
            self._google_cloud_api_key = settings["book_info_entry"]["google_cloud_api_key"]

        if isbn_range_table_path:
            self._isbn_range_table = ET.parse(isbn_range_table_path).getroot()

    def fetch_by_isbn(self):
        """ISBNコードを元にAPIから書籍情報を取得し、属性を更新する"""
        data = self._fetch_book_data()

        self.title = data.get("title")
        self.volume = data.get("volume")
        self.series = data.get("series")
        self.publisher = data.get("publisher")
        self.pubdate = data.get("pubdate")
        self.cover = data.get("cover")
        self.author = data.get("author")
        self.description = data.get("description")
        self.is_openbd_fetched = data.get("is_openbd_fetched", False)
        self.is_google_books_fetched = data.get("is_google_books_fetched", False)
        self.is_ai_generated = data.get("is_ai_generated", False)
        self.is_fetched = True

    def _fetch_book_data(self):
        """OpenBD及びGoogle Books APIからISBNに対応する書籍データを取得して返す"""
        openbd_url = f"https://api.openbd.jp/v1/get?isbn={self.isbn}"
        google_books_url = f"https://www.googleapis.com/books/v1/volumes?q=isbn:{self.isbn}&key={self._google_cloud_api_key}"

        summary = {
            "isbn": self.isbn,
            "jan_code": self.jan_code,
            "is_isbn_valid": self.is_isbn_valid,
            "is_jan_code_valid": self.is_jan_code_valid,
            "title": None,
            "volume": None,
            "series": None,
            "publisher": None,
            "pubdate": None,
            "cover": None,
            "author": None,
            "description": None,
            "is_openbd_fetched": False,
            "is_google_books_fetched": False,
            "is_ai_generated": False,
        }

        # OpenBD APIから基本書籍情報（summaryフィールド）を取得
        openbd_response = requests.get(openbd_url)
        if openbd_response.status_code == 200:
            openbd_data = openbd_response.json()
            if openbd_data and isinstance(openbd_data, list) and len(openbd_data) > 0 and openbd_data[0] is not None:
                openbd_summary = openbd_data[0].get("summary", {})
                summary["title"] = openbd_summary.get("title")
                summary["volume"] = openbd_summary.get("volume")
                summary["series"] = openbd_summary.get("series")
                summary["publisher"] = openbd_summary.get("publisher")
                summary["pubdate"] = openbd_summary.get("pubdate")
                summary["cover"] = openbd_summary.get("cover")
                summary["author"] = openbd_summary.get("author")
                summary["is_openbd_fetched"] = True

        # Google Books APIから追加書籍情報（説明文生成用）を取得
        google_books_data = None
        google_books_response = requests.get(google_books_url)
        if google_books_response.status_code == 200:
            google_books_data = google_books_response.json()
            if google_books_data and "items" in google_books_data and len(google_books_data["items"]) > 0:
                summary["is_google_books_fetched"] = True

        # Gemini APIを用いて説明文を生成
        summary["description"], summary["is_ai_generated"] = self._generate_description(
            summary,
            google_books_data if summary["is_google_books_fetched"] else None
        )

        return summary

    def _generate_description(self, summary, google_books_data):
        """Google Gemini APIを使用して書籍の説明文を生成して返す"""
        gemini_client = genai.Client(api_key=self._gemini_api_key)

        system_prompt = f"""複数の情報源に基づいて書籍に係る説明文を抽出・生成する優秀なアシスタントとして、与えられたJSONデータから説明文（description）を特定し、整形して出力せよ。
但し、次の条件を厳守すること。
1. 次に掲げる場合は、「書籍の説明を取得できませんでした。」と返答すること。
    - Google Books APIからの情報が取得できない場合（is_google_books_fetchedがFalseの場合）
    - Google Books APIからの情報が取得できている場合でも、descriptionフィールドが存在しない場合
    - Google Books APIからの情報が取得できている場合でも、descriptionフィールドの内容が不十分な場合（例: 単なる書籍タイトルの繰り返し。）
2. OpenBD及びGoogle Books APIの両方からの情報が取得できない場合（is_openbd_fetched及びis_google_books_fetchedの両方がFalseの場合）は、「情報が取得できませんでした。」と返答すること。
3. それ以外の場合は、Google Books APIからの情報を優先して説明文を抽出すること。Google Books APIからの情報が取得できない場合はOpenBDからの情報を用いて説明文を生成すること。
4. descriptionフィールドの内容がフレーバーテキストや宣伝文のような内容であっても、説明文として出力すること。
5. descriptionフィールド以外の内容を出力しないこと。また、descriptionフィールドの内容を要約したり、独自の文章を生成したりせず、descriptionフィールドの内容をそのまま出力すること。
6. 出力する説明文は、前後の空白を除去した上で、改行やスペースなどの余分な空白を適切に整形して出力すること。
7. 出力する説明文は、JSON形式などの構造化された形式ではなく、純粋なテキスト形式で出力すること。
"""
        prompt = f"""以下は、ISBNコード {self.isbn} と書籍JANコード {self.jan_code} に関する書籍情報の概要と、各情報源からの詳細な情報を示すJSONデータである。これらの情報に基づいて、書籍の説明文を抽出・生成せよ。

OpenBD情報・取得状態:
{json.dumps(summary, indent=2, ensure_ascii=False)}

Google Books API情報:
{json.dumps(google_books_data, indent=2, ensure_ascii=False)}"""


        try:
            response = gemini_client.models.generate_content(
                model=self._gemini_model,
                config=genai.types.GenerateContentConfig(system_instruction=system_prompt),
                contents=[prompt]
            )
            if response and response.text:
                return response.text.strip(), True
            else:
                return "説明文を取得できませんでした。", False

        except Exception as e:
            return f"エラーが発生しました: {str(e)}", False

    def fetch_by_jan_code(self):
        """書籍JANコードからCコードと販売額を抽出して属性に設定する。
        
        書籍JANコードの構成: "192" + Cコード（4桁） + 販売額（5桁, 10万円以上の場合は00000） + チェック数字（1桁）
        （例）1920979008007 → Cコード: 0979、販売額: 00800（→c_code: C0979、price: 800）
        （例）1920000000005 → Cコード: 0000、販売額: 00000（→c_code: C0000、price: None）

        """
        if self.jan_code and len(self.jan_code) == 13 and self.jan_code.startswith("192"):
            c_code_part = self.jan_code[3:7]  # Cコード部分（4桁）
            price_part = self.jan_code[7:12]    # 販売額部分（5桁）

            if c_code_part.isdigit() and price_part.isdigit():
                self.c_code = f"C{c_code_part}"
                self.price = int(price_part) if price_part != "00000" else None
            else:
                raise ValueError("無効な書籍JANコードです。Cコードと販売額は数字で構成されている必要があります。")
        else:
            raise ValueError("無効な書籍JANコードです。正しい形式のコードを指定してください。")
        
    def align_isbn(self, only_export=False):
        """ISBNコードをハイフンなしの形式に変換して返す関数"""
        if self.isbn:
            aligned_isbn = self.isbn.replace("-", "")
            if not only_export:
                self.isbn = aligned_isbn
            
            return aligned_isbn
        return None
    
    def design_isbn(self, only_export=False):
        """
        数字のみのISBN-13を、公式のRange Message XMLに基づいてハイフン区切りにする。
        """
        # 1. XMLパースの変数化
        root = self._isbn_range_table

        # 2. ISBNの正規化 (ハイフン除去など)
        isbn = str(self.isbn).replace("-", "").strip()
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

        if not only_export:
            self.isbn = designed_isbn

        return designed_isbn
    
    def verify_isbn(self):
        """ISBNコード（ISBN-13のみ）の有効性を検証する関数"""
        aligned = self.align_isbn(only_export=True)

        is_valid = (
            aligned and len(aligned) == 13 and aligned.isdigit() and
            aligned.startswith(("978", "979")) and
            checkdigits.verify(int(aligned[:12]), int(aligned[-1]), modulus=10, weight=3)
        )

        self.is_isbn_valid = is_valid
        return is_valid

    def verify_jan_code(self):
        """書籍JANコードの有効性を検証する関数"""
        code = self.jan_code

        is_valid = (
            code and len(code) == 13 and code.isdigit() and
            code.startswith("192") and
            checkdigits.verify(int(code[:12]), int(code[-1]), modulus=10, weight=3)
        )

        self.is_jan_code_valid = is_valid
        return is_valid
    
    def parse_c_code(self):
        """Cコードから対象、形態、内容の分類を解析して属性にセットする関数
        """
        c_code = self.c_code

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

        self.c_code_target = target
        self.c_code_form = form
        self.c_code_content = content

    def __str__(self):
        """Bookオブジェクトの文字列表現を定義する関数, APIキー以外の全ての属性を表示する"""
        # 現在のself.__dict__をjson.dumpsで整形して返す
        return json.dumps({k: v for k, v in self.__dict__.items() if not k.startswith("_")}, indent=2, ensure_ascii=False)
        

# 動作確認用エントリーポイント
def entry_book_info():
    # ISBNコードと書籍JANコードをスキャンしてBookオブジェクトを作成
    scanned_codes = scan_multiple_barcodes_stable(expected_count=2, stability_threshold=10)
    isbn_code = next((code for code in scanned_codes if code.startswith("978")), None)
    jan_code = next((code for code in scanned_codes if code.startswith("192")), None)

    # ISBNコードと書籍JANコードの両方がスキャンできた場合にBookオブジェクトを作成
    if isbn_code and jan_code:
        book = Book(isbn=isbn_code, jan_code=jan_code)
    else:
        print("ISBNコードと書籍JANコードの両方をスキャンできませんでした。")

    # ISBNコードと書籍JANコードの有効性を検証
    book.verify_isbn()
    book.verify_jan_code()

    # 書籍情報をAPIから取得して属性にセット
    book.fetch_by_isbn()
    book.fetch_by_jan_code()

    # Cコードから対象、形態、内容の分類を解析して属性にセット
    book.parse_c_code()

    # ISBNコードをハイフン付きの形式に変換して属性にセット
    book.design_isbn()

    # 取得した書籍情報を表示
    print(f"ISBNコード {book.isbn} 書籍JANコード {book.jan_code} に関する書籍は、次の通りです。")
    print()
    print(f"タイトル: {book.title}")
    print()
    print(f"出版社: {book.publisher}")
    print(f"説明文: {book.description}")
    print()
    print(f"Cコード: {book.c_code}")
    print(f"（対象: {book.c_code_target}）")
    print(f"（形態: {book.c_code_form}）")
    print(f"（内容: {book.c_code_content}）")
    print()
    print(f"価格: {book.price}")
    print(f"その他の情報: {book}")