"""schemas/book.py
書籍関連のスキーマ定義を行うモジュール
"""

from pydantic import BaseModel
from typing import Optional
from decimal import Decimal
from datetime import datetime, timezone

# 登録・更新時のリクエストボディ
class BookCreate(BaseModel):
    title: str
    title_phonetic: Optional[str] = None
    subtitle: Optional[str] = None
    authors: Optional[str] = None
    publisher: Optional[str] = None
    shelf_tsv_code: str          # 必須：どの書架に置くか
    bookgroup_tsv_code: Optional[str] = None
    parent_tsv_code: Optional[str] = None
    isbn: Optional[str] = None
    book_jan: Optional[str] = None
    c_code: Optional[str] = None
    price: Optional[Decimal] = None
    size: Optional[str] = None
    note: Optional[str] = None

# 更新時のリクエストボディ（全てのフィールドが任意）
class BookUpdate(BaseModel):
    title: Optional[str] = None
    title_phonetic: Optional[str] = None
    subtitle: Optional[str] = None
    authors: Optional[str] = None
    publisher: Optional[str] = None
    shelf_tsv_code: Optional[str] = None
    bookgroup_tsv_code: Optional[str] = None
    parent_tsv_code: Optional[str] = None
    isbn: Optional[str] = None
    book_jan: Optional[str] = None
    c_code: Optional[str] = None
    price: Optional[Decimal] = None
    size: Optional[str] = None
    note: Optional[str] = None

# レスポンスモデル
class BookResponse(BaseModel):
    tsv_code: str
    title: str
    title_phonetic: Optional[str] = None
    subtitle: Optional[str] = None
    authors: Optional[str] = None
    publisher: Optional[str] = None
    shelf_tsv_code: str
    bookgroup_tsv_code: Optional[str] = None
    parent_tsv_code: Optional[str] = None
    isbn: Optional[str] = None
    book_jan: Optional[str] = None
    c_code: Optional[str] = None
    price: Optional[Decimal] = None
    size: Optional[str] = None
    note: Optional[str] = None
    issued_timestamp: datetime
    last_updated_timestamp: datetime

    class Config:
        orm_mode = True