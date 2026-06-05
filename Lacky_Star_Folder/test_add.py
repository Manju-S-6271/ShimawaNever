from coapps.bookcodes import Book
from coapps.scan import scan_multiple_barcodes_stable
from coapps.checkdigits import calculate, verify
from Lacky_Star_Folder.testsz import get_perfect_book_info
from models import Book as BookModel
import database

if __name__ == "__main__":
    # スキャンして2つのコードを取得
    scanned_codes = scan_multiple_barcodes_stable(expected_count=2, stability_threshold=10)

    # 頭文字が "978" の方を ISBN、"192" の方を JAN として識別
    isbn_code = next((code for code in scanned_codes if code.startswith("978")), None)
    jan_code = next((code for code in scanned_codes if code.startswith("192")), None)

    if isbn_code and jan_code:
        book_info = get_perfect_book_info(isbn_code, jan_code)
        book_info.design_isbn()

        stsv_code = int(f"200{book_info.align_isbn(only_export=True)[4:-1]}")
        
        check_digit = calculate(stsv_code, modulus=10, weight=3)
        
        stsv_code = f"200{book_info.align_isbn(only_export=True)[4:-1]}{check_digit}"

        tsv_code = f"TSV-BK-200-{book_info.isbn[6:-2]}-{check_digit}"

        book = BookModel(
            tsv_code=tsv_code,
            title=book_info.title,
            authors=book_info.author,
            publisher=book_info.publisher,
            published_date=book_info.published_date,
            description=book_info.description,
            isbn=book_info.isbn,
            book_jan=book_info.jan_code,
            c_code=book_info.c_code,
            target=book_info.c_code_target,
            form=book_info.c_code_form,
            content=book_info.c_code_content,
            price=book_info.price,
            shelf_tsv_code="TSV-SH-0001-00001-0",
        )
        with database.SessionLocal() as session:
            session.add(book)
            session.commit()

        print(f"ISBNコード {book_info.isbn} 書籍JANコード {book_info.jan_code} に関する次の書籍は、TSVコード {tsv_code} としてデータベースに保存されました。")
        print()
        print(f"タイトル: {book_info.title}")
        print(f"著者: {book_info.author}")
        print(f"出版社: {book_info.publisher}")
        print(f"ISBNコード: {book_info.isbn}")
        print(f"書籍JANコード: {book_info.jan_code}")
        print(f"Cコード: {book_info.c_code}")
        print(f"価格: {book_info.price}円")

