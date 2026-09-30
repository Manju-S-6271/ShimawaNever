"""ShimawaNever Services / RAPIS plugin (Rakuten books API Services)
楽天ブックス系APIと接続するためのサービスです。
"""
import requests
import services.apms as apms
from loguru import logger

logger.debug("Rakuten Books API Services module loaded.")
logger.info("Welcome to ShimawaNever Services / RAPIS plugin (Rakuten books API Services)!")
logger.info("This service is supported by Rakuten Developers <https://developers.rakuten.com/>.")

class RakutenBooksAPI:
    """Rakuten Books API サービスクラス。"""
    logger.debug("Rakuten Books API service class loaded.")
    
    def __init__(self, api_key: str, applicationID: str, accessKey: str):
        logger.debug(f"Rakuten Books API service is initializing with API key: {api_key}, Application ID: {applicationID} and Access Key: {accessKey}")

        self.api_key = api_key
        self.applicationID = applicationID
        self.accessKey = accessKey
        self.base_url = f"https://openapi.rakuten.co.jp/services/api/BooksTotal/Search/20170404"

        logger.debug("Rakuten Books API service initialized.")
    
    def get_books(self, ISBN: str):
        """ISBNを使用して楽天ブックスAPIから書籍情報を取得する関数。"""
        logger.debug(f"Fetching book information for ISBN: {ISBN} from Rakuten Books API.")

        params = {
            'isbnjan': ISBN,
            'format': 'json',
            'applicationId': self.api_key,
            'accessKey': self.accessKey
        }

        response = requests.get(self.base_url, params=params)

        if response.status_code == 200:
            return response.json()
        else:
            response.raise_for_status()