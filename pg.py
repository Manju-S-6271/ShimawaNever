import os
from datetime import datetime
import database
from models import Book

def generate_html_report(books, output_filename="book_report.html"):
    """
    SQLAlchemyのBookオブジェクトを、デザインされたHTMLファイルとして出力する
    """
    
    # テーブル行の生成
    table_rows = ""
    for book in books:
        # 価格のフォーマット
        price_display = f"¥{book.price:,.0f}" if book.price else "-"
        # 日時のフォーマット
        updated_at = book.last_updated_timestamp.strftime('%Y-%m-%d %H:%M') if book.last_updated_timestamp else "-"
        
        table_rows += f"""
        <tr>
            <td class="code">{book.tsv_code or ''}</td>
            <td class="title">
                <strong>{book.title or ''}</strong>
                <div class="subtitle">{book.subtitle or ''}</div>
            </td>
            <td>{book.authors or ''}</td>
            <td>{book.publisher or ''}</td>
            <td>{book.isbn or ''}</td>
            <td class="center">{book.shelf_tsv_code or ''}</td>
            <td class="price">{price_display}</td>
            <td class="date">{updated_at}</td>
        </tr>
        """

    # HTMLテンプレート
    html_content = f"""
    <!DOCTYPE html>
    <html lang="ja">
    <head>
        <meta charset="UTF-8">
        <title>蔵書レポート - {datetime.now().strftime('%Y%m%d')}</title>
        <style>
            /* ベーススタイル */
            body {{
                font-family: 'Helvetica Neue', Arial, 'Hiragino Kaku Gothic ProN', 'Hiragino Sans', Meiryo, sans-serif;
                color: #333;
                line-height: 1.4;
                margin: 0;
                padding: 20px;
                background-color: #f5f5f5;
            }}
            .container {{
                background-color: #fff;
                padding: 30px;
                box-shadow: 0 0 10px rgba(0,0,0,0.1);
                max-width: 1200px;
                margin: 0 auto;
            }}
            header {{
                display: flex;
                justify-content: space-between;
                align-items: flex-end;
                border-bottom: 2px solid #444;
                padding-bottom: 10px;
                margin-bottom: 20px;
            }}
            h1 {{
                margin: 0;
                font-size: 24px;
                color: #2c3e50;
            }}
            .meta-info {{
                font-size: 12px;
                text-align: right;
            }}

            /* テーブルデザイン */
            table {{
                width: 100%;
                border-collapse: collapse;
                font-size: 12px;
            }}
            th {{
                background-color: #2c3e50;
                color: #ffffff;
                padding: 10px;
                text-align: left;
                border: 1px solid #ddd;
            }}
            td {{
                padding: 8px;
                border: 1px solid #ddd;
                vertical-align: top;
            }}
            tr:nth-child(even) {{
                background-color: #f9f9f9;
            }}
            
            /* カラム固有のスタイル */
            .code {{ font-family: monospace; color: #666; }}
            .title strong {{ display: block; font-size: 13px; color: #000; }}
            .subtitle {{ font-size: 10px; color: #777; margin-top: 2px; }}
            .price {{ text-align: right; font-weight: bold; }}
            .center {{ text-align: center; }}
            .date {{ font-size: 10px; color: #888; white-space: nowrap; }}

            /* 印刷用設定 */
            @media print {{
                body {{ background-color: #fff; padding: 0; }}
                .container {{ box-shadow: none; max-width: none; width: 100%; padding: 0; }}
                @page {{
                    size: A4 landscape;
                    margin: 10mm;
                }}
                th {{ background-color: #eee !important; color: #000 !important; }}
                tr {{ page-break-inside: avoid; }}
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <header>
                <h1>蔵書管理レポート</h1>
                <div class="meta-info">
                    出力日時: {datetime.now().strftime('%Y年%m月%d日 %H:%M')}<br>
                    対象件数: {len(books)} 件
                </div>
            </header>
            
            <table>
                <thead>
                    <tr>
                        <th style="width: 80px;">TSVコード</th>
                        <th>書籍名 / サブタイトル</th>
                        <th style="width: 120px;">著者</th>
                        <th style="width: 100px;">出版社</th>
                        <th style="width: 100px;">ISBN</th>
                        <th style="width: 70px;">書架</th>
                        <th style="width: 80px;">価格</th>
                        <th style="width: 90px;">最終更新</th>
                    </tr>
                </thead>
                <tbody>
                    {table_rows}
                </tbody>
            </table>
        </div>
    </body>
    </html>
    """

    with open(output_filename, "w", encoding="utf-8") as f:
        f.write(html_content)
    
    print(f"HTML Report generated: {os.path.abspath(output_filename)}")

# --- 実行イメージ ---
books_list = []
with database.SessionLocal() as session:
    books_list = session.query(Book).order_by(Book.last_updated_timestamp.desc()).all()
    
generate_html_report(books_list)