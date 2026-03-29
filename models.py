"""models.py
データベースのモデル定義を行うモジュール
"""

from sqlalchemy import Column, String, Integer, Numeric, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime, timezone


# Records テーブル: 記録資料等[RE]の情報を保存するテーブル（TSVコードを主キーとする）
class Record(Base):
    __tablename__ = "records"

    tsv_code = Column(String, primary_key=True, index=True, comment="TSVコード:記録資料等[RE]")
    parent_tsv_code = Column(String, ForeignKey("records.tsv_code"), nullable=True, index=True, comment="親記録資料のTSVコード")

    title = Column(String, nullable=False, index=True, comment="資料名")
    title_phonetic = Column(String, nullable=True, index=True, comment="資料名（読み仮名）")

    record_type = Column(String, nullable=False, index=True, comment="資料種別")

    issuer_tsv_code = Column(String, ForeignKey("issuers.tsv_code"), nullable=True, index=True, comment="発行者TSVコード")
    shelf_tsv_code = Column(String, ForeignKey("shelves.tsv_code"), nullable=False, index=True, comment="書架TSVコード")

    record_period_start = Column(String, nullable=True, index=True, comment="保管期間（開始）")
    record_period_end = Column(String, nullable=True, index=True, comment="保管期間（終了）")

    record_finished = Column(String, nullable=True, index=True, comment="保管終了フラグ")

    note = Column(String, nullable=True, index=True, comment="備考")

    issued_timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True, comment="登録日時")
    last_updated_timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False, index=True, comment="最終更新日時")

    issuer = relationship("Issuer", foreign_keys=[issuer_tsv_code])
    shelf = relationship("Shelf", foreign_keys=[shelf_tsv_code])
    parent = relationship("Record", remote_side="Record.tsv_code", foreign_keys=[parent_tsv_code])


# Issuers テーブル: 資料発行者[IS]の情報を保存するテーブル（TSVコードを主キーとする）
class Issuer(Base):
    __tablename__ = "issuers"

    tsv_code = Column(String, primary_key=True, index=True, comment="TSVコード:資料発行者[IS]")
    tsv_embed_code = Column(String, nullable=True, unique=True, index=True, comment="埋め込みTSVコード")
    parent_tsv_code = Column(String, ForeignKey("issuers.tsv_code"), nullable=True, index=True, comment="親発行者のTSVコード")

    name = Column(String, nullable=False, index=True, comment="発行者名")
    name_phonetic = Column(String, nullable=True, index=True, comment="発行者名（読み仮名）")

    issuer_code = Column(String, nullable=True, unique=True, index=True, comment="発行者コード")
    child_number = Column(Integer, nullable=True, index=True, comment="子番号")

    note = Column(String, nullable=True, index=True, comment="備考")

    issued_timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True, comment="登録日時")
    last_updated_timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False, index=True, comment="最終更新日時")

    parent = relationship("Issuer", remote_side="Issuer.tsv_code", foreign_keys=[parent_tsv_code])


# Books テーブル: 書籍[BK]の情報を保存するテーブル（TSVコードを主キーとする）
class Book(Base):
    __tablename__ = "books"

    tsv_code = Column(String, primary_key=True, index=True, comment="TSVコード:書籍[BK]")
    bookgroup_tsv_code = Column(String, ForeignKey("book_groups.tsv_code"), nullable=True, index=True, comment="書籍グループTSVコード")
    parent_tsv_code = Column(String, ForeignKey("books.tsv_code"), nullable=True, index=True, comment="親書籍のTSVコード")

    title = Column(String, nullable=False, index=True, comment="書籍名")
    title_phonetic = Column(String, nullable=True, index=True, comment="書籍名（読み仮名）")

    subtitle = Column(String, nullable=True, index=True, comment="サブタイトル")

    authors = Column(String, nullable=True, index=True, comment="著者")
    publisher = Column(String, nullable=True, index=True, comment="出版社")

    shelf_tsv_code = Column(String, ForeignKey("shelves.tsv_code"), nullable=False, index=True, comment="書架TSVコード")

    isbn = Column(String, nullable=True, unique=True, index=True, comment="ISBN")
    book_jan = Column(String, nullable=True, index=True, comment="書籍JANコード")
    c_code = Column(String, nullable=True, index=True, comment="Cコード")
    price = Column(Numeric(10, 2), nullable=True, index=True, comment="価格")

    size = Column(String, nullable=True, index=True, comment="サイズ")

    stock_finished = Column(String, nullable=True, index=True, comment="在架終了フラグ")

    note = Column(String, nullable=True, index=True, comment="備考")

    issued_timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True, comment="登録日時")
    last_updated_timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False, index=True, comment="最終更新日時")

    book_group = relationship("BookGroup", foreign_keys=[bookgroup_tsv_code])
    shelf = relationship("Shelf", foreign_keys=[shelf_tsv_code])
    parent = relationship("Book", remote_side="Book.tsv_code", foreign_keys=[parent_tsv_code])


# BookGroups テーブル: 書籍グループ（巻号）[BG]の情報を保存するテーブル（TSVコードを主キーとする）
class BookGroup(Base):
    __tablename__ = "book_groups"

    tsv_code = Column(String, primary_key=True, index=True, comment="TSVコード:書籍グループ[BG]")
    parent_tsv_code = Column(String, ForeignKey("book_groups.tsv_code"), nullable=True, index=True, comment="親書籍グループのTSVコード")

    title = Column(String, nullable=False, index=True, comment="グループ名")
    title_phonetic = Column(String, nullable=True, index=True, comment="グループ名（読み仮名）")

    note = Column(String, nullable=True, index=True, comment="備考")

    issued_timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True, comment="登録日時")
    last_updated_timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False, index=True, comment="最終更新日時")

    parent = relationship("BookGroup", remote_side="BookGroup.tsv_code", foreign_keys=[parent_tsv_code])


# Shelves テーブル: 書架[SH]の情報を保存するテーブル（TSVコードを主キーとする）
class Shelf(Base):
    __tablename__ = "shelves"

    tsv_code = Column(String, primary_key=True, index=True, comment="TSVコード:書架[SH]")
    parent_tsv_code = Column(String, ForeignKey("shelves.tsv_code"), nullable=True, index=True, comment="親書架のTSVコード")

    name = Column(String, nullable=False, index=True, comment="書架名")
    name_phonetic = Column(String, nullable=True, index=True, comment="書架名（読み仮名）")

    address = Column(String, nullable=True, index=True, comment="住所")
    specific_location = Column(String, nullable=True, index=True, comment="詳細位置")

    note = Column(String, nullable=True, index=True, comment="備考")

    issued_timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True, comment="登録日時")
    last_updated_timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False, index=True, comment="最終更新日時")

    parent = relationship("Shelf", remote_side="Shelf.tsv_code", foreign_keys=[parent_tsv_code])


# 変更履歴テーブル: 変更履歴の情報を保存するテーブル（連番のChangeIDを主キーとする）
class ChangeHistory(Base):
    __tablename__ = "change_history"

    change_id = Column(Integer, primary_key=True, index=True, comment="変更ID")
    tsv_code = Column(String, nullable=False, index=True, comment="変更対象のTSVコード")
    record_type = Column(String, nullable=False, index=True, comment="変更対象のレコード種別")
    change_type = Column(String, nullable=False, index=True, comment="変更種別（追加、更新、削除）")
    changed_data = Column(String, nullable=True, comment="変更されたデータの内容")

    changed_timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True, comment="変更日時")