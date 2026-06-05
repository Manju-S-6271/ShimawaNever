import csv
from barcode.ean import EuropeanArticleNumber13 as EAN13
from barcode.writer import ImageWriter
from reportlab.platypus import SimpleDocTemplate, Image, Spacer, Paragraph, PageBreak, Table, TableStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
import os

# --- 設定 ---
INPUT_CSV = "books.csv"
OUTPUT_PDF = "output.pdf"
TEMP_DIR = "temp_barcodes"

# 1. フォントの設定 (環境に合わせてパスを変更してください)
# Windows例: "C:/Windows/Fonts/msgothic.ttc"
# macOS例: "/System/Library/Fonts/Supplemental/MS Gothic.ttf"
# Linux例: "/usr/share/fonts/opentype/ipaexfont-gothic/ipaexgc.ttf"
FONT_PATH = "/Users/manju/Library/Fonts/NotoSansJP-VariableFont_wght.ttf" 
FONT_NAME = "JapaneseFont"

try:
    pdfmetrics.registerFont(TTFont(FONT_NAME, FONT_PATH))
except:
    print(f"Warning: フォントファイルが見つかりません。パスを確認してください: {FONT_PATH}")
    FONT_NAME = "Helvetica" # フォールバック

# レイアウト設定
COLUMNS = 2 # 左右2列
ITEMS_PER_PAGE = 20 # 10行 × 2列 = 20項目

os.makedirs(TEMP_DIR, exist_ok=True)

styles = getSampleStyleSheet()
# 日本語対応のカスタムスタイルを作成
jp_style = ParagraphStyle(
    name='JapaneseStyle',
    parent=styles['Normal'],
    fontName=FONT_NAME,
    fontSize=9,
    leading=11,
)

# CSV読み込み + 重複除去
items_dict = {}
with open(INPUT_CSV, newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        isbn = row["ISBNコード"]
        items_dict[isbn] = row 

items_list = list(items_dict.values())

# バーコード生成関数
def generate_barcode(gtin, filename):
    code = EAN13(str(gtin[:12]), writer=ImageWriter())
    path = os.path.join(TEMP_DIR, filename)
    # save時に拡張子.pngが付与されるため、そのパスを返す
    full_path = code.save(path)
    return full_path

# PDF作成準備
doc = SimpleDocTemplate(OUTPUT_PDF, pagesize=A4, leftMargin=30, rightMargin=30, topMargin=30, bottomMargin=30)
story = []
table_data = []
current_row = []

for i, item in enumerate(items_list):
    title = item["タイトル"]
    isbn = item["ISBNコード"]
    jan = item["書籍JANコード"]

    # 1つのセル内のコンテンツを作成
    cell_content = []
    cell_content.append(Paragraph(f"<b>{title}</b>", jp_style))
    cell_content.append(Spacer(1, 2))

    # バーコード作成 (ISBNとJAN)
    for suffix, code_val in [("isbn", isbn), ("jan", jan)]:
        img_path = generate_barcode(code_val, f"{isbn}_{suffix}")
        cell_content.append(Image(img_path, width=140, height=50))
        cell_content.append(Spacer(1, 2))

    current_row.append(cell_content)

    # 2列埋まったら行を追加
    if len(current_row) == COLUMNS:
        table_data.append(current_row)
        current_row = []

    # ページ区切りの判定
    if len(table_data) > 0 and (len(table_data) * COLUMNS) % ITEMS_PER_PAGE == 0 and len(current_row) == 0:
        table = Table(table_data, colWidths=[250, 250])
        table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 20),
        ]))
        story.append(table)
        story.append(PageBreak())
        table_data = []

# 残りのデータをテーブル化
if current_row:
    while len(current_row) < COLUMNS:
        current_row.append("") # 空のセルで埋める
    table_data.append(current_row)

if table_data:
    table = Table(table_data, colWidths=[250, 250])
    table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 20),
    ]))
    story.append(table)

# PDF出力
doc.build(story)
print("PDF生成完了:", OUTPUT_PDF)