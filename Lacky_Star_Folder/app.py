"""app.py
TSVデータベース管理 CLIアプリケーション
Windows XP セットアップ風デザイン
"""

import sys
import os
import json
from datetime import datetime, timezone
from typing import Optional, Any

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from textual.app import App, ComposeResult
from textual.widgets import (
    Header, Footer, Static, Button, Input, Label,
    DataTable, Select, TextArea, TabbedContent, TabPane
)
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.screen import Screen, ModalScreen
from textual.binding import Binding
from textual import events
from textual.reactive import reactive

import database
from database import init_db
from models import Record, Issuer, Book, BookGroup, Shelf, ChangeHistory
from Lacky_Star_Folder.tsvgen.tsvgen import (
    generate_bk_code, generate_bg_code, generate_re_code,
    generate_is_code, generate_sh_code,
    validate_tsv_code, validate_s_tsv_code,
)

# ─────────────────────────────────────────────
#  XP風 CSS テーマ
# ─────────────────────────────────────────────
XP_CSS = """
/* ═══════════════════════════════════
   基本 - XP ブルー背景
   ═══════════════════════════════════ */
Screen {
    background: #0000AA;
    align: center middle;
    overflow: hidden;
}

/* ─── ヘッダー/フッター ─── */
Header {
    background: #000080;
    color: #FFFF00;
    height: 1;
    dock: top;
}
Footer {
    background: #000080;
    color: #C0C0C0;
    height: 1;
    dock: bottom;
}

/* ─── メインウィンドウ（灰色パネル） ─── */
#main_panel {
    width: 95%;
    height: 90%;
    background: #C0C0C0;
    border: tall #FFFFFF;
    border-right: tall #808080;
    border-bottom: tall #808080;
    padding: 0 1;
}

/* ─── タイトルバー ─── */
#titlebar {
    background: #000080;
    color: #FFFFFF;
    height: 1;
    padding: 0 1;
    text-style: bold;
}

/* ─── タブ風コンテナ ─── */
TabbedContent {
    background: #C0C0C0;
    height: 1fr;
}
TabbedContent ContentSwitcher {
    background: #C0C0C0;
}
TabPane {
    background: #C0C0C0;
    padding: 0 1;
}

/* ─── DataTable ─── */
DataTable {
    background: #FFFFFF;
    color: #000000;
    border: tall #808080;
    border-right: tall #FFFFFF;
    border-bottom: tall #FFFFFF;
    height: 1fr;
}
DataTable > .datatable--header {
    background: #000080;
    color: #FFFFFF;
    text-style: bold;
}
DataTable > .datatable--cursor {
    background: #000080;
    color: #FFFFFF;
}
DataTable > .datatable--even-row {
    background: #E8E8E8;
}

/* ─── ボタン（XP風 押し込み） ─── */
Button {
    background: #C0C0C0;
    color: #000000;
    border: tall #FFFFFF;
    border-right: tall #808080;
    border-bottom: tall #808080;
    min-width: 12;
    height: 3;
    text-style: none;
}
Button:focus {
    border: tall #000080;
    text-style: bold;
}
Button:hover {
    background: #D0D0D0;
}
Button.-focus, Button:focus {
    border: tall #808080;
    border-right: tall #FFFFFF;
    border-bottom: tall #FFFFFF;
    background: #A0A0A0;
}
Button.danger {
    color: #CC0000;
    text-style: bold;
}
Button.primary {
    background: #000080;
    color: #FFFFFF;
    border: tall #4040FF;
    border-right: tall #000040;
    border-bottom: tall #000040;
}

/* ─── 入力フィールド ─── */
Input {
    background: #FFFFFF;
    color: #000000;
    border: tall #808080;
    border-right: tall #FFFFFF;
    border-bottom: tall #FFFFFF;
    height: 3;
}
Input:focus {
    border: tall #000080;
}

TextArea {
    background: #FFFFFF;
    color: #000000;
    border: tall #808080;
    border-right: tall #FFFFFF;
    border-bottom: tall #FFFFFF;
    height: 5;
}

Select {
    background: #FFFFFF;
    color: #000000;
    border: tall #808080;
    height: 3;
}

/* ─── ラベル ─── */
Label {
    background: #C0C0C0;
    color: #000000;
    padding: 0 0;
}
.section_label {
    background: #000080;
    color: #FFFFFF;
    padding: 0 1;
    text-style: bold;
}
.error_label {
    color: #CC0000;
    background: #C0C0C0;
    text-style: bold;
}
.success_label {
    color: #006600;
    background: #C0C0C0;
    text-style: bold;
}
.info_label {
    color: #000080;
    background: #C0C0C0;
}

/* ─── ボタン列 ─── */
.button_row {
    height: 3;
    align: left middle;
    background: #C0C0C0;
    margin-top: 1;
}
.button_row Button {
    margin-right: 1;
}

/* ─── フォームエリア ─── */
.form_area {
    background: #C0C0C0;
    height: auto;
    padding: 0 0;
}
.form_row {
    height: auto;
    background: #C0C0C0;
    margin-bottom: 0;
}
.field_label {
    width: 20;
    height: 3;
    align: left middle;
    background: #C0C0C0;
    color: #000000;
    padding: 1 0;
}
.field_input {
    width: 1fr;
}

/* ─── モーダルダイアログ ─── */
ModalScreen {
    align: center middle;
    background: rgba(0,0,0,0.5);
}
#dialog {
    width: 60;
    height: auto;
    max-height: 40;
    background: #C0C0C0;
    border: tall #FFFFFF;
    border-right: tall #808080;
    border-bottom: tall #808080;
    padding: 1 2;
}
#dialog_title {
    background: #000080;
    color: #FFFFFF;
    text-style: bold;
    padding: 0 1;
    margin-bottom: 1;
}
.dialog_buttons {
    height: 3;
    align: center middle;
    margin-top: 1;
}
.dialog_buttons Button {
    margin: 0 1;
}

/* ─── ステータスバー ─── */
#status_bar {
    background: #C0C0C0;
    color: #000000;
    height: 1;
    border-top: tall #808080;
    padding: 0 1;
}

/* ─── スクロール ─── */
ScrollableContainer {
    background: #C0C0C0;
    scrollbar-color: #000080;
    scrollbar-background: #C0C0C0;
}
"""


# ─────────────────────────────────────────────
#  CRUD ヘルパー関数群
# ─────────────────────────────────────────────

def log_change(session, tsv_code: str, record_type: str, change_type: str, data: dict):
    """変更履歴を記録する"""
    history = ChangeHistory(
        tsv_code=tsv_code,
        record_type=record_type,
        change_type=change_type,
        changed_data=json.dumps(data, ensure_ascii=False),
    )
    session.add(history)


def model_to_dict(obj) -> dict:
    """SQLAlchemyオブジェクトを辞書に変換"""
    d = {}
    for col in obj.__table__.columns:
        val = getattr(obj, col.name)
        if isinstance(val, datetime):
            val = val.isoformat()
        d[col.name] = val
    return d


# ─────────────────────────────────────────────
#  確認ダイアログ
# ─────────────────────────────────────────────

class ConfirmDialog(ModalScreen):
    """はい/いいえ確認ダイアログ"""

    def __init__(self, message: str, title: str = "確認", **kwargs):
        super().__init__(**kwargs)
        self._message = message
        self._title = title

    def compose(self) -> ComposeResult:
        with Container(id="dialog"):
            yield Static(f"▶ {self._title}", id="dialog_title")
            yield Static(self._message)
            with Horizontal(classes="dialog_buttons"):
                yield Button("  はい(Y)  ", id="yes_btn", classes="primary")
                yield Button("  いいえ(N)  ", id="no_btn")

    def on_button_pressed(self, event: Button.Pressed):
        self.dismiss(event.button.id == "yes_btn")


# ─────────────────────────────────────────────
#  メッセージダイアログ
# ─────────────────────────────────────────────

class MessageDialog(ModalScreen):
    """情報メッセージダイアログ"""

    def __init__(self, message: str, title: str = "情報", error: bool = False, **kwargs):
        super().__init__(**kwargs)
        self._message = message
        self._title = title
        self._error = error

    def compose(self) -> ComposeResult:
        icon = "✖" if self._error else "✔"
        with Container(id="dialog"):
            yield Static(f"{icon} {self._title}", id="dialog_title")
            yield Static(self._message)
            with Horizontal(classes="dialog_buttons"):
                yield Button("    OK    ", id="ok_btn", classes="primary")

    def on_button_pressed(self, event: Button.Pressed):
        self.dismiss(True)


# ─────────────────────────────────────────────
#  レコード詳細ダイアログ
# ─────────────────────────────────────────────

class RecordDetailDialog(ModalScreen):
    """レコード詳細表示ダイアログ"""

    BINDINGS = [Binding("escape", "dismiss", "閉じる")]

    def __init__(self, data: dict, title: str = "詳細", **kwargs):
        super().__init__(**kwargs)
        self._data = data
        self._title = title

    def compose(self) -> ComposeResult:
        with Container(id="dialog"):
            yield Static(f"📋 {self._title}", id="dialog_title")
            with ScrollableContainer():
                for key, val in self._data.items():
                    if val is not None:
                        yield Static(f"[bold]{key}:[/] {val}")
            with Horizontal(classes="dialog_buttons"):
                yield Button("    OK    ", id="ok_btn", classes="primary")

    def on_button_pressed(self, _):
        self.dismiss(True)


# ─────────────────────────────────────────────
#  書架管理タブ
# ─────────────────────────────────────────────

class ShelvesTab(Static):
    """書架[SH] CRUD パネル"""

    def compose(self) -> ComposeResult:
        yield Static("─── 書架管理 [SH] ───────────────────────────────", classes="section_label")

        with Horizontal(classes="button_row"):
            yield Button("🔍 一覧更新", id="shelf_refresh")
            yield Button("➕ 新規追加", id="shelf_add")
            yield Button("✏  編集", id="shelf_edit")
            yield Button("🗑  削除", id="shelf_delete", classes="danger")
            yield Button("📋 詳細", id="shelf_detail")

        yield DataTable(id="shelf_table")
        yield Label("", id="shelf_status", classes="info_label")

    def on_mount(self):
        self._setup_table()
        self._load_data()

    def _setup_table(self):
        t = self.query_one("#shelf_table", DataTable)
        t.add_columns("TSVコード", "書架名", "読み仮名", "住所", "詳細位置", "登録日時")
        t.cursor_type = "row"

    def _load_data(self):
        t = self.query_one("#shelf_table", DataTable)
        t.clear()
        session = database.SessionLocal()
        try:
            rows = session.query(Shelf).order_by(Shelf.issued_timestamp.desc()).all()
            for r in rows:
                dt = r.issued_timestamp.strftime("%Y-%m-%d") if r.issued_timestamp else ""
                t.add_row(
                    r.tsv_code or "",
                    r.name or "",
                    r.name_phonetic or "",
                    r.address or "",
                    r.specific_location or "",
                    dt,
                    key=r.tsv_code,
                )
            self.query_one("#shelf_status").update(f"✔ {len(rows)} 件")
        except Exception as e:
            self.query_one("#shelf_status").update(f"エラー: {e}")
        finally:
            session.close()

    def _get_selected_key(self) -> Optional[str]:
        t = self.query_one("#shelf_table", DataTable)
        if t.cursor_row >= 0 and t.row_count > 0:
            row_key = t.get_row_at(t.cursor_row)
            return t.get_cell_at((t.cursor_row, 0))
        return None

    def on_button_pressed(self, event: Button.Pressed):
        btn_id = event.button.id
        if btn_id == "shelf_refresh":
            self._load_data()
        elif btn_id == "shelf_add":
            self.app.push_screen(ShelfFormDialog(None), self._on_form_closed)
        elif btn_id == "shelf_edit":
            key = self._get_selected_key()
            if key:
                self.app.push_screen(ShelfFormDialog(key), self._on_form_closed)
            else:
                self.app.push_screen(MessageDialog("行を選択してください。", "警告", error=True))
        elif btn_id == "shelf_delete":
            key = self._get_selected_key()
            if key:
                self.app.push_screen(
                    ConfirmDialog(f"書架「{key}」を削除しますか？", "削除確認"),
                    lambda ok: self._do_delete(key) if ok else None,
                )
            else:
                self.app.push_screen(MessageDialog("行を選択してください。", "警告", error=True))
        elif btn_id == "shelf_detail":
            key = self._get_selected_key()
            if key:
                session = database.SessionLocal()
                try:
                    obj = session.query(Shelf).get(key)
                    if obj:
                        self.app.push_screen(RecordDetailDialog(model_to_dict(obj), f"書架詳細: {key}"))
                finally:
                    session.close()

    def _on_form_closed(self, saved: bool):
        if saved:
            self._load_data()

    def _do_delete(self, key: str):
        session = database.SessionLocal()
        try:
            obj = session.query(Shelf).get(key)
            if obj:
                log_change(session, key, "Shelf", "削除", model_to_dict(obj))
                session.delete(obj)
                session.commit()
                self.app.push_screen(MessageDialog(f"削除しました: {key}", "完了"))
                self._load_data()
        except Exception as e:
            session.rollback()
            self.app.push_screen(MessageDialog(str(e), "エラー", error=True))
        finally:
            session.close()


class ShelfFormDialog(ModalScreen):
    """書架の追加/編集フォーム"""

    BINDINGS = [Binding("escape", "dismiss_false", "キャンセル")]

    def __init__(self, tsv_code: Optional[str], **kwargs):
        super().__init__(**kwargs)
        self._tsv_code = tsv_code
        self._obj = None

    def compose(self) -> ComposeResult:
        title = f"書架編集: {self._tsv_code}" if self._tsv_code else "書架 新規追加"
        with Container(id="dialog"):
            yield Static(f"🗄 {title}", id="dialog_title")
            with ScrollableContainer():
                with Horizontal(classes="form_row"):
                    yield Label("TSVコード", classes="field_label")
                    yield Input(placeholder="TSV-SH-...", id="f_tsv_code", classes="field_input")
                with Horizontal(classes="form_row"):
                    yield Label("書架名 *", classes="field_label")
                    yield Input(placeholder="例: 自宅書架A", id="f_name", classes="field_input")
                with Horizontal(classes="form_row"):
                    yield Label("読み仮名", classes="field_label")
                    yield Input(placeholder="じたくしょかA", id="f_name_phonetic", classes="field_input")
                with Horizontal(classes="form_row"):
                    yield Label("住所", classes="field_label")
                    yield Input(placeholder="東京都...", id="f_address", classes="field_input")
                with Horizontal(classes="form_row"):
                    yield Label("詳細位置", classes="field_label")
                    yield Input(placeholder="1F 書斎 棚3段目", id="f_specific_location", classes="field_input")
                with Horizontal(classes="form_row"):
                    yield Label("親書架コード", classes="field_label")
                    yield Input(placeholder="TSV-SH-...(任意)", id="f_parent_tsv_code", classes="field_input")
                with Horizontal(classes="form_row"):
                    yield Label("備考", classes="field_label")
                    yield Input(placeholder="メモ", id="f_note", classes="field_input")
                yield Label("", id="form_error", classes="error_label")
            with Horizontal(classes="dialog_buttons"):
                yield Button("  保存(S)  ", id="save_btn", classes="primary")
                yield Button("  キャンセル  ", id="cancel_btn")

    def on_mount(self):
        if self._tsv_code:
            session = database.SessionLocal()
            try:
                self._obj = session.query(Shelf).get(self._tsv_code)
                if self._obj:
                    self.query_one("#f_tsv_code", Input).value = self._obj.tsv_code or ""
                    self.query_one("#f_name", Input).value = self._obj.name or ""
                    self.query_one("#f_name_phonetic", Input).value = self._obj.name_phonetic or ""
                    self.query_one("#f_address", Input).value = self._obj.address or ""
                    self.query_one("#f_specific_location", Input).value = self._obj.specific_location or ""
                    self.query_one("#f_parent_tsv_code", Input).value = self._obj.parent_tsv_code or ""
                    self.query_one("#f_note", Input).value = self._obj.note or ""
                    self.query_one("#f_tsv_code", Input).disabled = True
            finally:
                session.close()

    def action_dismiss_false(self):
        self.dismiss(False)

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "cancel_btn":
            self.dismiss(False)
        elif event.button.id == "save_btn":
            self._save()
        elif event.button.id == "auto_tsv_btn":
            self._auto_generate_tsv()

    def _auto_generate_tsv(self):
        """TSVコードを自動採番してフィールドに設定する"""
        try:
            parent = self.query_one("#f_parent_tsv_code", Input).value.strip() or None
            result = generate_sh_code(parent_shelf_tsv_code=parent)
            self.query_one("#f_tsv_code", Input).value = result["tsv_code"]
            s_tsv = result["s_tsv_code"]
            self.query_one("#form_error").update(
                f"✔ 採番: {result['tsv_code']}  S-TSV: {s_tsv}"
            )
        except Exception as e:
            self.query_one("#form_error").update(f"✖ 自動採番エラー: {e}")

    def _save(self):
        tsv_code = self.query_one("#f_tsv_code", Input).value.strip()
        name = self.query_one("#f_name", Input).value.strip()

        if not name:
            self.query_one("#form_error").update("✖ 書架名は必須です。")
            return
        if not tsv_code and not self._tsv_code:
            self.query_one("#form_error").update("✖ TSVコードは必須です（自動採番ボタンをお使いください）。")
            return
        # TSVコード形式検証
        if tsv_code:
            ok, msg = validate_tsv_code(tsv_code)
            if not ok:
                self.query_one("#form_error").update(f"✖ TSVコード形式エラー: {msg}")
                return

        session = database.SessionLocal()
        try:
            if self._tsv_code:
                obj = session.query(Shelf).get(self._tsv_code)
                obj.name = name
                obj.name_phonetic = self.query_one("#f_name_phonetic", Input).value.strip() or None
                obj.address = self.query_one("#f_address", Input).value.strip() or None
                obj.specific_location = self.query_one("#f_specific_location", Input).value.strip() or None
                obj.parent_tsv_code = self.query_one("#f_parent_tsv_code", Input).value.strip() or None
                obj.note = self.query_one("#f_note", Input).value.strip() or None
                obj.last_updated_timestamp = datetime.now(timezone.utc)
                log_change(session, self._tsv_code, "Shelf", "更新", model_to_dict(obj))
                session.commit()
            else:
                obj = Shelf(
                    tsv_code=tsv_code,
                    name=name,
                    name_phonetic=self.query_one("#f_name_phonetic", Input).value.strip() or None,
                    address=self.query_one("#f_address", Input).value.strip() or None,
                    specific_location=self.query_one("#f_specific_location", Input).value.strip() or None,
                    parent_tsv_code=self.query_one("#f_parent_tsv_code", Input).value.strip() or None,
                    note=self.query_one("#f_note", Input).value.strip() or None,
                )
                session.add(obj)
                log_change(session, tsv_code, "Shelf", "追加", model_to_dict(obj))
                session.commit()
            self.dismiss(True)
        except Exception as e:
            session.rollback()
            self.query_one("#form_error").update(f"✖ {e}")
        finally:
            session.close()


# ─────────────────────────────────────────────
#  発行者管理タブ
# ─────────────────────────────────────────────

class IssuersTab(Static):
    """発行者[IS] CRUD パネル"""

    def compose(self) -> ComposeResult:
        yield Static("─── 発行者管理 [IS] ──────────────────────────────", classes="section_label")
        with Horizontal(classes="button_row"):
            yield Button("🔍 一覧更新", id="issuer_refresh")
            yield Button("➕ 新規追加", id="issuer_add")
            yield Button("✏  編集", id="issuer_edit")
            yield Button("🗑  削除", id="issuer_delete", classes="danger")
            yield Button("📋 詳細", id="issuer_detail")
        yield DataTable(id="issuer_table")
        yield Label("", id="issuer_status", classes="info_label")

    def on_mount(self):
        t = self.query_one("#issuer_table", DataTable)
        t.add_columns("TSVコード", "発行者名", "読み仮名", "発行者コード", "登録日時")
        t.cursor_type = "row"
        self._load_data()

    def _load_data(self):
        t = self.query_one("#issuer_table", DataTable)
        t.clear()
        session = database.SessionLocal()
        try:
            rows = session.query(Issuer).order_by(Issuer.issued_timestamp.desc()).all()
            for r in rows:
                dt = r.issued_timestamp.strftime("%Y-%m-%d") if r.issued_timestamp else ""
                t.add_row(r.tsv_code or "", r.name or "", r.name_phonetic or "", r.issuer_code or "", dt, key=r.tsv_code)
            self.query_one("#issuer_status").update(f"✔ {len(rows)} 件")
        except Exception as e:
            self.query_one("#issuer_status").update(f"エラー: {e}")
        finally:
            session.close()

    def _get_selected_key(self) -> Optional[str]:
        t = self.query_one("#issuer_table", DataTable)
        if t.cursor_row >= 0 and t.row_count > 0:
            return t.get_cell_at((t.cursor_row, 0))
        return None

    def on_button_pressed(self, event: Button.Pressed):
        btn_id = event.button.id
        if btn_id == "issuer_refresh":
            self._load_data()
        elif btn_id == "issuer_add":
            self.app.push_screen(IssuerFormDialog(None), self._on_form_closed)
        elif btn_id == "issuer_edit":
            key = self._get_selected_key()
            if key:
                self.app.push_screen(IssuerFormDialog(key), self._on_form_closed)
            else:
                self.app.push_screen(MessageDialog("行を選択してください。", "警告", error=True))
        elif btn_id == "issuer_delete":
            key = self._get_selected_key()
            if key:
                self.app.push_screen(
                    ConfirmDialog(f"発行者「{key}」を削除しますか？", "削除確認"),
                    lambda ok: self._do_delete(key) if ok else None,
                )
            else:
                self.app.push_screen(MessageDialog("行を選択してください。", "警告", error=True))
        elif btn_id == "issuer_detail":
            key = self._get_selected_key()
            if key:
                session = database.SessionLocal()
                try:
                    obj = session.query(Issuer).get(key)
                    if obj:
                        self.app.push_screen(RecordDetailDialog(model_to_dict(obj), f"発行者詳細: {key}"))
                finally:
                    session.close()

    def _on_form_closed(self, saved):
        if saved:
            self._load_data()

    def _do_delete(self, key: str):
        session = database.SessionLocal()
        try:
            obj = session.query(Issuer).get(key)
            if obj:
                log_change(session, key, "Issuer", "削除", model_to_dict(obj))
                session.delete(obj)
                session.commit()
                self.app.push_screen(MessageDialog(f"削除しました: {key}", "完了"))
                self._load_data()
        except Exception as e:
            session.rollback()
            self.app.push_screen(MessageDialog(str(e), "エラー", error=True))
        finally:
            session.close()


class IssuerFormDialog(ModalScreen):
    BINDINGS = [Binding("escape", "dismiss_false", "キャンセル")]

    def __init__(self, tsv_code: Optional[str], **kwargs):
        super().__init__(**kwargs)
        self._tsv_code = tsv_code

    def compose(self) -> ComposeResult:
        title = f"発行者編集: {self._tsv_code}" if self._tsv_code else "発行者 新規追加"
        with Container(id="dialog"):
            yield Static(f"🏢 {title}", id="dialog_title")
            with ScrollableContainer():
                with Horizontal(classes="form_row"):
                    yield Label("TSVコード", classes="field_label")
                    yield Input(placeholder="TSV-IS-...", id="f_tsv_code", classes="field_input")
                if not self._tsv_code:
                    with Horizontal(classes="form_row"):
                        yield Label("", classes="field_label")
                        yield Button("🎲 TSVコード自動採番", id="auto_tsv_btn")
                with Horizontal(classes="form_row"):
                    yield Label("発行者名 *", classes="field_label")
                    yield Input(placeholder="例: 国土交通省", id="f_name", classes="field_input")
                with Horizontal(classes="form_row"):
                    yield Label("読み仮名", classes="field_label")
                    yield Input(id="f_name_phonetic", classes="field_input")
                with Horizontal(classes="form_row"):
                    yield Label("発行者コード", classes="field_label")
                    yield Input(id="f_issuer_code", classes="field_input")
                with Horizontal(classes="form_row"):
                    yield Label("子番号", classes="field_label")
                    yield Input(placeholder="数値", id="f_child_number", classes="field_input")
                with Horizontal(classes="form_row"):
                    yield Label("親発行者コード", classes="field_label")
                    yield Input(id="f_parent_tsv_code", classes="field_input")
                with Horizontal(classes="form_row"):
                    yield Label("備考", classes="field_label")
                    yield Input(id="f_note", classes="field_input")
                yield Label("", id="form_error", classes="error_label")
            with Horizontal(classes="dialog_buttons"):
                yield Button("  保存(S)  ", id="save_btn", classes="primary")
                yield Button("  キャンセル  ", id="cancel_btn")

    def on_mount(self):
        if self._tsv_code:
            session = database.SessionLocal()
            try:
                obj = session.query(Issuer).get(self._tsv_code)
                if obj:
                    self.query_one("#f_tsv_code", Input).value = obj.tsv_code or ""
                    self.query_one("#f_tsv_code", Input).disabled = True
                    self.query_one("#f_name", Input).value = obj.name or ""
                    self.query_one("#f_name_phonetic", Input).value = obj.name_phonetic or ""
                    self.query_one("#f_issuer_code", Input).value = obj.issuer_code or ""
                    self.query_one("#f_child_number", Input).value = str(obj.child_number) if obj.child_number is not None else ""
                    self.query_one("#f_parent_tsv_code", Input).value = obj.parent_tsv_code or ""
                    self.query_one("#f_note", Input).value = obj.note or ""
            finally:
                session.close()

    def action_dismiss_false(self):
        self.dismiss(False)

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "cancel_btn":
            self.dismiss(False)
        elif event.button.id == "save_btn":
            self._save()
        elif event.button.id == "auto_tsv_btn":
            self._auto_generate_tsv()

    def _auto_generate_tsv(self):
        try:
            result = generate_is_code()
            self.query_one("#f_tsv_code", Input).value = result["tsv_code"]
            self.query_one("#form_error").update(
                f"✔ 採番: {result['tsv_code']}  S-TSV: {result['s_tsv_code']}"
            )
        except Exception as e:
            self.query_one("#form_error").update(f"✖ 自動採番エラー: {e}")

    def _save(self):
        tsv_code = self.query_one("#f_tsv_code", Input).value.strip()
        name = self.query_one("#f_name", Input).value.strip()
        if not name:
            self.query_one("#form_error").update("✖ 発行者名は必須です。")
            return
        if tsv_code:
            ok, msg = validate_tsv_code(tsv_code)
            if not ok:
                self.query_one("#form_error").update(f"✖ TSVコード形式エラー: {msg}")
                return
        child_num_str = self.query_one("#f_child_number", Input).value.strip()
        child_num = int(child_num_str) if child_num_str.isdigit() else None

        session = database.SessionLocal()
        try:
            if self._tsv_code:
                obj = session.query(Issuer).get(self._tsv_code)
                obj.name = name
                obj.name_phonetic = self.query_one("#f_name_phonetic", Input).value.strip() or None
                obj.issuer_code = self.query_one("#f_issuer_code", Input).value.strip() or None
                obj.child_number = child_num
                obj.parent_tsv_code = self.query_one("#f_parent_tsv_code", Input).value.strip() or None
                obj.note = self.query_one("#f_note", Input).value.strip() or None
                obj.last_updated_timestamp = datetime.now(timezone.utc)
                log_change(session, self._tsv_code, "Issuer", "更新", model_to_dict(obj))
                session.commit()
            else:
                if not tsv_code:
                    self.query_one("#form_error").update("✖ TSVコードは必須です。")
                    return
                obj = Issuer(
                    tsv_code=tsv_code,
                    name=name,
                    name_phonetic=self.query_one("#f_name_phonetic", Input).value.strip() or None,
                    issuer_code=self.query_one("#f_issuer_code", Input).value.strip() or None,
                    child_number=child_num,
                    parent_tsv_code=self.query_one("#f_parent_tsv_code", Input).value.strip() or None,
                    note=self.query_one("#f_note", Input).value.strip() or None,
                )
                session.add(obj)
                log_change(session, tsv_code, "Issuer", "追加", model_to_dict(obj))
                session.commit()
            self.dismiss(True)
        except Exception as e:
            session.rollback()
            self.query_one("#form_error").update(f"✖ {e}")
        finally:
            session.close()


# ─────────────────────────────────────────────
#  書籍グループ管理タブ
# ─────────────────────────────────────────────

class BookGroupsTab(Static):
    """書籍グループ[BG] CRUD パネル"""

    def compose(self) -> ComposeResult:
        yield Static("─── 書籍グループ管理 [BG] ────────────────────────", classes="section_label")
        with Horizontal(classes="button_row"):
            yield Button("🔍 一覧更新", id="bg_refresh")
            yield Button("➕ 新規追加", id="bg_add")
            yield Button("✏  編集", id="bg_edit")
            yield Button("🗑  削除", id="bg_delete", classes="danger")
            yield Button("📋 詳細", id="bg_detail")
        yield DataTable(id="bg_table")
        yield Label("", id="bg_status", classes="info_label")

    def on_mount(self):
        t = self.query_one("#bg_table", DataTable)
        t.add_columns("TSVコード", "グループ名", "読み仮名", "親グループ", "登録日時")
        t.cursor_type = "row"
        self._load_data()

    def _load_data(self):
        t = self.query_one("#bg_table", DataTable)
        t.clear()
        session = database.SessionLocal()
        try:
            rows = session.query(BookGroup).order_by(BookGroup.issued_timestamp.desc()).all()
            for r in rows:
                dt = r.issued_timestamp.strftime("%Y-%m-%d") if r.issued_timestamp else ""
                t.add_row(r.tsv_code or "", r.title or "", r.title_phonetic or "", r.parent_tsv_code or "", dt, key=r.tsv_code)
            self.query_one("#bg_status").update(f"✔ {len(rows)} 件")
        except Exception as e:
            self.query_one("#bg_status").update(f"エラー: {e}")
        finally:
            session.close()

    def _get_selected_key(self):
        t = self.query_one("#bg_table", DataTable)
        if t.cursor_row >= 0 and t.row_count > 0:
            return t.get_cell_at((t.cursor_row, 0))
        return None

    def on_button_pressed(self, event: Button.Pressed):
        btn_id = event.button.id
        if btn_id == "bg_refresh":
            self._load_data()
        elif btn_id == "bg_add":
            self.app.push_screen(BookGroupFormDialog(None), lambda s: self._load_data() if s else None)
        elif btn_id == "bg_edit":
            key = self._get_selected_key()
            if key:
                self.app.push_screen(BookGroupFormDialog(key), lambda s: self._load_data() if s else None)
            else:
                self.app.push_screen(MessageDialog("行を選択してください。", "警告", error=True))
        elif btn_id == "bg_delete":
            key = self._get_selected_key()
            if key:
                self.app.push_screen(ConfirmDialog(f"グループ「{key}」を削除しますか？", "削除確認"),
                    lambda ok: self._do_delete(key) if ok else None)
            else:
                self.app.push_screen(MessageDialog("行を選択してください。", "警告", error=True))
        elif btn_id == "bg_detail":
            key = self._get_selected_key()
            if key:
                session = database.SessionLocal()
                try:
                    obj = session.query(BookGroup).get(key)
                    if obj:
                        self.app.push_screen(RecordDetailDialog(model_to_dict(obj), f"書籍グループ詳細: {key}"))
                finally:
                    session.close()

    def _do_delete(self, key: str):
        session = database.SessionLocal()
        try:
            obj = session.query(BookGroup).get(key)
            if obj:
                log_change(session, key, "BookGroup", "削除", model_to_dict(obj))
                session.delete(obj)
                session.commit()
                self.app.push_screen(MessageDialog(f"削除しました: {key}", "完了"))
                self._load_data()
        except Exception as e:
            session.rollback()
            self.app.push_screen(MessageDialog(str(e), "エラー", error=True))
        finally:
            session.close()


class BookGroupFormDialog(ModalScreen):
    BINDINGS = [Binding("escape", "dismiss_false", "キャンセル")]

    def __init__(self, tsv_code: Optional[str], **kwargs):
        super().__init__(**kwargs)
        self._tsv_code = tsv_code

    def compose(self) -> ComposeResult:
        title = f"グループ編集: {self._tsv_code}" if self._tsv_code else "書籍グループ 新規追加"
        with Container(id="dialog"):
            yield Static(f"📚 {title}", id="dialog_title")
            with ScrollableContainer():
                with Horizontal(classes="form_row"):
                    yield Label("TSVコード", classes="field_label")
                    yield Input(placeholder="TSV-BG-...", id="f_tsv_code", classes="field_input")
                if not self._tsv_code:
                    with Horizontal(classes="form_row"):
                        yield Label("", classes="field_label")
                        yield Button("🎲 TSVコード自動採番", id="auto_tsv_btn")
                with Horizontal(classes="form_row"):
                    yield Label("グループ名 *", classes="field_label")
                    yield Input(id="f_title", classes="field_input")
                with Horizontal(classes="form_row"):
                    yield Label("読み仮名", classes="field_label")
                    yield Input(id="f_title_phonetic", classes="field_input")
                with Horizontal(classes="form_row"):
                    yield Label("親グループコード", classes="field_label")
                    yield Input(id="f_parent_tsv_code", classes="field_input")
                with Horizontal(classes="form_row"):
                    yield Label("備考", classes="field_label")
                    yield Input(id="f_note", classes="field_input")
                yield Label("", id="form_error", classes="error_label")
            with Horizontal(classes="dialog_buttons"):
                yield Button("  保存(S)  ", id="save_btn", classes="primary")
                yield Button("  キャンセル  ", id="cancel_btn")

    def on_mount(self):
        if self._tsv_code:
            session = database.SessionLocal()
            try:
                obj = session.query(BookGroup).get(self._tsv_code)
                if obj:
                    self.query_one("#f_tsv_code", Input).value = obj.tsv_code or ""
                    self.query_one("#f_tsv_code", Input).disabled = True
                    self.query_one("#f_title", Input).value = obj.title or ""
                    self.query_one("#f_title_phonetic", Input).value = obj.title_phonetic or ""
                    self.query_one("#f_parent_tsv_code", Input).value = obj.parent_tsv_code or ""
                    self.query_one("#f_note", Input).value = obj.note or ""
            finally:
                session.close()

    def action_dismiss_false(self):
        self.dismiss(False)

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "cancel_btn":
            self.dismiss(False)
        elif event.button.id == "save_btn":
            self._save()
        elif event.button.id == "auto_tsv_btn":
            self._auto_generate_tsv()

    def _auto_generate_tsv(self):
        try:
            result = generate_bg_code()
            self.query_one("#f_tsv_code", Input).value = result["tsv_code"]
            self.query_one("#form_error").update(
                f"✔ 採番: {result['tsv_code']}  S-TSV: {result['s_tsv_code']}"
            )
        except Exception as e:
            self.query_one("#form_error").update(f"✖ 自動採番エラー: {e}")

    def _save(self):
        tsv_code = self.query_one("#f_tsv_code", Input).value.strip()
        title = self.query_one("#f_title", Input).value.strip()
        if not title:
            self.query_one("#form_error").update("✖ グループ名は必須です。")
            return
        if tsv_code:
            ok, msg = validate_tsv_code(tsv_code)
            if not ok:
                self.query_one("#form_error").update(f"✖ TSVコード形式エラー: {msg}")
                return
        session = database.SessionLocal()
        try:
            if self._tsv_code:
                obj = session.query(BookGroup).get(self._tsv_code)
                obj.title = title
                obj.title_phonetic = self.query_one("#f_title_phonetic", Input).value.strip() or None
                obj.parent_tsv_code = self.query_one("#f_parent_tsv_code", Input).value.strip() or None
                obj.note = self.query_one("#f_note", Input).value.strip() or None
                obj.last_updated_timestamp = datetime.now(timezone.utc)
                log_change(session, self._tsv_code, "BookGroup", "更新", model_to_dict(obj))
                session.commit()
            else:
                if not tsv_code:
                    self.query_one("#form_error").update("✖ TSVコードは必須です。")
                    return
                obj = BookGroup(
                    tsv_code=tsv_code,
                    title=title,
                    title_phonetic=self.query_one("#f_title_phonetic", Input).value.strip() or None,
                    parent_tsv_code=self.query_one("#f_parent_tsv_code", Input).value.strip() or None,
                    note=self.query_one("#f_note", Input).value.strip() or None,
                )
                session.add(obj)
                log_change(session, tsv_code, "BookGroup", "追加", model_to_dict(obj))
                session.commit()
            self.dismiss(True)
        except Exception as e:
            session.rollback()
            self.query_one("#form_error").update(f"✖ {e}")
        finally:
            session.close()


# ─────────────────────────────────────────────
#  書籍管理タブ
# ─────────────────────────────────────────────

class BooksTab(Static):
    """書籍[BK] CRUD パネル"""

    def compose(self) -> ComposeResult:
        yield Static("─── 書籍管理 [BK] ────────────────────────────────", classes="section_label")
        with Horizontal(classes="button_row"):
            yield Button("🔍 一覧更新", id="bk_refresh")
            yield Button("➕ 新規追加", id="bk_add")
            yield Button("✏  編集", id="bk_edit")
            yield Button("🗑  削除", id="bk_delete", classes="danger")
            yield Button("📋 詳細", id="bk_detail")
        yield DataTable(id="bk_table")
        yield Label("", id="bk_status", classes="info_label")

    def on_mount(self):
        t = self.query_one("#bk_table", DataTable)
        t.add_columns("TSVコード", "書籍名", "著者", "出版社", "ISBN", "書架", "登録日時")
        t.cursor_type = "row"
        self._load_data()

    def _load_data(self):
        t = self.query_one("#bk_table", DataTable)
        t.clear()
        session = database.SessionLocal()
        try:
            rows = session.query(Book).order_by(Book.issued_timestamp.desc()).all()
            for r in rows:
                dt = r.issued_timestamp.strftime("%Y-%m-%d") if r.issued_timestamp else ""
                t.add_row(r.tsv_code or "", r.title or "", r.authors or "", r.publisher or "",
                          r.isbn or "", r.shelf_tsv_code or "", dt, key=r.tsv_code)
            self.query_one("#bk_status").update(f"✔ {len(rows)} 件")
        except Exception as e:
            self.query_one("#bk_status").update(f"エラー: {e}")
        finally:
            session.close()

    def _get_selected_key(self):
        t = self.query_one("#bk_table", DataTable)
        if t.cursor_row >= 0 and t.row_count > 0:
            return t.get_cell_at((t.cursor_row, 0))
        return None

    def on_button_pressed(self, event: Button.Pressed):
        btn_id = event.button.id
        if btn_id == "bk_refresh":
            self._load_data()
        elif btn_id == "bk_add":
            self.app.push_screen(BookFormDialog(None), lambda s: self._load_data() if s else None)
        elif btn_id == "bk_edit":
            key = self._get_selected_key()
            if key:
                self.app.push_screen(BookFormDialog(key), lambda s: self._load_data() if s else None)
            else:
                self.app.push_screen(MessageDialog("行を選択してください。", "警告", error=True))
        elif btn_id == "bk_delete":
            key = self._get_selected_key()
            if key:
                self.app.push_screen(ConfirmDialog(f"書籍「{key}」を削除しますか？", "削除確認"),
                    lambda ok: self._do_delete(key) if ok else None)
            else:
                self.app.push_screen(MessageDialog("行を選択してください。", "警告", error=True))
        elif btn_id == "bk_detail":
            key = self._get_selected_key()
            if key:
                session = database.SessionLocal()
                try:
                    obj = session.query(Book).get(key)
                    if obj:
                        self.app.push_screen(RecordDetailDialog(model_to_dict(obj), f"書籍詳細: {key}"))
                finally:
                    session.close()

    def _do_delete(self, key: str):
        session = database.SessionLocal()
        try:
            obj = session.query(Book).get(key)
            if obj:
                log_change(session, key, "Book", "削除", model_to_dict(obj))
                session.delete(obj)
                session.commit()
                self.app.push_screen(MessageDialog(f"削除しました: {key}", "完了"))
                self._load_data()
        except Exception as e:
            session.rollback()
            self.app.push_screen(MessageDialog(str(e), "エラー", error=True))
        finally:
            session.close()


class BookFormDialog(ModalScreen):
    BINDINGS = [Binding("escape", "dismiss_false", "キャンセル")]

    def __init__(self, tsv_code: Optional[str], **kwargs):
        super().__init__(**kwargs)
        self._tsv_code = tsv_code

    def compose(self) -> ComposeResult:
        title = f"書籍編集: {self._tsv_code}" if self._tsv_code else "書籍 新規追加"
        with Container(id="dialog"):
            yield Static(f"📖 {title}", id="dialog_title")
            with ScrollableContainer():
                with Horizontal(classes="form_row"):
                    yield Label("TSVコード", classes="field_label")
                    yield Input(placeholder="TSV-BK-...", id="f_tsv_code", classes="field_input")
                if not self._tsv_code:
                    with Horizontal(classes="form_row"):
                        yield Label("", classes="field_label")
                        yield Button("🎲 TSVコード自動採番 (ISBN優先)", id="auto_tsv_btn")
                for fid, label, ph in [
                    ("f_title",             "書籍名 *",      ""),
                    ("f_title_phonetic",    "読み仮名",      ""),
                    ("f_subtitle",          "サブタイトル",   ""),
                    ("f_authors",           "著者",          ""),
                    ("f_publisher",         "出版社",        ""),
                    ("f_published_date",    "出版日",        "YYYY-MM-DD"),
                    ("f_shelf_tsv_code",    "書架コード *",   "TSV-SH-..."),
                    ("f_bookgroup_tsv_code","書籍グループ",   "TSV-BG-...(任意)"),
                    ("f_isbn",              "ISBN",          "ISBN-13 or ISBN-10"),
                    ("f_price",             "価格",          "数値"),
                    ("f_c_code",            "Cコード",       ""),
                    ("f_size",              "サイズ",        ""),
                    ("f_note",              "備考",          ""),
                ]:
                    with Horizontal(classes="form_row"):
                        yield Label(label, classes="field_label")
                        yield Input(placeholder=ph, id=fid, classes="field_input")
                yield Label("", id="form_error", classes="error_label")
            with Horizontal(classes="dialog_buttons"):
                yield Button("  保存(S)  ", id="save_btn", classes="primary")
                yield Button("  キャンセル  ", id="cancel_btn")

    def _v(self, fid: str) -> str:
        return self.query_one(f"#{fid}", Input).value.strip()

    def on_mount(self):
        if self._tsv_code:
            session = database.SessionLocal()
            try:
                obj = session.query(Book).get(self._tsv_code)
                if obj:
                    fields = {
                        "f_tsv_code": obj.tsv_code, "f_title": obj.title,
                        "f_title_phonetic": obj.title_phonetic, "f_subtitle": obj.subtitle,
                        "f_authors": obj.authors, "f_publisher": obj.publisher,
                        "f_published_date": obj.published_date, "f_shelf_tsv_code": obj.shelf_tsv_code,
                        "f_bookgroup_tsv_code": obj.bookgroup_tsv_code, "f_isbn": obj.isbn,
                        "f_price": str(obj.price) if obj.price is not None else "",
                        "f_c_code": obj.c_code, "f_size": obj.size, "f_note": obj.note,
                    }
                    for fid, val in fields.items():
                        self.query_one(f"#{fid}", Input).value = val or ""
                    self.query_one("#f_tsv_code", Input).disabled = True
            finally:
                session.close()

    def action_dismiss_false(self):
        self.dismiss(False)

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "cancel_btn":
            self.dismiss(False)
        elif event.button.id == "save_btn":
            self._save()
        elif event.button.id == "auto_tsv_btn":
            self._auto_generate_tsv()

    def _auto_generate_tsv(self):
        """ISBNフィールドの内容に応じてTSVコードを自動採番する。

        ISBNが入力されていれば区分コード200/201、なければ202で採番する。
        """
        try:
            isbn = self._v("f_isbn")
            digits = isbn.replace("-", "").replace(" ", "")
            if len(digits) == 13 and digits.isdigit():
                result = generate_bk_code(isbn13=isbn)
                method = f"ISBN-13 → 区分コード {result['class_code']}"
            elif len(digits) == 10 and digits.isdigit():
                result = generate_bk_code(isbn10=isbn)
                method = f"ISBN-10 → 区分コード {result['class_code']}"
            else:
                result = generate_bk_code()
                method = f"自動採番 → 区分コード {result['class_code']}"
            self.query_one("#f_tsv_code", Input).value = result["tsv_code"]
            self.query_one("#form_error").update(
                f"✔ {method}: {result['tsv_code']}  S-TSV: {result['s_tsv_code']}"
            )
        except Exception as e:
            self.query_one("#form_error").update(f"✖ 自動採番エラー: {e}")

    def _save(self):
        tsv_code = self._v("f_tsv_code")
        title = self._v("f_title")
        shelf = self._v("f_shelf_tsv_code")
        if not title:
            self.query_one("#form_error").update("✖ 書籍名は必須です。")
            return
        if not shelf:
            self.query_one("#form_error").update("✖ 書架コードは必須です。")
            return
        if tsv_code:
            ok, msg = validate_tsv_code(tsv_code)
            if not ok:
                self.query_one("#form_error").update(f"✖ TSVコード形式エラー: {msg}")
                return
        price_str = self._v("f_price")
        try:
            price = float(price_str) if price_str else None
        except ValueError:
            self.query_one("#form_error").update("✖ 価格は数値で入力してください。")
            return

        session = database.SessionLocal()
        try:
            if self._tsv_code:
                obj = session.query(Book).get(self._tsv_code)
                obj.title = title
                obj.title_phonetic = self._v("f_title_phonetic") or None
                obj.subtitle = self._v("f_subtitle") or None
                obj.authors = self._v("f_authors") or None
                obj.publisher = self._v("f_publisher") or None
                obj.published_date = self._v("f_published_date") or None
                obj.shelf_tsv_code = shelf
                obj.bookgroup_tsv_code = self._v("f_bookgroup_tsv_code") or None
                obj.isbn = self._v("f_isbn") or None
                obj.price = price
                obj.c_code = self._v("f_c_code") or None
                obj.size = self._v("f_size") or None
                obj.note = self._v("f_note") or None
                obj.last_updated_timestamp = datetime.now(timezone.utc)
                log_change(session, self._tsv_code, "Book", "更新", model_to_dict(obj))
                session.commit()
            else:
                if not tsv_code:
                    self.query_one("#form_error").update("✖ TSVコードは必須です。")
                    return
                obj = Book(
                    tsv_code=tsv_code, title=title,
                    title_phonetic=self._v("f_title_phonetic") or None,
                    subtitle=self._v("f_subtitle") or None,
                    authors=self._v("f_authors") or None,
                    publisher=self._v("f_publisher") or None,
                    published_date=self._v("f_published_date") or None,
                    shelf_tsv_code=shelf,
                    bookgroup_tsv_code=self._v("f_bookgroup_tsv_code") or None,
                    isbn=self._v("f_isbn") or None,
                    price=price,
                    c_code=self._v("f_c_code") or None,
                    size=self._v("f_size") or None,
                    note=self._v("f_note") or None,
                )
                session.add(obj)
                log_change(session, tsv_code, "Book", "追加", model_to_dict(obj))
                session.commit()
            self.dismiss(True)
        except Exception as e:
            session.rollback()
            self.query_one("#form_error").update(f"✖ {e}")
        finally:
            session.close()


# ─────────────────────────────────────────────
#  記録資料管理タブ
# ─────────────────────────────────────────────

class RecordsTab(Static):
    """記録資料[RE] CRUD パネル"""

    def compose(self) -> ComposeResult:
        yield Static("─── 記録資料管理 [RE] ────────────────────────────", classes="section_label")
        with Horizontal(classes="button_row"):
            yield Button("🔍 一覧更新", id="re_refresh")
            yield Button("➕ 新規追加", id="re_add")
            yield Button("✏  編集", id="re_edit")
            yield Button("🗑  削除", id="re_delete", classes="danger")
            yield Button("📋 詳細", id="re_detail")
        yield DataTable(id="re_table")
        yield Label("", id="re_status", classes="info_label")

    def on_mount(self):
        t = self.query_one("#re_table", DataTable)
        t.add_columns("TSVコード", "資料名", "種別", "発行日", "発行者", "書架", "登録日時")
        t.cursor_type = "row"
        self._load_data()

    def _load_data(self):
        t = self.query_one("#re_table", DataTable)
        t.clear()
        session = database.SessionLocal()
        try:
            rows = session.query(Record).order_by(Record.issued_timestamp.desc()).all()
            for r in rows:
                dt = r.issued_timestamp.strftime("%Y-%m-%d") if r.issued_timestamp else ""
                t.add_row(r.tsv_code or "", r.title or "", r.record_type or "",
                          r.document_date or "", r.issuer_tsv_code or "",
                          r.shelf_tsv_code or "", dt, key=r.tsv_code)
            self.query_one("#re_status").update(f"✔ {len(rows)} 件")
        except Exception as e:
            self.query_one("#re_status").update(f"エラー: {e}")
        finally:
            session.close()

    def _get_selected_key(self):
        t = self.query_one("#re_table", DataTable)
        if t.cursor_row >= 0 and t.row_count > 0:
            return t.get_cell_at((t.cursor_row, 0))
        return None

    def on_button_pressed(self, event: Button.Pressed):
        btn_id = event.button.id
        if btn_id == "re_refresh":
            self._load_data()
        elif btn_id == "re_add":
            self.app.push_screen(RecordFormDialog(None), lambda s: self._load_data() if s else None)
        elif btn_id == "re_edit":
            key = self._get_selected_key()
            if key:
                self.app.push_screen(RecordFormDialog(key), lambda s: self._load_data() if s else None)
            else:
                self.app.push_screen(MessageDialog("行を選択してください。", "警告", error=True))
        elif btn_id == "re_delete":
            key = self._get_selected_key()
            if key:
                self.app.push_screen(ConfirmDialog(f"資料「{key}」を削除しますか？", "削除確認"),
                    lambda ok: self._do_delete(key) if ok else None)
            else:
                self.app.push_screen(MessageDialog("行を選択してください。", "警告", error=True))
        elif btn_id == "re_detail":
            key = self._get_selected_key()
            if key:
                session = database.SessionLocal()
                try:
                    obj = session.query(Record).get(key)
                    if obj:
                        self.app.push_screen(RecordDetailDialog(model_to_dict(obj), f"資料詳細: {key}"))
                finally:
                    session.close()

    def _do_delete(self, key: str):
        session = database.SessionLocal()
        try:
            obj = session.query(Record).get(key)
            if obj:
                log_change(session, key, "Record", "削除", model_to_dict(obj))
                session.delete(obj)
                session.commit()
                self.app.push_screen(MessageDialog(f"削除しました: {key}", "完了"))
                self._load_data()
        except Exception as e:
            session.rollback()
            self.app.push_screen(MessageDialog(str(e), "エラー", error=True))
        finally:
            session.close()


class RecordFormDialog(ModalScreen):
    BINDINGS = [Binding("escape", "dismiss_false", "キャンセル")]

    def __init__(self, tsv_code: Optional[str], **kwargs):
        super().__init__(**kwargs)
        self._tsv_code = tsv_code

    def compose(self) -> ComposeResult:
        title = f"資料編集: {self._tsv_code}" if self._tsv_code else "記録資料 新規追加"
        with Container(id="dialog"):
            yield Static(f"📄 {title}", id="dialog_title")
            with ScrollableContainer():
                with Horizontal(classes="form_row"):
                    yield Label("TSVコード", classes="field_label")
                    yield Input(placeholder="TSV-RE-...", id="f_tsv_code", classes="field_input")
                if not self._tsv_code:
                    with Horizontal(classes="form_row"):
                        yield Label("", classes="field_label")
                        yield Button("🎲 TSVコード自動採番 (発行者必須)", id="auto_tsv_btn")
                for fid, label, ph in [
                    ("f_title",              "資料名 *",       ""),
                    ("f_title_phonetic",     "読み仮名",       ""),
                    ("f_record_type",        "資料種別 *",     "例: 証明書 / 契約書"),
                    ("f_issuer_tsv_code",    "発行者コード *", "TSV-IS-..."),
                    ("f_shelf_tsv_code",     "書架コード *",   "TSV-SH-..."),
                    ("f_document_date",      "発行・有効日",   "YYYY-MM-DD"),
                    ("f_record_period_start","保管期間（開始）","YYYY-MM-DD"),
                    ("f_record_period_end",  "保管期間（終了）","YYYY-MM-DD"),
                    ("f_record_finished",    "保管終了フラグ", "1 or 空"),
                    ("f_parent_tsv_code",    "親資料コード",   "TSV-RE-...(任意)"),
                    ("f_note",               "備考",           ""),
                ]:
                    with Horizontal(classes="form_row"):
                        yield Label(label, classes="field_label")
                        yield Input(placeholder=ph, id=fid, classes="field_input")
                yield Label("", id="form_error", classes="error_label")
            with Horizontal(classes="dialog_buttons"):
                yield Button("  保存(S)  ", id="save_btn", classes="primary")
                yield Button("  キャンセル  ", id="cancel_btn")

    def _v(self, fid: str) -> str:
        return self.query_one(f"#{fid}", Input).value.strip()

    def on_mount(self):
        if self._tsv_code:
            session = database.SessionLocal()
            try:
                obj = session.query(Record).get(self._tsv_code)
                if obj:
                    fields = {
                        "f_tsv_code": obj.tsv_code, "f_title": obj.title,
                        "f_title_phonetic": obj.title_phonetic, "f_record_type": obj.record_type,
                        "f_issuer_tsv_code": obj.issuer_tsv_code, "f_shelf_tsv_code": obj.shelf_tsv_code,
                        "f_document_date": obj.document_date, "f_record_period_start": obj.record_period_start,
                        "f_record_period_end": obj.record_period_end, "f_record_finished": obj.record_finished,
                        "f_parent_tsv_code": obj.parent_tsv_code, "f_note": obj.note,
                    }
                    for fid, val in fields.items():
                        self.query_one(f"#{fid}", Input).value = val or ""
                    self.query_one("#f_tsv_code", Input).disabled = True
            finally:
                session.close()

    def action_dismiss_false(self):
        self.dismiss(False)

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "cancel_btn":
            self.dismiss(False)
        elif event.button.id == "save_btn":
            self._save()
        elif event.button.id == "auto_tsv_btn":
            self._auto_generate_tsv()

    def _auto_generate_tsv(self):
        """発行者コードをもとにTSV-REコードを自動採番する。"""
        try:
            issuer = self._v("f_issuer_tsv_code")
            if not issuer:
                self.query_one("#form_error").update(
                    "✖ 発行者コードを先に入力してください。"
                )
                return
            result = generate_re_code(issuer)
            self.query_one("#f_tsv_code", Input).value = result["tsv_code"]
            self.query_one("#form_error").update(
                f"✔ 採番: {result['tsv_code']}  "
                f"発行者番号={result['issuer_number']} 資料番号={result['doc_number']}  "
                f"S-TSV: {result['s_tsv_code']}"
            )
        except Exception as e:
            self.query_one("#form_error").update(f"✖ 自動採番エラー: {e}")

    def _save(self):
        tsv_code = self._v("f_tsv_code")
        title = self._v("f_title")
        record_type = self._v("f_record_type")
        shelf = self._v("f_shelf_tsv_code")
        # 発行者は入力値を優先し、空ならデフォルト発行者（§2.2.4.2）
        issuer = self._v("f_issuer_tsv_code") or "TSV-IS-215-0001-00001-6"

        if not title:
            self.query_one("#form_error").update("✖ 資料名は必須です。")
            return
        if not record_type:
            self.query_one("#form_error").update("✖ 資料種別は必須です。")
            return
        if not shelf:
            self.query_one("#form_error").update("✖ 書架コードは必須です。")
            return
        if tsv_code:
            ok, msg = validate_tsv_code(tsv_code)
            if not ok:
                self.query_one("#form_error").update(f"✖ TSVコード形式エラー: {msg}")
                return

        session = database.SessionLocal()
        try:
            if self._tsv_code:
                obj = session.query(Record).get(self._tsv_code)
                obj.title = title
                obj.title_phonetic = self._v("f_title_phonetic") or None
                obj.record_type = record_type
                obj.issuer_tsv_code = issuer
                obj.shelf_tsv_code = shelf
                obj.document_date = self._v("f_document_date") or None
                obj.record_period_start = self._v("f_record_period_start") or None
                obj.record_period_end = self._v("f_record_period_end") or None
                obj.record_finished = self._v("f_record_finished") or None
                obj.parent_tsv_code = self._v("f_parent_tsv_code") or None
                obj.note = self._v("f_note") or None
                obj.last_updated_timestamp = datetime.now(timezone.utc)
                log_change(session, self._tsv_code, "Record", "更新", model_to_dict(obj))
                session.commit()
            else:
                if not tsv_code:
                    self.query_one("#form_error").update("✖ TSVコードは必須です。")
                    return
                obj = Record(
                    tsv_code=tsv_code, title=title,
                    title_phonetic=self._v("f_title_phonetic") or None,
                    record_type=record_type, issuer_tsv_code=issuer,
                    shelf_tsv_code=shelf,
                    document_date=self._v("f_document_date") or None,
                    record_period_start=self._v("f_record_period_start") or None,
                    record_period_end=self._v("f_record_period_end") or None,
                    record_finished=self._v("f_record_finished") or None,
                    parent_tsv_code=self._v("f_parent_tsv_code") or None,
                    note=self._v("f_note") or None,
                )
                session.add(obj)
                log_change(session, tsv_code, "Record", "追加", model_to_dict(obj))
                session.commit()
            self.dismiss(True)
        except Exception as e:
            session.rollback()
            self.query_one("#form_error").update(f"✖ {e}")
        finally:
            session.close()


# ─────────────────────────────────────────────
#  変更履歴タブ
# ─────────────────────────────────────────────

class HistoryTab(Static):
    """変更履歴 表示パネル"""

    def compose(self) -> ComposeResult:
        yield Static("─── 変更履歴 ─────────────────────────────────────", classes="section_label")
        with Horizontal(classes="button_row"):
            yield Button("🔍 一覧更新", id="hist_refresh")
            yield Button("🗑  全削除", id="hist_clear", classes="danger")
        yield DataTable(id="hist_table")
        yield Label("", id="hist_status", classes="info_label")

    def on_mount(self):
        t = self.query_one("#hist_table", DataTable)
        t.add_columns("変更ID", "TSVコード", "レコード種別", "変更種別", "変更日時")
        t.cursor_type = "row"
        self._load_data()

    def _load_data(self):
        t = self.query_one("#hist_table", DataTable)
        t.clear()
        session = database.SessionLocal()
        try:
            rows = session.query(ChangeHistory).order_by(ChangeHistory.changed_timestamp.desc()).limit(200).all()
            for r in rows:
                dt = r.changed_timestamp.strftime("%Y-%m-%d %H:%M") if r.changed_timestamp else ""
                t.add_row(str(r.change_id), r.tsv_code or "", r.record_type or "", r.change_type or "", dt, key=str(r.change_id))
            self.query_one("#hist_status").update(f"✔ {len(rows)} 件（最新200件）")
        except Exception as e:
            self.query_one("#hist_status").update(f"エラー: {e}")
        finally:
            session.close()

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "hist_refresh":
            self._load_data()
        elif event.button.id == "hist_clear":
            self.app.push_screen(ConfirmDialog("変更履歴を全て削除しますか？", "履歴全削除"),
                lambda ok: self._do_clear() if ok else None)

    def _do_clear(self):
        session = database.SessionLocal()
        try:
            session.query(ChangeHistory).delete()
            session.commit()
            self._load_data()
            self.app.push_screen(MessageDialog("変更履歴を全て削除しました。", "完了"))
        except Exception as e:
            session.rollback()
            self.app.push_screen(MessageDialog(str(e), "エラー", error=True))
        finally:
            session.close()


# ─────────────────────────────────────────────
#  メインアプリケーション
# ─────────────────────────────────────────────

class TSVManagerApp(App):
    """TSV データベース管理 - Windows XP 風 TUI"""

    TITLE = "TSVデータベース管理システム"
    CSS = XP_CSS
    BINDINGS = [
        Binding("ctrl+q", "quit", "終了"),
        Binding("f5", "refresh_all", "全更新"),
    ]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Container(id="main_panel"):
            yield Static("📁 TSVデータベース管理システム  v1.0", id="titlebar")
            with TabbedContent():
                with TabPane("🗄 書架 [SH]", id="tab_shelves"):
                    yield ShelvesTab()
                with TabPane("🏢 発行者 [IS]", id="tab_issuers"):
                    yield IssuersTab()
                with TabPane("📚 書籍グループ [BG]", id="tab_bookgroups"):
                    yield BookGroupsTab()
                with TabPane("📖 書籍 [BK]", id="tab_books"):
                    yield BooksTab()
                with TabPane("📄 記録資料 [RE]", id="tab_records"):
                    yield RecordsTab()
                with TabPane("📜 変更履歴", id="tab_history"):
                    yield HistoryTab()
            yield Static("F5:更新  Ctrl+Q:終了  Tab:タブ切替  ↑↓:行選択  Enter:選択確定", id="status_bar")
        yield Footer()

    def action_refresh_all(self):
        pass  # 各タブの一覧更新ボタンで対応

    def on_mount(self):
        self.notify("TSVデータベース管理システムへようこそ。", title="起動完了")


# ─────────────────────────────────────────────
#  エントリポイント
# ─────────────────────────────────────────────

if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    init_db()
    app = TSVManagerApp()
    app.run()
