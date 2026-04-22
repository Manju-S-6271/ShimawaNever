"""./BookRegister/main.py
App A（書籍登録ロジック）を BookRecorder の設計思想・デザイン思想に基づき
Textual アプリケーション化したもの。

依存: textual, fetch_all (既存モジュール), BookModel (既存モジュール),
      database (既存モジュール), calculate (既存モジュール)
"""

import os
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static, Button, Input, Label, RichLog
from textual.containers import Horizontal, Vertical, ScrollableContainer
from textual.reactive import reactive
from coapps.tsvgen.tsvgen3 import generate_bk_isbn13 as generate_bk_code

# ── 既存モジュール（プロジェクト側で用意されているものをそのまま使用） ──
from coapps.bookcodes import fetch_all          # type: ignore
from models import Book as BookModel            # type: ignore
from coapps.checkdigits import calculate        # type: ignore
import database                                 # type: ignore


class BookRegister(App):
    TITLE = "ShimawaNever CoApps"

    # ── Windows XP 風スタイル（BookRecorder の設計思想を継承・拡張） ──
    CSS = """
    Screen {
        background: #003399;
        align: center middle;
    }

    /* ── メインダイアログ ── */
    #dialog {
        width: 90;
        height: 50;
        background: #ECE9D8;
        border: tall #FFFFFF;
        color: black;
        padding: 0;
    }

    /* ── タイトルバー ── */
    #title_bar {
        background: #0A246A;
        color: white;
        text-style: bold;
        height: 3;
        content-align: left middle;
        padding-left: 1;
    }

    /* ── 入力エリア ── */
    #content {
        padding: 2 4;
        height: 14;
    }

    .instruction {
        margin-bottom: 1;
        text-style: bold;
    }

    Input {
        width: 100%;
        margin-bottom: 1;
        border: solid #7F9DB9;
        background: #FFFFFF;
        color: #000000;
    }

    Input:focus {
        border: double #FF9900;
    }

    #status_area {
        height: 2;
        content-align: left middle;
        color: #008000;
        text-style: bold;
        margin-top: 1;
    }

    /* ── 書籍詳細表示エリア ── */
    #result_title {
        background: #0A246A;
        color: white;
        text-style: bold;
        height: 2;
        content-align: left middle;
        padding-left: 1;
    }

    #result_scroll {
        height: 23;
        border: solid #7F9DB9;
        margin: 0 4;
        background: #FFFFFF;
    }

    #result_log {
        background: #FFFFFF;
        color: #000000;
        padding: 0 1;
    }

    /* ── ボタン行 ── */
    #button_row {
        background: #ECE9D8;
        border-top: solid #999999;
        align: right middle;
        height: 5;
        padding-right: 2;
    }

    Button {
        width: 16;
        margin-left: 1;
        background: #ECE9D8;
        border: solid #FFFFFF;
        color: black;
    }

    #register_button {
        text-style: bold;
    }
    """

    # ── ウィジェット構築 ──
    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical(id="dialog"):
            yield Static(" 書籍登録ソフトウェア", id="title_bar")

            with Vertical(id="content"):
                yield Label("書籍のバーコードをスキャンしてください。", classes="instruction")

                yield Label("1. ISBNコード（上段）:")
                yield Input(placeholder="978... または 979...", id="isbn_input")

                yield Label("2. 書籍JANコード（下段）:")
                yield Input(placeholder="192...", id="jan_input")

                yield Static("", id="status_area")

            # ── 登録結果プレビュー ──
            yield Static(" 登録結果プレビュー", id="result_title")
            with ScrollableContainer(id="result_scroll"):
                yield RichLog(id="result_log", highlight=True, markup=True)

            with Horizontal(id="button_row"):
                yield Button("< 終了", id="back_button", variant="default")
                yield Button("登録 >", id="register_button", variant="primary")

        yield Footer()

    # ── 初期フォーカス ──
    def on_mount(self) -> None:
        self.query_one("#isbn_input").focus()

    # ── Enter キーでフォーカス移動 & 登録実行 ──
    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "isbn_input":
            self.query_one("#jan_input").focus()
        elif event.input.id == "jan_input":
            self._register_book()

    # ── ボタン押下 ──
    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "register_button":
            self._register_book()
        elif event.button.id == "back_button":
            self.exit()

    # ── 書籍登録メイン処理 ──
    def _register_book(self) -> None:
        isbn_widget   = self.query_one("#isbn_input", Input)
        jan_widget    = self.query_one("#jan_input",  Input)
        status        = self.query_one("#status_area", Static)
        log: RichLog  = self.query_one("#result_log",  RichLog)

        isbn = isbn_widget.value.strip()
        jan  = jan_widget.value.strip()

        # ── バリデーション ──
        if not isbn:
            status.update("❌ ISBNコードを入力してください")
            isbn_widget.focus()
            return

        if not (isbn.startswith("978") or isbn.startswith("979")):
            status.update("❌ 不正なISBNコードです（978 / 979 で始まる必要があります）")
            isbn_widget.focus()
            return

        if not jan:
            status.update("❌ 書籍JANコードと両方が必要です。登録できません。")
            jan_widget.focus()
            return

        if not jan.startswith("192"):
            status.update("❌ 不正な書籍JANコードです（192 で始まる必要があります）")
            jan_widget.focus()
            return

        # ── 書籍情報取得 ──
        status.update("⏳ 書籍情報を取得中...")
        self.refresh()

        try:
            book_info = fetch_all(isbn, jan)
            book_info.design_isbn()

            # TSVコード生成
            tsv_code = generate_bk_code(isbn13=str(book_info.align_isbn(only_export=True)))[0]

            # ── DB 保存 ──
            book = BookModel(
                tsv_code      = tsv_code,
                title         = book_info.title,
                authors       = book_info.author,
                publisher     = book_info.publisher,
                published_date= book_info.pubdate,
                description   = book_info.description,
                isbn          = book_info.isbn,
                book_jan      = book_info.jan_code,
                c_code        = book_info.c_code,
                target        = book_info.c_code_target,
                form          = book_info.c_code_form,
                content       = book_info.c_code_content,
                price         = book_info.price,
                shelf_tsv_code= "TSV-SH-0001-00001-0",
            )
            with database.SessionLocal() as session:
                session.add(book)
                session.commit()

            # ── 結果表示 ──
            log.clear()
            log.write(f"[bold green]✅ 登録完了 — TSVコード: {tsv_code}[/bold green]")
            log.write("─" * 60)
            log.write(f"[bold]タイトル    :[/bold] {book_info.title}")
            log.write(f"[bold]著者        :[/bold] {book_info.author}")
            log.write(f"[bold]出版社      :[/bold] {book_info.publisher}")
            log.write(f"[bold]出版日      :[/bold] {book_info.pubdate}")
            log.write(f"[bold]ISBNコード  :[/bold] {book_info.isbn}")
            log.write(f"[bold]書籍JANコード:[/bold] {book_info.jan_code}")
            log.write(f"[bold]Cコード     :[/bold] {book_info.c_code}")
            log.write(f"[bold]  対象      :[/bold] {book_info.c_code_target}")
            log.write(f"[bold]  形態      :[/bold] {book_info.c_code_form}")
            log.write(f"[bold]  内容      :[/bold] {book_info.c_code_content}")
            log.write(f"[bold]価格        :[/bold] {book_info.price} 円")
            log.write("─" * 60)
            if book_info.description:
                log.write(f"[bold]概要:[/bold]")
                log.write(book_info.description)

            status.update(f"✅ TSVコード {tsv_code} として保存しました")

            # ── 入力欄をリセットして次の登録へ ──
            isbn_widget.value = ""
            jan_widget.value  = ""
            isbn_widget.focus()

            # 2秒後にステータスをクリア
            self.set_timer(2.0, lambda: status.update(""))

        except Exception as e:
            status.update(f"⚠️ エラー: {e}")
            log.clear()
            log.write(f"[bold red]エラーの詳細:[/bold red] {e}")


def main() -> None:
    app = BookRegister()
    app.run()


if __name__ == "__main__":
    main()