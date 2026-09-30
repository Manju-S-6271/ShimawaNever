"""ShimawaNever Services / APMS plugin (Application Preferences Management Services)
アプリケーションの環境設定を取得するためのサービスです。
"""
import json
import portalocker
import atexit
from loguru import logger

logger.debug("Application Preferences Management Services module loaded.")

class ApplicationPreferences:
    """Application Preferences Management サービスクラス。"""
    logger.debug("Application Preferences Management Services class loaded.")

    def __init__(self, config_path: str = 'config.json'):
        logger.debug(f"Application Preferences Management Services is initializing with config path: {config_path}")

        self.config_path = config_path
        self._lock = None
        self._file_obj = None

        try:
            self._lock = portalocker.Lock(
                self.config_path,
                mode='a+',
                timeout=5,
                flags=portalocker.LOCK_EX | portalocker.LOCK_NB,
            )
            self._file_obj = self._lock.acquire()
        except portalocker.exceptions.AlreadyLocked:
            logger.error(f"failed to acquire lock on config file ({self.config_path}): File is already locked by another process.")
            raise RuntimeError(f"failed to acquire lock on config file ({self.config_path}): File is already locked by another process.")
        except Exception as e:
            logger.error(f"failed to acquire lock on config file ({self.config_path}): {e}")
            raise RuntimeError(f"failed to acquire lock on config file ({self.config_path}): {e}")

        logger.debug("Preferences File lock acquired and file opened.")

        # アプリケーション終了時にロック解除とファイルクローズを行う
        atexit.register(self.complete)

        logger.debug("Application Preferences Management Services initialized.")
        logger.debug("Application Preferences Management Services is started and now Online.")

    def complete(self):
        """ロックを解除し、ファイルをクローズしてアプリケーションのサービスを終了する関数。"""
        if self._lock is not None:
            try:
                self._lock.release()
                self._lock = None
                self._file_obj = None
            except Exception as e:
                logger.error("Failed to release the lock: {}", e)
                raise RuntimeError(f"Failed to release the lock: {e}")

        logger.debug("Preferences File lock released and file closed.")
        logger.debug("Application Preferences Management Services is finished and now Offline.")

    def load_preferences(self, key: str):
        """指定されたキーに対応する設定値を取得する関数。"""
        logger.debug(f"Loading preferences for key: {key}")

        try:
            self._file_obj.seek(0)
            config_data = json.load(self._file_obj)
            value = config_data.get(key, None)
            if value is not None:
                logger.debug(f"Preferences loaded for key: {key}, value: {value}")
            else:
                logger.warning(f"No preferences found for key: {key}.")
            return value
        except json.JSONDecodeError:
            logger.error("Failed to decode JSON from the configuration file.")
            raise RuntimeError("Failed to decode JSON from the configuration file.")
        except Exception as e:
            logger.error(f"Failed to load preferences for key ({key}): {e}")
            raise RuntimeError(f"Failed to load preferences for key ({key}): {e}")