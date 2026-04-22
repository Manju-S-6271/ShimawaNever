"""./crud.py
データベースの基本的な登録・更新・削除・検索の操作を行うアプリケーション
"""

from coapps.bookcodes import Book, fetch_all, entry_book_info
from coapps.scan import scan_multiple_barcodes_stable
from coapps.checkdigits import calculate, verify
from testsz import get_perfect_book_info
from models import Book as BookModel
import database
import inquirer
from BookRecorder.main import main as run_book_recorder
from BookDataQuerier.main import main as run_book_querier


if __name__ == "__main__":
    print("==== ShimawaNever Database CRUD Application ====")
    print("Hello!")
    print("ShimawaNever データベース CRUD アプリケーションへようこそ！")

    operation = inquirer.prompt([inquirer.List("operation", message="実施する操作を選択してください:", choices=["Create", "Read", "Update", "Delete", "Open CoApps...", "Exit"])])["operation"]

    if operation in [ "Read", "Update", "Delete"]:
        print(f"申し訳ありませんが、{operation} 操作は現在開発中です。")
    elif operation == "Create":
        object_type = inquirer.prompt([inquirer.List("object_type", message="作成するオブジェクトの種類を選択してください:", choices=["Book with ISBN scanner"])])["object_type"]

        if object_type == "Book with ISBN scanner":
            # while True:
            #     isbn_code = inquirer.prompt([inquirer.Text("isbn_code", message="ISBNコードをスキャンしてください [登録を終える場合はEnterを押してください]:")])["isbn_code"]
            #     jan_code = inquirer.prompt([inquirer.Text("jan_code", message="書籍JANコードをスキャンしてください [JANコードのない書籍は登録できません]:")])["jan_code"]

            #     if isbn_code and jan_code:
            #         book_info = fetch_all(isbn_code, jan_code)
            #         book_info.design_isbn()

            #         stsv_code = int(f"200{book_info.align_isbn(only_export=True)[4:-1]}")
                    
            #         check_digit = calculate(stsv_code, modulus=10, weight=3)
                    
            #         stsv_code = f"200{book_info.align_isbn(only_export=True)[4:-1]}{check_digit}"

            #         tsv_code = f"TSV-BK-200-{book_info.isbn[6:-2]}-{check_digit}"

            #         book = BookModel(
            #             tsv_code=tsv_code,
            #             title=book_info.title,
            #             authors=book_info.author,
            #             publisher=book_info.publisher,
            #             published_date=book_info.pubdate,
            #             description=book_info.description,
            #             isbn=book_info.isbn,
            #             book_jan=book_info.jan_code,
            #             c_code=book_info.c_code,
            #             target=book_info.c_code_target,
            #             form=book_info.c_code_form,
            #             content=book_info.c_code_content,
            #             price=book_info.price,
            #             shelf_tsv_code="TSV-SH-0001-00001-0",
            #         )
            #         with database.SessionLocal() as session:
            #             session.add(book)
            #             session.commit()

            #         print(f"ISBNコード {book_info.isbn} 書籍JANコード {book_info.jan_code} に関する次の書籍は、TSVコード {tsv_code} としてデータベースに保存されました。")
            #         print()
            #         print(f"タイトル: {book_info.title}")
            #         print(f"著者: {book_info.author}")
            #         print(f"出版社: {book_info.publisher}")
            #         print(f"ISBNコード: {book_info.isbn}")
            #         print(f"書籍JANコード: {book_info.jan_code}")
            #         print(f"Cコード: {book_info.c_code}")
            #         print(f"価格: {book_info.price}円")
            #     else:
            #         print("ISBNコードと書籍JANコードの両方が必要です。登録を終了します。")
            #         break
            print("Book with ISBN scanner の作成は現在開発中です。")
                    
                    
    elif operation == "Open CoApps...":
        coapps = inquirer.prompt([inquirer.List("coapp", message="開くCoAppを選択してください:", choices=["Book Recorder", "Book Data Querier", "DEBUG: Check Book Object", "Book Record Exporter"])])["coapp"]
        if coapps == "Book Recorder":
            print("Book Recorder を開きます...")
            run_book_recorder()
        elif coapps == "Book Data Querier":
            print("Book Data Querier を開きます...")
            run_book_querier()
        elif coapps == "DEBUG: Check Book Object":
            print("Book オブジェクトの動作確認を行います...")
            entry_book_info()
        elif coapps == "Book Record Exporter":
            print("Book Record Exporter を開きます...")
            import BookRecordExporter.main
            