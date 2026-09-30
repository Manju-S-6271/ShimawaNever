"""./coapps/checkdigits.py
チェック数字の計算及び検証を行うモジュラス・ウェイトの計算を行うクラスを定義するモジュール
"""

def calculate(value: int, modulus: int = 10, weight: int = 3):
    """ある数列x及び数y, zに対する、xのモジュラスy ウェイトzの一桁目を10から引いた数を返す関数

    Args:
        value (int): 計算対象の数値
        modulus (int, optional): モジュラス. Defaults to 10.
        weight (int, optional): ウェイト. Defaults to 3.
    Returns:
        int: 特定の関数に基づいて計算されたチェック数字
    """
    digits = [int(d) for d in str(value)]

    # ウェイト列：1とweightを交互に生成
    weights = [1 if i % 2 == 0 else weight for i in range(len(digits))]
    
    # 各桁と対応するウェイトの積の合計を計算し、モジュラスで割った余りを求める
    modulus_sum = (sum(d * w for d, w in zip(digits, weights)) % modulus)

    # modulusの1桁目を10から引いた数を返す
    check_digit = 10 - (abs(modulus_sum) % 10)
    
    # 10の場合は0を返す
    return check_digit if check_digit != 10 else 0

def verify(value: int, check_digit: int, modulus: int = 10, weight: int = 3):
    """ISBN・書籍JANコード・TSVコード等におけるチェック数字の検証を行う関数
    Args:
        value (int): チェック数字を除いた数列（12桁であること。）
        check_digit (int): チェック数字（1桁であること。）
        modulus (int, optional): モジュラス. Defaults to 10.
        weight (int, optional): ウェイト. Defaults to 3.
    Returns:
        bool: チェック数字が正しいかどうか
    """
    calculated_check_digit = calculate(value, modulus, weight)
    return calculated_check_digit == check_digit
        
    
if __name__ == "__main__":
    result = calculate(input(), modulus=10, weight=3)
    print(result)