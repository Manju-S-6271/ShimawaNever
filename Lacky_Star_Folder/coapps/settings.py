"""./coapps/settings.py
設定情報を取得するモジュール
"""

import yaml
import xml.etree.ElementTree as ET

def get_isbn_range_table():
    with open("./settings.yml", "r") as f:
        settings = yaml.safe_load(f)
        isbn_range_table_path = settings["book_info_entry"]["isbn_range_table_path"]
        print(f"Loaded: {isbn_range_table_path}")
        
        if isbn_range_table_path:
            print("ET OK")
            return ET.parse(isbn_range_table_path).getroot()