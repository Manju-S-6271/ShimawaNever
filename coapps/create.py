import inquirer
from models import Book
from coapps.BookApps import BookJAN
from coapps.BookApps import RakutenAPI
from coapps.BookApps import ISBN
from coapps.tsvgen import TSVCodeGenerator as TSVGen

def createBookwithScanner():
    shelf = inquirer.text("これから登録する全ての本に関連付ける書架のTSVコードを入力してください")
    while True:
        isbn = inquirer.text("追加する書籍のISBNコードをスキャンしてください（終了する場合はEnterを押してください）")
        book = Book(isbn = isbn, shelf_tsv_code = shelf, stock_finished = False)

        if not book.isbn:
            break

        book = RakutenAPI.fetch_data(book)
        book = ISBN.design_isbn(book)

        book.book_jan = inquirer.text("追加する書籍の書籍JANコードをスキャンしてください（ない場合はEnterを押してください）")

        if book.book_jan:
            book = BookJAN.fetch_data(book)

        tsv_codes = TSVGen.book_isbn13(book.isbn[4:15])
        book.tsv_code = tsv_codes["TSV_Code"]
        book.s_tsv_code = tsv_codes["S_TSV_Code"]

        print(f"TSVコード         : {book.tsv_code} （Barcode: {book.s_tsv_code}）")
        print(f"書籍グループ      : {book.bookgroup_tsv_code}")
        print(f"親書籍            : {book.parent_tsv_code}")
        print(f"書籍名            : {book.title}")
        print(f"書籍名（読み仮名）: {book.title_phonetic}")
        print(f"サブタイトル      : {book.subtitle}")
        print(f"著者              : {book.authors}")
        print(f"出版社            : {book.publisher}")
        print(f"出版日            : {book.published_date}")
        print(f"説明              : {book.description}")
        print(f"書架              : {book.shelf_tsv_code}")
        print(f"ISBN              : {book.isbn}")
        print(f"書籍JANコード     : {book.book_jan}")
        print(f"Cコード           : {book.c_code}")
        print(f"対象              : {book.target}")
        print(f"形態              : {book.form}")
        print(f"内容              : {book.content}")
        print(f"価格              : {book.price}")
        print(f"サイズ            : {book.size}")
        print(f"在架終了フラグ    : {book.stock_finished}")
        print(f"備考              : {book.note}")
        print(f"登録日時          : {book.issued_timestamp}")
        print(f"最終更新日時      : {book.last_updated_timestamp}")