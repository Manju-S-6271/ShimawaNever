"""
export_book_html.py
====================
SQLAlchemy の Book オブジェクト（または Book のリスト）を
デザインされた HTML ファイルとして出力するスクリプト。

使い方:
    from export_book_html import export_books_to_html

    # 単一オブジェクト
    export_books_to_html(book)

    # リスト
    export_books_to_html([book1, book2, ...], output_path="output.html")
"""

from __future__ import annotations

import html
import os
from datetime import datetime, timezone
from decimal import Decimal
from typing import Union

# ---------------------------------------------------------------------------
# 型ヒント用（実行環境に SQLAlchemy がなくても import エラーにならないよう
# TYPE_CHECKING ガードを使う）
# ---------------------------------------------------------------------------
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from models import Book  # 実際のモデルパスに合わせて変更


# ============================================================
# ヘルパー
# ============================================================

def _esc(value) -> str:
    """None を空文字に変換し、HTML エスケープを適用する。"""
    if value is None:
        return ""
    return html.escape(str(value))


def _fmt_price(price) -> str:
    if price is None:
        return ""
    try:
        return f"¥{Decimal(str(price)):,.0f}"
    except Exception:
        return str(price)


def _fmt_datetime(dt) -> str:
    if dt is None:
        return ""
    if isinstance(dt, datetime):
        # UTC → JST (UTC+9)
        if dt.tzinfo is not None:
            from datetime import timedelta
            jst = timezone(timedelta(hours=9))
            dt = dt.astimezone(jst)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    return str(dt)


def _book_to_dict(book) -> dict:
    """Book インスタンスをテンプレート用の辞書に変換する。"""

    def rel_str(obj, attr: str) -> str:
        """リレーション先オブジェクトの属性を安全に取得する。"""
        try:
            rel = getattr(book, obj, None)
            if rel is None:
                return ""
            return _esc(getattr(rel, attr, ""))
        except Exception:
            return ""

    return {
        "tsv_code":             _esc(book.tsv_code),
        "title":                _esc(book.title),
        "title_phonetic":       _esc(book.title_phonetic),
        "subtitle":             _esc(book.subtitle),
        "authors":              _esc(book.authors),
        "publisher":            _esc(book.publisher),
        "isbn":                 _esc(book.isbn),
        "book_jan":             _esc(book.book_jan),
        "c_code":               _esc(book.c_code),
        "target":               _esc(book.target),
        "form":                 _esc(book.form),
        "content":              _esc(book.content),
        "price":                _fmt_price(book.price),
        "size":                 _esc(book.size),
        "stock_finished":       _esc(book.stock_finished),
        "note":                 _esc(book.note),
        "issued_timestamp":     _fmt_datetime(book.issued_timestamp),
        "last_updated_timestamp": _fmt_datetime(book.last_updated_timestamp),
        # 外部キー (生の値)
        "bookgroup_tsv_code":   _esc(book.bookgroup_tsv_code),
        "parent_tsv_code":      _esc(book.parent_tsv_code),
        "shelf_tsv_code":       _esc(book.shelf_tsv_code),
        # リレーション先
        "book_group_name":      rel_str("book_group", "name"),
        "shelf_name":           rel_str("shelf", "name"),
        "parent_title":         rel_str("parent", "title"),
    }


# ============================================================
# カード HTML 生成
# ============================================================

def _render_card(d: dict, index: int) -> str:
    """1冊分のカード HTML を生成する。"""

    def row(label: str, value: str, mono: bool = False) -> str:
        if not value:
            return ""
        cls = ' class="mono"' if mono else ''
        return (
            f'<tr>'
            f'<th>{label}</th>'
            f'<td{cls}>{value}</td>'
            f'</tr>'
        )

    def badge(value: str, kind: str = "default") -> str:
        if not value:
            return ""
        return f'<span class="badge badge-{kind}">{value}</span>'

    stock_badge = (
        badge("在架終了", "danger") if d["stock_finished"] else badge("在架中", "ok")
    )

    table_rows = "".join([
        row("TSVコード",       d["tsv_code"],              mono=True),
        row("読み仮名",        d["title_phonetic"]),
        row("サブタイトル",     d["subtitle"]),
        row("著者",            d["authors"]),
        row("出版社",          d["publisher"]),
        row("書架",            d["shelf_name"] or d["shelf_tsv_code"],    mono=not d["shelf_name"]),
        row("書籍グループ",     d["book_group_name"] or d["bookgroup_tsv_code"]),
        row("親書籍",          d["parent_title"] or d["parent_tsv_code"]),
        row("ISBN",            d["isbn"],                  mono=True),
        row("JANコード",       d["book_jan"],              mono=True),
        row("Cコード",         d["c_code"],                mono=True),
        row("対象",            d["target"]),
        row("形態",            d["form"]),
        row("内容",            d["content"]),
        row("価格",            d["price"]),
        row("サイズ",          d["size"]),
        row("備考",            d["note"]),
        row("登録日時",        d["issued_timestamp"],      mono=True),
        row("最終更新日時",     d["last_updated_timestamp"], mono=True),
    ])

    return f"""
    <article class="book-card" style="animation-delay:{index * 0.06:.2f}s">
      <header class="card-header">
        <div class="card-index">#{index + 1:03d}</div>
        <div class="card-title-block">
          <h2 class="card-title">{d['title'] or '(タイトル未設定)'}</h2>
          {f'<p class="card-authors">{d["authors"]}</p>' if d["authors"] else ''}
        </div>
        <div class="card-badges">{stock_badge}</div>
      </header>
      <div class="card-body">
        <table class="info-table">
          <tbody>
            {table_rows}
          </tbody>
        </table>
      </div>
    </article>
"""


# ============================================================
# ページ全体の HTML 生成
# ============================================================

def _render_page(books_data: list[dict], generated_at: str) -> str:
    cards_html = "\n".join(
        _render_card(d, i) for i, d in enumerate(books_data)
    )
    count = len(books_data)

    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>書籍一覧レポート</title>
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Noto+Serif+JP:wght@300;400;600;700&family=DM+Mono:wght@300;400;500&family=Playfair+Display:wght@700;900&display=swap" rel="stylesheet" />
  <style>
    /* ======================================================
       Design Token
    ====================================================== */
    :root {{
      --bg:          #0e0e0f;
      --surface:     #16161a;
      --surface-hi:  #1e1e24;
      --border:      #2a2a33;
      --accent:      #c9a84c;
      --accent-dim:  #8a6e2e;
      --ok:          #4caf7d;
      --danger:      #d16060;
      --text-primary:#e8e6df;
      --text-muted:  #7a7870;
      --text-label:  #9b9890;
      --mono:        'DM Mono', monospace;
      --serif:       'Noto Serif JP', serif;
      --display:     'Playfair Display', serif;
      --radius:      4px;
      --card-w:      780px;
    }}

    /* ======================================================
       Reset & Base
    ====================================================== */
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

    html {{
      font-size: 14px;
      background: var(--bg);
      color: var(--text-primary);
      font-family: var(--serif);
    }}

    body {{
      min-height: 100vh;
      padding: 0;
    }}

    /* ======================================================
       Page Header
    ====================================================== */
    .page-header {{
      position: relative;
      background: var(--surface);
      border-bottom: 1px solid var(--border);
      padding: 56px 40px 40px;
      overflow: hidden;
    }}

    .page-header::before {{
      content: '';
      position: absolute;
      inset: 0;
      background:
        repeating-linear-gradient(
          0deg,
          transparent,
          transparent 39px,
          var(--border) 39px,
          var(--border) 40px
        ),
        repeating-linear-gradient(
          90deg,
          transparent,
          transparent 39px,
          var(--border) 39px,
          var(--border) 40px
        );
      opacity: 0.3;
    }}

    .page-header::after {{
      content: '';
      position: absolute;
      top: 0; left: 0; right: 0;
      height: 3px;
      background: linear-gradient(90deg, var(--accent), var(--accent-dim), transparent);
    }}

    .header-inner {{
      position: relative;
      max-width: var(--card-w);
      margin: 0 auto;
    }}

    .header-eyebrow {{
      font-family: var(--mono);
      font-size: 10px;
      letter-spacing: 0.3em;
      color: var(--accent);
      text-transform: uppercase;
      margin-bottom: 16px;
    }}

    .header-title {{
      font-family: var(--display);
      font-size: clamp(28px, 5vw, 44px);
      font-weight: 900;
      color: var(--text-primary);
      line-height: 1.1;
      letter-spacing: -0.02em;
    }}

    .header-meta {{
      margin-top: 20px;
      display: flex;
      gap: 32px;
      flex-wrap: wrap;
      align-items: center;
    }}

    .meta-item {{
      display: flex;
      flex-direction: column;
      gap: 2px;
    }}

    .meta-label {{
      font-family: var(--mono);
      font-size: 9px;
      letter-spacing: 0.2em;
      color: var(--text-muted);
      text-transform: uppercase;
    }}

    .meta-value {{
      font-family: var(--mono);
      font-size: 13px;
      color: var(--accent);
    }}

    /* ======================================================
       Search / Filter Bar
    ====================================================== */
    .toolbar {{
      position: sticky;
      top: 0;
      z-index: 100;
      background: rgba(14,14,15,0.92);
      backdrop-filter: blur(12px);
      border-bottom: 1px solid var(--border);
      padding: 10px 40px;
    }}

    .toolbar-inner {{
      max-width: var(--card-w);
      margin: 0 auto;
      display: flex;
      gap: 12px;
      align-items: center;
    }}

    .search-box {{
      flex: 1;
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      padding: 8px 14px;
      font-family: var(--mono);
      font-size: 12px;
      color: var(--text-primary);
      outline: none;
      transition: border-color 0.2s;
    }}
    .search-box::placeholder {{ color: var(--text-muted); }}
    .search-box:focus {{ border-color: var(--accent); }}

    .result-count {{
      font-family: var(--mono);
      font-size: 11px;
      color: var(--text-muted);
      white-space: nowrap;
    }}
    .result-count span {{ color: var(--accent); }}

    /* ======================================================
       Main Content
    ====================================================== */
    .main {{
      max-width: var(--card-w);
      margin: 0 auto;
      padding: 40px 40px 80px;
      display: flex;
      flex-direction: column;
      gap: 24px;
    }}

    /* ======================================================
       Book Card
    ====================================================== */
    @keyframes slide-in {{
      from {{ opacity: 0; transform: translateY(16px); }}
      to   {{ opacity: 1; transform: translateY(0); }}
    }}

    .book-card {{
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      overflow: hidden;
      animation: slide-in 0.4s ease both;
      transition: border-color 0.2s, box-shadow 0.2s;
    }}

    .book-card:hover {{
      border-color: var(--accent-dim);
      box-shadow: 0 0 0 1px var(--accent-dim), 0 8px 32px rgba(0,0,0,0.5);
    }}

    .book-card.hidden {{ display: none; }}

    /* Card Header */
    .card-header {{
      display: grid;
      grid-template-columns: 48px 1fr auto;
      gap: 16px;
      align-items: start;
      padding: 20px 24px 16px;
      border-bottom: 1px solid var(--border);
      background: var(--surface-hi);
    }}

    .card-index {{
      font-family: var(--mono);
      font-size: 10px;
      color: var(--text-muted);
      padding-top: 6px;
      letter-spacing: 0.05em;
    }}

    .card-title-block {{
      display: flex;
      flex-direction: column;
      gap: 4px;
    }}

    .card-title {{
      font-family: var(--serif);
      font-size: 17px;
      font-weight: 700;
      color: var(--text-primary);
      line-height: 1.4;
    }}

    .card-authors {{
      font-size: 12px;
      color: var(--text-muted);
    }}

    .card-badges {{
      display: flex;
      gap: 6px;
      flex-wrap: wrap;
      justify-content: flex-end;
      padding-top: 4px;
    }}

    /* Card Body */
    .card-body {{
      padding: 0;
    }}

    /* Info Table */
    .info-table {{
      width: 100%;
      border-collapse: collapse;
    }}

    .info-table tr {{
      border-bottom: 1px solid var(--border);
      transition: background 0.15s;
    }}
    .info-table tr:last-child {{ border-bottom: none; }}
    .info-table tr:hover {{ background: var(--surface-hi); }}

    .info-table th {{
      width: 140px;
      padding: 9px 16px 9px 24px;
      font-family: var(--mono);
      font-size: 10px;
      font-weight: 400;
      letter-spacing: 0.08em;
      color: var(--text-label);
      text-align: left;
      text-transform: uppercase;
      vertical-align: top;
      white-space: nowrap;
    }}

    .info-table td {{
      padding: 9px 24px 9px 0;
      font-size: 13px;
      color: var(--text-primary);
      line-height: 1.6;
      vertical-align: top;
      word-break: break-all;
    }}

    .info-table td.mono {{
      font-family: var(--mono);
      font-size: 11px;
      color: var(--accent);
      letter-spacing: 0.05em;
    }}

    /* ======================================================
       Badge
    ====================================================== */
    .badge {{
      display: inline-block;
      padding: 2px 8px;
      border-radius: 2px;
      font-family: var(--mono);
      font-size: 10px;
      letter-spacing: 0.08em;
      text-transform: uppercase;
    }}
    .badge-ok     {{ background: rgba(76,175,125,0.15); color: var(--ok);     border: 1px solid rgba(76,175,125,0.3); }}
    .badge-danger {{ background: rgba(209, 96, 96,0.15); color: var(--danger); border: 1px solid rgba(209,96,96,0.3); }}
    .badge-default{{ background: var(--surface-hi); color: var(--text-muted); border: 1px solid var(--border); }}

    /* ======================================================
       Empty State
    ====================================================== */
    .empty-state {{
      text-align: center;
      padding: 80px 0;
      color: var(--text-muted);
      font-family: var(--mono);
      font-size: 12px;
      letter-spacing: 0.2em;
      display: none;
    }}

    /* ======================================================
       Page Footer
    ====================================================== */
    .page-footer {{
      border-top: 1px solid var(--border);
      padding: 20px 40px;
      text-align: center;
      font-family: var(--mono);
      font-size: 10px;
      color: var(--text-muted);
      letter-spacing: 0.15em;
    }}

    /* ======================================================
       Responsive
    ====================================================== */
    @media (max-width: 600px) {{
      .page-header, .toolbar, .main {{ padding-left: 16px; padding-right: 16px; }}
      .info-table th {{ width: 100px; font-size: 9px; }}
      .card-header {{ grid-template-columns: 36px 1fr; }}
      .card-badges {{ grid-column: 1 / -1; justify-content: flex-start; }}
    }}
  </style>
</head>
<body>

  <!-- ===== Page Header ===== -->
  <header class="page-header">
    <div class="header-inner">
      <p class="header-eyebrow">Library Management System</p>
      <h1 class="header-title">書籍一覧レポート</h1>
      <div class="header-meta">
        <div class="meta-item">
          <span class="meta-label">Total</span>
          <span class="meta-value" id="total-count">{count}</span>
        </div>
        <div class="meta-item">
          <span class="meta-label">Generated</span>
          <span class="meta-value">{generated_at}</span>
        </div>
      </div>
    </div>
  </header>

  <!-- ===== Toolbar ===== -->
  <div class="toolbar">
    <div class="toolbar-inner">
      <input
        class="search-box"
        type="search"
        id="search-input"
        placeholder="タイトル・著者・ISBN・TSVコード などで絞り込み…"
        aria-label="絞り込み検索"
      />
      <p class="result-count" id="result-count">
        <span id="result-num">{count}</span> 件表示
      </p>
    </div>
  </div>

  <!-- ===== Main ===== -->
  <main class="main" id="book-list">
    {cards_html}
    <p class="empty-state" id="empty-state">— 該当する書籍がありません —</p>
  </main>

  <!-- ===== Footer ===== -->
  <footer class="page-footer">
    LIBRARY MANAGEMENT SYSTEM &nbsp;·&nbsp; BOOK EXPORT &nbsp;·&nbsp; {generated_at}
  </footer>

  <!-- ===== Search Script ===== -->
  <script>
    (function () {{
      const input  = document.getElementById('search-input');
      const cards  = Array.from(document.querySelectorAll('.book-card'));
      const numEl  = document.getElementById('result-num');
      const empty  = document.getElementById('empty-state');

      input.addEventListener('input', function () {{
        const q = this.value.trim().toLowerCase();
        let visible = 0;

        cards.forEach(function (card) {{
          const text = card.textContent.toLowerCase();
          const match = !q || text.includes(q);
          card.classList.toggle('hidden', !match);
          if (match) visible++;
        }});

        numEl.textContent = visible;
        empty.style.display = visible === 0 ? 'block' : 'none';
      }});
    }})();
  </script>

</body>
</html>
"""


# ============================================================
# 公開 API
# ============================================================

def export_books_to_html(
    books,
    output_path: str = "books_export.html",
) -> str:
    """
    Book オブジェクト（単体またはリスト）を HTML ファイルに書き出す。

    Parameters
    ----------
    books : Book | list[Book]
        SQLAlchemy の Book インスタンス、またはそのリスト。
    output_path : str
        出力先ファイルパス（デフォルト: "books_export.html"）。

    Returns
    -------
    str
        書き出したファイルの絶対パス。
    """
    if not isinstance(books, (list, tuple)):
        books = [books]

    books_data = [_book_to_dict(b) for b in books]

    now_jst = datetime.now(timezone.utc).astimezone(
        __import__("datetime").timezone(
            __import__("datetime").timedelta(hours=9)
        )
    )
    generated_at = now_jst.strftime("%Y-%m-%d %H:%M JST")

    html_content = _render_page(books_data, generated_at)

    abs_path = os.path.abspath(output_path)
    with open(abs_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"[export] {len(books_data)} 冊を書き出しました → {abs_path}")
    return abs_path


# ============================================================
# デモ実行（スタンドアロンでの動作確認用）
# ============================================================

# if __name__ == "__main__":
#     from decimal import Decimal
#     from datetime import datetime, timezone

#     class _FakeRelation:
#         def __init__(self, name): self.name = name; self.title = name

#     class _FakeBook:
#         def __init__(self, **kwargs):
#             for k, v in kwargs.items():
#                 setattr(self, k, v)

#     sample_books = [
#         _FakeBook(
#             tsv_code="BK-2024-00001",
#             bookgroup_tsv_code="BKG-001",
#             parent_tsv_code=None,
#             title="SQLAlchemy 実践入門",
#             title_phonetic="えすきゅーえるあるけみーじっせんにゅうもん",
#             subtitle="Python ORM の設計と運用",
#             authors="山田 太郎",
#             publisher="技術評論社",
#             shelf_tsv_code="SH-001",
#             isbn="978-4-297-00001-0",
#             book_jan="9784297000010",
#             c_code="C3055",
#             target="専門",
#             form="単行本",
#             content="プログラミング",
#             price=Decimal("3200"),
#             size="A5",
#             stock_finished=None,
#             note="人気書籍・複数在庫あり",
#             issued_timestamp=datetime(2024, 4, 1, 0, 0, 0, tzinfo=timezone.utc),
#             last_updated_timestamp=datetime(2024, 11, 20, 12, 30, 0, tzinfo=timezone.utc),
#             book_group=_FakeRelation("Python 関連書籍グループ"),
#             shelf=_FakeRelation("3F-技術書架-A"),
#             parent=None,
#         ),
#         _FakeBook(
#             tsv_code="BK-2024-00002",
#             bookgroup_tsv_code=None,
#             parent_tsv_code=None,
#             title="データベース設計の基礎",
#             title_phonetic="でーたべーすせっけいのきそ",
#             subtitle=None,
#             authors="鈴木 花子, 田中 一郎",
#             publisher="オーム社",
#             shelf_tsv_code="SH-002",
#             isbn="978-4-274-00002-5",
#             book_jan="9784274000025",
#             c_code="C3055",
#             target="一般",
#             form="単行本",
#             content="コンピュータ",
#             price=Decimal("2800"),
#             size="B5",
#             stock_finished="1",
#             note=None,
#             issued_timestamp=datetime(2023, 9, 15, 0, 0, 0, tzinfo=timezone.utc),
#             last_updated_timestamp=datetime(2024, 1, 5, 8, 0, 0, tzinfo=timezone.utc),
#             book_group=None,
#             shelf=_FakeRelation("2F-参考書架-B"),
#             parent=None,
#         ),
#     ]

#     export_books_to_html(sample_books, output_path="books_export.html")

# ============================================================
# デモ実行用 2 （実際のデータベースから取得して出力）
# ============================================================

if __name__ == "__main__":
    import database
    from models import Book

    with database.SessionLocal() as session:
        books_list = session.query(Book).order_by(Book.last_updated_timestamp.desc()).all()
    
    export_books_to_html(books_list, output_path="books_export.html")