# main.py
# ベースレベルモジュールのインポート
import sys
from loguru import logger

# 1. 既存のデフォルトハンドラー（標準出力）を削除
logger.remove()

# 2. フォーマットや出力先を一括設定
logger.add(
    sys.stdout,
    format='<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{module: <7}</cyan> | <level>{message}</level>',
    level="DEBUG"
)

logger.info("Welcome to ShimawaNever!")
logger.debug("System is starting up...")

# サービスレベルモジュールのインポート
logger.info("Now Loading: Calling Services")
logger.debug("Start Calling Services...")

logger.debug("Calling APMS...")
import services.apms as apms

logger.debug("Calling RAPIS...")
import services.rapis as rapis

logger.debug("Calling ISBNS...")
import services.isbns as isbns

def main():
    logger.info("Now Loading: Loading Services")
    logger.debug("Loading APMS...")
    apms_service = apms.ApplicationPreferences()
    print("A")

if __name__ == "__main__":
    main()