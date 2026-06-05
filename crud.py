"""./crud.py
データベースの基本的な登録・更新・削除・検索の操作を行うアプリケーション
"""

from coapps.bookcodes import Book, fetch_all, entry_book_info
from Lacky_Star_Folder.scan import scan_multiple_barcodes_stable
from coapps.checkdigits import calculate, verify
from coapps.BookApps import BookJAN
from coapps.BookApps import RakutenAPI
from coapps.BookApps import ISBN
from coapps.create import createBookwithScanner
from coapps.tsvgen import TSVCodeGenerator as TSVGen
from Lacky_Star_Folder.testsz import get_perfect_book_info
from models import Book
import database
import inquirer
from Lacky_Star_Folder.BookRecorder.main import main as run_book_recorder
from Lacky_Star_Folder.BookDataQuerier.main import main as run_book_querier

if __name__ == "__main__":
    print("==== ShimawaNever Database CRUD Application ====")
    print("Hello!")
    print("ShimawaNever データベース CRUD アプリケーションへようこそ！")

    operation = inquirer.prompt([inquirer.List("operation", message="実施する操作を選択してください:", choices=["Create", "Read", "Update", "Delete", "Open CoApps...", "Exit"])])["operation"]

    if operation in [ "Read", "Update", "Delete"]:
        print(f"申し訳ありませんが、{operation} 操作は現在開発中です。")
    elif operation == "Create":
        object_type = inquirer.prompt([inquirer.List("object_type", message="作成するオブジェクトの種類を選択してください:", choices=["Book with ISBN scanner (Loop)"])])["object_type"]

        if object_type == "Book with ISBN scanner (Loop)":
            createBookwithScanner()            

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
            import Lacky_Star_Folder.BookRecordExporter.main
            