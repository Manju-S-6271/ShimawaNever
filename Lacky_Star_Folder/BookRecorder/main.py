"""./BookRecorder/main.py
ShimawaNeverに登録されていない、これから登録する予定の書籍等に貼り付けられたISBNコードと書籍JANコードをスキャンし、CSVファイルに保存するアプリケーション
（バーコードリーダーを要する）
"""

import csv
import os
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static, Button, Input, Label
from textual.containers import Horizontal, Vertical
from textual.message import Message
import requests
import yaml

csvfile = "books_tsundoku.csv"

class BookRecorder(App):
    TITLE = "ShimawaNever CoApps"
    
    CSS = """
    Screen {
        background: #003399; 
        align: center middle;
    }

    #dialog {
        width: 76;
        height: 32;
        background: #ECE9D8;
        /* outsetの代わりに tall を使い、XPらしい厚みを持たせます */
        border: tall #FFFFFF; 
        color: black;
        padding: 0;
    }

    #title_bar {
        background: #0A246A;
        color: white;
        text-style: bold;
        height: 3;
        content-align: left middle;
        padding-left: 1;
    }

    #content {
        padding: 2 4;
        height: 22;
    }

    .instruction {
        margin-bottom: 1;
        text-style: bold;
    }

    Input {
        width: 100%;
        margin-bottom: 2;
        /* insetの代わりに solid を使用 */
        border: solid #7F9DB9;
        background: #FFFFFF;
        color: #000000;
    }

    Input:focus {
        border: double #FF9900; 
    }

    #status_area {
        height: 3;
        content-align: center middle;
        color: #008000;
        text-style: bold;
    }

    #button_row {
        background: #ECE9D8;
        border-top: solid #999999;
        align: right middle;
        height: 5;
        padding-right: 2;
    }

    Button {
        width: 14;
        margin-left: 1;
        background: #ECE9D8;
        /* outsetの代わりに solid を使用 */
        border: solid #FFFFFF;
        color: black;
    }

    #save_button {
        text-style: bold;
    }
    """

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical(id="dialog"):
            yield Static(" 書籍情報一時保管ソフトウェア", id="title_bar")
            
            with Vertical(id="content"):
                yield Label("書籍のバーコードをスキャンしてください。", classes="instruction")
                
                yield Label("1. ISBNコード (上段):")
                yield Input(placeholder="978...", id="isbn_input")

                yield Label("2. 書籍JANコード (下段):")
                yield Input(placeholder="192...", id="jan_input")
                
                yield Static("", id="status_area")

            with Horizontal(id="button_row"):
                yield Button("< 終了", id="back_button", variant="default")
                yield Button("登録 >", id="save_button", variant="primary")
        yield Footer()

    def on_mount(self) -> None:
        self.query_one("#isbn_input").focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "isbn_input":
            # 978から始まらない場合は警告を出すなどの拡張も可能
            self.query_one("#jan_input").focus()
        elif event.input.id == "jan_input":
            self._save_record()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "save_button":
            self._save_record()
        elif event.button.id == "back_button":
            self.exit()

    def _save_record(self) -> None:
        isbn_widget = self.query_one("#isbn_input", Input)
        jan_widget = self.query_one("#jan_input", Input)
        status = self.query_one("#status_area", Static)

        isbn = isbn_widget.value.strip()
        jan = jan_widget.value.strip()

        # 簡易バリデーション
        if not (isbn.startswith("978") or isbn.startswith("979")):
            status.update("❌ 不正なISBNコードです")
            isbn_widget.focus()
            return
        
        if not jan.startswith("192") and not jan == "":
            status.update("❌ 不正なJANコードです")
            jan_widget.focus()
            return

        try:
            # openbd_url = f"https://api.openbd.jp/v1/get?isbn={isbn}"
            # response = requests.get(openbd_url)
            # if response.status_code == 200:
            #     data = response.json()
            #     if data and data[0] and data[0].get("summary"):
            #         title = data[0]["summary"].get("title", "タイトル情報なし")
            # 設定ファイルからAI生成とGoogle Cloud APIに関する設定を読み込む
            # Google Books API
            with open("./settings.yml", "r") as f:
                settings = yaml.safe_load(f)
                _google_cloud_api_key = settings["book_info_entry"]["google_cloud_api_key"]

            google_books_url = f"https://www.googleapis.com/books/v1/volumes?q=isbn:{isbn}&key={_google_cloud_api_key}"
            response = requests.get(google_books_url)
            if response.status_code == 200:
                try:
                    data = response.json()
                    if data.get("items"):
                        title = data["items"][0]["volumeInfo"].get("title", "タイトル情報なし")
                    else:
                        title = "タイトル情報なし"
                except Exception as e:
                    title = "タイトル情報なし"
            else:
                title = "タイトル情報なし"

            # Google Booksで取得できなかった場合のみopenBDへ
            if title == "タイトル情報なし":
                openbd_url = f"https://api.openbd.jp/v1/get?isbn={isbn}"
                response = requests.get(openbd_url)
                if response.status_code == 200:
                    try:
                        data = response.json()
                        if data and data[0] and data[0].get("summary"):
                            title = data[0]["summary"].get("title", "タイトル情報なし")
                        else:
                            title = "タイトル情報なし"
                    except Exception as e:
                        title = "タイトル情報なし"
                        
            with open(csvfile, "a", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow([isbn, jan, title if 'title' in locals() else "タイトル情報なし"])
            
            # 成功時の処理
            status.update(f"書籍『{title}』が登録されました！")
            isbn_widget.value = ""
            jan_widget.value = ""
            isbn_widget.focus()
            
            # 1秒後にステータスをクリア
            self.set_timer(1.5, lambda: status.update(""))
            
        except Exception as e:
            status.update(f"⚠️ エラー: {e}")

def main():
    if not os.path.exists(csvfile):
        with open(csvfile, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["ISBNコード", "書籍JANコード", "タイトル"])

    app = BookRecorder()
    app.run()