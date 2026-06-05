"""./coapps/BookApps/RakutenAPI.py
ISBNコードから書籍情報を取得するモジュール
"""

from models import Book
import requests

def fetch_data(book: Book) -> Book:
    url = f"https://openapi.rakuten.co.jp/services/api/BooksBook/Search/20170404?format=json&isbn={book.isbn}&applicationId=ca16f3e9-c848-4fe4-824d-9827748f2156&accessKey=pk_Bi1el9TxldqBsgkJLtWNFLNcG8tXHAv4FlKBOUNFSHo"
    
    response = requests.get(url)
    data = response.json()["Items"][0]["Item"]

    # print(data)
    book.title = data["title"]
    book.title_phonetic = data["titleKana"]

    book.subtitle = data["subTitle"]

    book.authors = data["author"]
    book.publisher = data["publisherName"]
    book.published_date = data["salesDate"]

    book.description = data["itemCaption"]
    book.size = data["size"]

    return book

# fetch_data(Book(isbn = 9784758026079))