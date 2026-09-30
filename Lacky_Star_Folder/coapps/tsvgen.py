class TSVCodeGenerator:
    """
    TSVコード体系定義書に基づくコード生成クラス
    """

    @staticmethod
    def tsv_to_s_tsv(tsv_code: str) -> str:
        """
        TSVコード → S-TSVコード
        例: TSV-BK-202-000-000-000-6 → 2020000000006
        """
        parts = tsv_code.split("-")
        # TSV-XX-NNN-[固有番号(可変個)]-C の構造
        # parts[0]="TSV", parts[1]=区分記号, parts[2]=区分コード(3桁),
        # parts[3...-1]=固有番号各セグメント, parts[-1]=チェック数字
        if parts[0] != "TSV" or len(parts) < 5:
            raise ValueError(f"不正なTSVコードです: {tsv_code}")

        obj_code   = parts[2]                          # 3桁
        unique_raw = "".join(parts[3:-1])              # 固有番号（ハイフン除去）
        check      = parts[-1]                         # チェック数字

        if len(obj_code) != 3 or not obj_code.isdigit():
            raise ValueError(f"オブジェクト区分コードが不正です: {obj_code}")
        if len(unique_raw) != 9 or not unique_raw.isdigit():
            raise ValueError(f"固有番号（ハイフン除外後）が9桁になりません: {unique_raw}")
        if len(check) != 1 or not check.isdigit():
            raise ValueError(f"チェック数字が不正です: {check}")

        return f"{obj_code}{unique_raw}{check}"

    @staticmethod
    def calculate_check_digit(validation_code: str) -> str:
        """
        S-TSV検証コード（12桁）からチェック数字を計算する（モジュール10 ウェイト3）
        1桁目（奇数桁）から交互に加算、偶数桁の合計は3倍する。
        """
        if len(validation_code) != 12 or not validation_code.isdigit():
            raise ValueError("S-TSV検証コードは12桁の数字である必要があります。")

        # 奇数桁の合計 (インデックス0, 2, 4, 6, 8, 10)
        odd_sum = sum(int(validation_code[i]) for i in range(0, 12, 2))
        
        # 偶数桁の合計 (インデックス1, 3, 5, 7, 9, 11)
        even_sum = sum(int(validation_code[i]) for i in range(1, 12, 2))
        
        total = odd_sum + (even_sum * 3)
        remainder = total % 10
        
        return "0" if remainder == 0 else str(10 - remainder)

    @classmethod
    def _generate(cls, obj_symbol: str, obj_code: str, unique_formatted: str) -> dict:
        """
        内部生成用のベースメソッド
        """
        unique_digits = unique_formatted.replace("-", "")
        if len(unique_digits) != 9 or not unique_digits.isdigit():
            raise ValueError(f"固有番号（ハイフン除外後）は9桁の数字である必要があります: {unique_digits}")

        validation_code = f"{obj_code}{unique_digits}"
        check_digit = cls.calculate_check_digit(validation_code)

        return {
            "TSV_Code": f"TSV-{obj_symbol}-{obj_code}-{unique_formatted}-{check_digit}",
            "S_TSV_Validation_Code": validation_code,
            "S_TSV_Code": f"{validation_code}{check_digit}"
        }

    # ==========================================
    # TSV-BK オブジェクト（書籍）
    # ==========================================
    @classmethod
    def book_normal(cls, number_9digits: str) -> dict:
        """特例を受けない書籍 (202)"""
        formatted = f"{number_9digits[:3]}-{number_9digits[3:6]}-{number_9digits[6:]}"
        return cls._generate("BK", "202", formatted)

    @classmethod
    def book_isbn13(cls, formatted_isbn_9digits: str) -> dict:
        """13桁の国際標準図書番号の特例 (200) ※区切り文字付きで渡す"""
        return cls._generate("BK", "200", formatted_isbn_9digits)

    @classmethod
    def book_isbn10(cls, formatted_isbn_9digits: str) -> dict:
        """10桁の国際標準図書番号の特例 (201) ※区切り文字付きで渡す"""
        return cls._generate("BK", "201", formatted_isbn_9digits)

    # ==========================================
    # TSV-BG オブジェクト（書籍グループ）
    # ==========================================
    @classmethod
    def book_group(cls, number_9digits: str) -> dict:
        """書籍グループ (205)"""
        formatted = f"{number_9digits[:3]}-{number_9digits[3:6]}-{number_9digits[6:]}"
        return cls._generate("BG", "205", formatted)

    # ==========================================
    # TSV-RE オブジェクト（記録資料等）
    # ==========================================
    @classmethod
    def record(cls, issuer_id_5digits: str, record_id_4digits: str) -> dict:
        """記録資料等 (210)"""
        formatted = f"{issuer_id_5digits}-{record_id_4digits}"
        return cls._generate("RE", "210", formatted)

    # ==========================================
    # TSV-IS オブジェクト（資料発行者）
    # ==========================================
    @classmethod
    def issuer(cls, issuer_id_5digits: str) -> dict:
        """資料発行者 (215)"""
        formatted = f"0000-{issuer_id_5digits}"
        return cls._generate("IS", "215", formatted)

    @classmethod
    def issuer_reserved_system(cls) -> dict:
        """システムで予約済みのTSV-IS オブジェクトに係る特例（システム発行者）"""
        return cls._generate("IS", "215", "0001-00000")

    @classmethod
    def issuer_reserved_default(cls) -> dict:
        """システムで予約済みのTSV-IS オブジェクトに係る特例（デフォルト発行者）"""
        return cls._generate("IS", "215", "0001-00001")

    # ==========================================
    # TSV-SH オブジェクト（書架）
    # ==========================================
    @classmethod
    def shelf(cls, shelf_id_7digits: str, column_id_2digits: str) -> dict:
        """書架・設置列番号の割り当てを受ける書架特例含む (220)"""
        formatted = f"{shelf_id_7digits}-{column_id_2digits}"
        return cls._generate("SH", "220", formatted)

    @classmethod
    def shelf_reserved_system(cls) -> dict:
        """システムで予約済みのTSV-SH オブジェクトに係る特例（システムデータ書架）"""
        return cls._generate("SH", "220", "0000000-00")

    @classmethod
    def shelf_reserved_default(cls) -> dict:
        """システムで予約済みのTSV-SH オブジェクトに係る特例（デフォルト書架）"""
        return cls._generate("SH", "220", "0000000-01")


# === 実行テスト（仕様書第4章「コード実例」に基づく検証） ===
if __name__ == "__main__":
    examples = [
        ("書籍（通常）", TSVCodeGenerator.book_normal("000000000")),
        ("書籍（ISBN-13）", TSVCodeGenerator.book_isbn13("4-01-000000")),
        ("書籍（ISBN-10）", TSVCodeGenerator.book_isbn10("0-0000-0000")),
        ("書籍グループ", TSVCodeGenerator.book_group("000000000")),
        ("書類", TSVCodeGenerator.record("00001", "0001")),
        ("書類発行者（通常）", TSVCodeGenerator.issuer("00002")),
        ("書類発行者（システム発行者）", TSVCodeGenerator.issuer_reserved_system()),
        ("書類発行者（デフォルト発行者）", TSVCodeGenerator.issuer_reserved_default()),
        ("書架（通常）", TSVCodeGenerator.shelf("0000001", "00")),
        ("書架（設置列番号特例）", TSVCodeGenerator.shelf("0000001", "01")),
        ("書架（システムデータ書架）", TSVCodeGenerator.shelf_reserved_system()),
        ("書架（デフォルト書架）", TSVCodeGenerator.shelf_reserved_default()),
    ]

    print(f"{'オブジェクト':<25} | {'TSVコード':<28} | {'検証コード':<15} | {'S-TSVコード'}")
    print("-" * 90)
    for name, data in examples:
        # 見やすさのために検証コードとS-TSVコードをスペースでフォーマットして表示
        v_code = " ".join([data['S_TSV_Validation_Code'][0:3], data['S_TSV_Validation_Code'][3:6], data['S_TSV_Validation_Code'][6:9], data['S_TSV_Validation_Code'][9:12]])
        s_code = f"{v_code} {data['S_TSV_Code'][-1]}"
        
        # 固有番号の区切り位置が違うため、単純な3桁区切りではなく仕様に沿った出力となる
        print(f"{name:　<15} | {data['TSV_Code']:<28} | {v_code.replace(' ', ''):<15} | {data['S_TSV_Code']}")