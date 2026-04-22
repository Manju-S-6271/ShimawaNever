"""database.py
データベース接続の設定とセッション管理を行うモジュール
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# database/ ディレクトリが存在しない場合は作成する
os.makedirs("database", exist_ok=True)

# ShimaNev.db のパスを指定
DATABASE_URL = "sqlite:///./database/ShimaNev.db"

# SQLAlchemy のエンジンを作成
engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)

# セッションの作成
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ベースクラスの作成
Base = declarative_base()


# データベースセッションを取得するための関数
def get_db():
    # データベースセッションを作成
    db = SessionLocal()

    try:
        # セッションを返す
        yield db
    finally:
        # セッションを閉じる
        db.close()

def init_db():
    """テーブルを作成する"""
    from models import Record, Issuer, Book, BookGroup, Shelf, ChangeHistory
    Base.metadata.create_all(bind=engine)
 