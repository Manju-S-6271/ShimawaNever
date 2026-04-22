from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static, ProgressBar

class XPInstaller(App):
    # CSSで背景色を「あの青」に設定
    CSS = """
    Screen {
        background: #0000AA;
        align: center middle;
    }
    #dialog {
        width: 60;
        height: 20;
        background: #C0C0C0;  /* グレーのダイアログ */
        border: thick #FFFFFF;
        color: black;
    }
    """

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Static(id="dialog"):
            yield Static("Windows XP セットアップ", id="title")
            yield Static("\nファイルをコピーしています...")
            yield Static("\n残り時間: 約5分")
            yield ProgressBar(total=100, show_eta=False, id="progress")
            # 1秒ごとにプログレスバーを更新するためのタイマーをセット
            self.set_interval(1, self.update_progress)
        yield Footer()

    def update_progress(self):
        progress_bar = self.query_one(ProgressBar)
        
if __name__ == "__main__":
    app = XPInstaller()
    app.run()