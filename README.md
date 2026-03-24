# ShimawaNever — 蔵置管理システム

書類・書籍のメタデータを管理するローカルWebアプリケーションです。

## 技術スタック
- **バックエンド**: Python + FastAPI
- **DB**: SQLite（`shimanev.db` 1ファイルで完結）
- **フロントエンド**: HTML + Jinja2

## セットアップ・起動

```bash
# 1. 依存パッケージをインストール
pip install -r requirements.txt

# 2. サーバーを起動
uvicorn main:app --reload

# 3. ブラウザでアクセス
# http://localhost:8000
```

## 使い方

### 初回セットアップ順序
1. **場所マスタ** (`/locations`) — 蔵置場所を登録（P001, P002, …）
2. **発行者マスタ** (`/issuers`) — 発行者コードを登録（COM, GOV, …）
3. **親分類マスタ** (`/categories`) — 任意で書類群の分類を登録
4. **蔵置管理票** (`/records/new`) — 書類・書籍を登録

### 蔵置管理票番号の形式
```
TSV-LH-P001-ICOM-C000-R001
│   │   │    │    │    └── 資料連番 (R)
│   │   │    │    └─────── 発行者サブコード (C)
│   │   │    └──────────── 発行者コード (I)
│   │   └───────────────── 場所コード (P)
│   └───────────────────── 蔵置区分 (LS/LI/LH/LW/LB/OTHER)
└───────────────────────── システム識別子
```

### 蔵置区分
| コード | 区分 |
|--------|------|
| LS | 機密資料 |
| LI | 重要資料 |
| LH | 記録資料 |
| LW | 持出資料 |
| LB | 書籍 |

### CSVエクスポート
ナビゲーションの「CSV エクスポート」から全件をCSV形式でダウンロードできます。

## ファイル構成
```
tsvault/
├── main.py           # FastAPIアプリ（ルーティング・ビジネスロジック）
├── database.py       # DB初期化・接続
├── requirements.txt
├── shimanev.db        # SQLiteデータベース（初回起動時自動生成）
├── static/
│   └── css/style.css
└── templates/
    ├── base.html
    ├── index.html
    ├── records/
    │   ├── list.html
    │   ├── form.html
    │   └── detail.html
    └── masters/
        ├── issuers.html
        ├── locations.html
        └── categories.html
```
