"""models.py
データベースのモデル定義を行うモジュール

TSVコード体系定義書 (TSVCODE.md) 及び
ShimawaNever TSVコード運用文書 (TSVCODE_Operation_ShimawaNever.md) に準拠する。
"""

from sqlalchemy import Column, String, Integer, Numeric, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime, timezone


# ---------------------------------------------------------------------------
# Records テーブル
# 記録資料等 [TSV-RE / オブジェクト区分コード: 210] の情報を保存するテーブル
# TSVコードを主キーとする。
# ---------------------------------------------------------------------------
class Record(Base):
    __tablename__ = "records"

    tsv_code = Column(
        String, primary_key=True, index=True,
        comment="TSVコード [TSV-RE]: 記録資料等の識別子"
    )
    parent_tsv_code = Column(
        String, ForeignKey("records.tsv_code"), nullable=True, index=True,
        comment="親記録資料のTSVコード [TSV-RE]: 資料がファイル等の収納物である場合に設定する"
    )

    title = Column(String, nullable=False, index=True, comment="資料名")
    title_phonetic = Column(String, nullable=True, index=True, comment="資料名（読み仮名）")

    record_type = Column(String, nullable=False, index=True, comment="資料種別")

    issuer_tsv_code = Column(
        String, ForeignKey("issuers.tsv_code"),
        # デフォルト発行者: TSV-IS-215-0001-00001-C
        # （システムで予約済みのTSV-IS オブジェクト / いずれの発行者にも属さない資料に関連付ける）
        # チェック数字 C は実装時にシステムが算出した正しい値に置き換えること。
        default="TSV-IS-215-0001-00001-C",
        nullable=False, index=True,
        comment="発行者TSVコード [TSV-IS]: 関連付けられる資料発行者の識別子"
    )
    shelf_tsv_code = Column(
        String, ForeignKey("shelves.tsv_code"), nullable=False, index=True,
        comment="書架TSVコード [TSV-SH]: 資料が収納される書架の識別子"
    )

    document_date = Column(String, nullable=True, index=True, comment="発行・交付・有効日")
    record_period_start = Column(String, nullable=True, index=True, comment="保管期間（開始）")
    record_period_end = Column(String, nullable=True, index=True, comment="保管期間（終了）")

    record_finished = Column(
        String, nullable=True, index=True,
        comment="保管終了フラグ: 保管が終了した資料に設定する"
    )

    note = Column(String, nullable=True, comment="備考")

    issued_timestamp = Column(
        DateTime, default=lambda: datetime.now(timezone.utc),
        nullable=False, index=True, comment="登録日時（UTC）"
    )
    last_updated_timestamp = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False, index=True, comment="最終更新日時（UTC）"
    )

    issuer = relationship("Issuer", foreign_keys=[issuer_tsv_code])
    shelf = relationship("Shelf", foreign_keys=[shelf_tsv_code])
    parent = relationship("Record", remote_side="Record.tsv_code", foreign_keys=[parent_tsv_code])


# ---------------------------------------------------------------------------
# Issuers テーブル
# 資料発行者 [TSV-IS / オブジェクト区分コード: 215] の情報を保存するテーブル
# TSVコードを主キーとする。
# ---------------------------------------------------------------------------
class Issuer(Base):
    __tablename__ = "issuers"

    tsv_code = Column(
        String, primary_key=True, index=True,
        comment="TSVコード [TSV-IS]: 資料発行者の識別子"
    )
    parent_tsv_code = Column(
        String, ForeignKey("issuers.tsv_code"), nullable=True, index=True,
        comment="親発行者のTSVコード [TSV-IS]: 発行者が組織の下位部門等である場合に設定する"
    )

    name = Column(String, nullable=False, index=True, comment="発行者名")
    name_phonetic = Column(String, nullable=True, index=True, comment="発行者名（読み仮名）")

    issuer_number = Column(
        String(5), nullable=True, unique=True, index=True,
        comment=(
            "発行者番号（5桁）: TSVコードの固有番号後半5桁に相当する。"
            "システムで予約済みのTSV-IS オブジェクトは NULL とする。"
            "範囲: 00002–99999"
        )
    )

    note = Column(String, nullable=True, comment="備考")

    issued_timestamp = Column(
        DateTime, default=lambda: datetime.now(timezone.utc),
        nullable=False, index=True, comment="登録日時（UTC）"
    )
    last_updated_timestamp = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False, index=True, comment="最終更新日時（UTC）"
    )

    parent = relationship("Issuer", remote_side="Issuer.tsv_code", foreign_keys=[parent_tsv_code])


# ---------------------------------------------------------------------------
# Books テーブル
# 書籍 [TSV-BK / オブジェクト区分コード: 200・201・202] の情報を保存するテーブル
# TSVコードを主キーとする。
# ---------------------------------------------------------------------------
class Book(Base):
    __tablename__ = "books"

    tsv_code = Column(
        String, primary_key=True, index=True,
        comment="TSVコード [TSV-BK]: 書籍の識別子"
    )
    bookgroup_tsv_code = Column(
        String, ForeignKey("book_groups.tsv_code"), nullable=True, index=True,
        comment="書籍グループTSVコード [TSV-BG]: 所属するシリーズ等の識別子"
    )
    parent_tsv_code = Column(
        String, ForeignKey("books.tsv_code"), nullable=True, index=True,
        comment="親書籍のTSVコード [TSV-BK]: 書籍が別書籍の下位に位置する場合に設定する"
    )

    title = Column(String, nullable=False, index=True, comment="書籍名")
    title_phonetic = Column(String, nullable=True, index=True, comment="書籍名（読み仮名）")

    subtitle = Column(String, nullable=True, index=True, comment="サブタイトル")

    authors = Column(String, nullable=True, index=True, comment="著者")
    publisher = Column(String, nullable=True, index=True, comment="出版社")
    published_date = Column(String, nullable=True, index=True, comment="出版日")

    description = Column(String, nullable=True, comment="説明")

    shelf_tsv_code = Column(
        String, ForeignKey("shelves.tsv_code"), nullable=False, index=True,
        comment="書架TSVコード [TSV-SH]: 書籍が収納される書架の識別子"
    )

    isbn = Column(
        String, nullable=True, unique=True, index=True,
        comment="ISBN: ISBN-13 を優先して格納する。ISBN-10 のみの場合は ISBN-10 を格納する。"
    )
    book_jan = Column(
        String, nullable=True, index=True,
        comment="書籍JANコード: 書籍に印刷されている出版社付番のJANコード（GTIN-13）。S-TSVコードとは独立した値。"
    )

    c_code = Column(String, nullable=True, index=True, comment="Cコード")
    target = Column(String, nullable=True, index=True, comment="対象（Cコードより導出）")
    form = Column(String, nullable=True, index=True, comment="形態（Cコードより導出）")
    content = Column(String, nullable=True, index=True, comment="内容（Cコードより導出）")

    price = Column(Numeric(10, 2), nullable=True, index=True, comment="価格")

    size = Column(String, nullable=True, index=True, comment="サイズ")

    stock_finished = Column(
        String, nullable=True, index=True,
        comment="在架終了フラグ: 在架が終了した書籍に設定する"
    )

    note = Column(String, nullable=True, comment="備考")

    issued_timestamp = Column(
        DateTime, default=lambda: datetime.now(timezone.utc),
        nullable=False, index=True, comment="登録日時（UTC）"
    )
    last_updated_timestamp = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False, index=True, comment="最終更新日時（UTC）"
    )

    book_group = relationship("BookGroup", foreign_keys=[bookgroup_tsv_code])
    shelf = relationship("Shelf", foreign_keys=[shelf_tsv_code])
    parent = relationship("Book", remote_side="Book.tsv_code", foreign_keys=[parent_tsv_code])


# ---------------------------------------------------------------------------
# BookGroups テーブル
# 書籍グループ [TSV-BG / オブジェクト区分コード: 205] の情報を保存するテーブル
# TSVコードを主キーとする。
# ---------------------------------------------------------------------------
class BookGroup(Base):
    __tablename__ = "book_groups"

    tsv_code = Column(
        String, primary_key=True, index=True,
        comment="TSVコード [TSV-BG]: 書籍グループの識別子"
    )
    parent_tsv_code = Column(
        String, ForeignKey("book_groups.tsv_code"), nullable=True, index=True,
        comment="親書籍グループのTSVコード [TSV-BG]: グループが別グループの下位に位置する場合に設定する"
    )

    title = Column(String, nullable=False, index=True, comment="グループ名")
    title_phonetic = Column(String, nullable=True, index=True, comment="グループ名（読み仮名）")

    note = Column(String, nullable=True, comment="備考")

    issued_timestamp = Column(
        DateTime, default=lambda: datetime.now(timezone.utc),
        nullable=False, index=True, comment="登録日時（UTC）"
    )
    last_updated_timestamp = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False, index=True, comment="最終更新日時（UTC）"
    )

    parent = relationship("BookGroup", remote_side="BookGroup.tsv_code", foreign_keys=[parent_tsv_code])


# ---------------------------------------------------------------------------
# Shelves テーブル
# 書架 [TSV-SH / オブジェクト区分コード: 220] の情報を保存するテーブル
# TSVコードを主キーとする。
# ---------------------------------------------------------------------------
class Shelf(Base):
    __tablename__ = "shelves"

    tsv_code = Column(
        String, primary_key=True, index=True,
        comment="TSVコード [TSV-SH]: 書架の識別子"
    )
    parent_tsv_code = Column(
        String, ForeignKey("shelves.tsv_code"), nullable=True, index=True,
        comment="親書架のTSVコード [TSV-SH]: 書架が別書架の下位（設置列等）である場合に設定する"
    )

    name = Column(String, nullable=False, index=True, comment="書架名")
    name_phonetic = Column(String, nullable=True, index=True, comment="書架名（読み仮名）")

    address = Column(String, nullable=True, index=True, comment="住所")
    specific_location = Column(String, nullable=True, index=True, comment="詳細位置")

    note = Column(String, nullable=True, comment="備考")

    issued_timestamp = Column(
        DateTime, default=lambda: datetime.now(timezone.utc),
        nullable=False, index=True, comment="登録日時（UTC）"
    )
    last_updated_timestamp = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False, index=True, comment="最終更新日時（UTC）"
    )

    parent = relationship("Shelf", remote_side="Shelf.tsv_code", foreign_keys=[parent_tsv_code])


# ---------------------------------------------------------------------------
# ChangeHistory テーブル
# 変更履歴の情報を保存するテーブル（連番の change_id を主キーとする）
# ---------------------------------------------------------------------------
class ChangeHistory(Base):
    __tablename__ = "change_history"

    change_id = Column(Integer, primary_key=True, autoincrement=True, index=True, comment="変更ID（連番）")
    tsv_code = Column(String, nullable=False, index=True, comment="変更対象のTSVコード")
    object_category = Column(
        String, nullable=False, index=True,
        comment="変更対象のオブジェクト区分（例: TSV-BK, TSV-RE, TSV-IS, TSV-SH, TSV-BG）"
    )
    change_type = Column(
        String, nullable=False, index=True,
        comment="変更種別（CREATE / UPDATE / DELETE / INVALIDATE）"
    )
    changed_data = Column(String, nullable=True, comment="変更されたデータの内容（JSON等）")

    changed_timestamp = Column(
        DateTime, default=lambda: datetime.now(timezone.utc),
        nullable=False, index=True, comment="変更日時（UTC）"
    )