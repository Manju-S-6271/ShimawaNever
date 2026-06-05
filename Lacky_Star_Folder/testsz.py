from coapps.bookcodes import Book
from Lacky_Star_Folder.scan import scan_multiple_barcodes_stable

def get_perfect_book_info(isbn, jan):
    # ① インスタンス化
    # ハイフンの有無はクラス内の align_isbn で処理されるため、どちらでも OK
    my_book = Book(isbn=isbn, jan_code=jan)

    print(f"--- 処理開始: {isbn} ---")

    # ② 有効性のチェック (バリデーション)
    # 不正なコードで API を叩く無駄を省きます
    if not my_book.verify_isbn():
        print("エラー: ISBNコードが正しくありません。")
        return None
    
    if not my_book.verify_jan_code():
        print("エラー: 書籍JANコード(2段目)が正しくありません。")
        return None

    # ③ データの同期 (フェッチ)
    try:
        # ISBNからタイトル、著者、AIによる説明文を取得
        my_book.fetch_by_isbn()
        
        # JANコードからCコード（分類）と価格を抽出
        my_book.fetch_by_jan_code()

        # ISBNとJAN両方の情報を統合して、Cコードからさらに詳細な分類情報を解析
        if my_book.c_code:
            my_book.parse_c_code()
        
        # ④ 結果の確認
        if my_book.is_fetched:
            print(f"成功！『{my_book.title}』の情報を取得しました。")
            return my_book
        else:
            print("警告: コードは正しいですが、APIから情報が見つかりませんでした。")
            return my_book

    except Exception as e:
        print(f"実行中にエラーが発生しました: {e}")
        return None

# --- テストコード ---
if __name__ == "__main__":
    # スキャンして2つのコードを取得
    scanned_codes = scan_multiple_barcodes_stable(expected_count=2, stability_threshold=10)

    # 頭文字が "978" の方を ISBN、"192" の方を JAN として識別
    isbn_code = next((code for code in scanned_codes if code.startswith("978")), None)
    jan_code = next((code for code in scanned_codes if code.startswith("192")), None)

    if isbn_code and jan_code:
        book_info = get_perfect_book_info(isbn_code, jan_code)
        book_info.design_isbn()
        if book_info:
            print(f"ISBNコード {book_info.isbn} 書籍JANコード {book_info.jan_code} に関する書籍は、次の通りです。")
            print()
            print(f"タイトル: {book_info.title}")
            print()
            print(f"出版社: {book_info.publisher}")
            print(f"説明文: {book_info.description}")
            print()
            print(f"Cコード: {book_info.c_code}")
            print(f"（対象: {book_info.c_code_target}）")
            print(f"（形態: {book_info.c_code_form}）")
            print(f"（内容: {book_info.c_code_content}）")
            print()
            print(f"価格: {book_info.price}")
            print(f"その他の情報: {book_info}")
            