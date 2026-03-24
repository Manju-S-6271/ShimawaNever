from fastapi import FastAPI, HTTPException
import cv2
from pyzbar.pyzbar import decode
import uvicorn

app = FastAPI()

def scan_multiple_barcodes(expected_count=1, camera_index=0):
    cap = cv2.VideoCapture(camera_index)
    
    # 高精度化のため解像度を確保
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    print(f"{expected_count}個のバーコードを同時スキャン中... (Escで中止)")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # 前処理
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # PyZbarでスキャン
        detected_barcodes = decode(gray)
        
        # 重複を除去しつつ、データを抽出
        # (同じ内容のバーコードが2つある場合も考慮し、位置情報などで区別するのが理想)
        results = []
        for bc in detected_barcodes:
            data = bc.data.decode('utf-8')
            # データの値だけでなく、画面上の「高さ(y座標)」も一緒に保存
            results.append({
                'data': data,
                'top': bc.rect.top
            })

        # 指定された行数が見つかったかチェック
        if len(results) >= expected_count:
            # y座標(top)で昇順ソートすることで「上から順」のリストにする
            results.sort(key=lambda x: x['top'])
            final_data = [item['data'] for item in results]
            
            cap.release()
            cv2.destroyAllWindows()
            return final_data

        # プレビュー表示（見つかっている数だけ枠を描画）
        for bc in detected_barcodes:
            (x, y, w, h) = bc.rect
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.putText(frame, bc.data.decode('utf-8'), (x, y - 10), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

        cv2.imshow('Multi-Barcode Scanner', frame)

        if cv2.waitKey(1) & 0xFF == 27:
            break

    cap.release()
    cv2.destroyAllWindows()
    return None

def scan_multiple_barcodes_stable(expected_count=2, camera_index=1, stability_threshold=10):
    cap = cv2.VideoCapture(camera_index)
    
    # 解像度の設定
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    # 安定性確認用の変数
    previous_results = []
    consecutive_count = 0

    print(f"{expected_count}個のバーコードを{stability_threshold}フレーム連続検知で確定します...")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # 前処理
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # デコード実行
        detected_barcodes = decode(gray)
        
        # 現在のフレームでの読み取り結果をリスト化（y座標でソートして順序を固定）
        current_results = []
        for bc in detected_barcodes:
            current_results.append({
                'data': bc.data.decode('utf-8'),
                'top': bc.rect.top
            })
        
        # y座標でソート（上から順）
        current_results.sort(key=lambda x: x['top'])
        current_data_only = [item['data'] for item in current_results]

        # --- 判定ロジック ---
        # 1. 指定した行数が見つかっているか
        if len(current_data_only) == expected_count:
            # 2. 前のフレームの結果と完全に一致するか
            if current_data_only == previous_results:
                consecutive_count += 1
            else:
                consecutive_count = 1 # 不一致ならカウントリセット
            
            previous_results = current_data_only
        else:
            # 指定行数見つからない場合はリセット
            consecutive_count = 0
            previous_results = []

        # 3. 規定フレーム数（10フレーム）連続で一致したら確定
        if consecutive_count >= stability_threshold:
            cap.release()
            cv2.destroyAllWindows()
            cv2.waitKey(1) 
            cv2.waitKey(1)
            return current_data_only

        # プレビュー表示（枠の描画コードは削除済み）
        # 進行状況を画面の端に表示（デバッグ用：不要なら消去してください）
        status_text = f"{len(current_data_only)} barcode(s) found for last {consecutive_count} frames"
        instructed_text = f"Align {expected_count} barcode(s) for {stability_threshold} consecutive frames"
        cv2.putText(frame, status_text, (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        cv2.putText(frame, instructed_text, (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

        cv2.imshow('Stable Barcode Scanner', frame)

        if cv2.waitKey(1) & 0xFF == 27: # Escで終了
            break

    cap.release()
    cv2.destroyAllWindows()
    return None

# # --- 実行例 ---
# excepted_count = int(input("スキャンするバーコードの数を入力してください: "))
# stability_threshold = int(input("安定とみなす連続フレーム数を入力してください (例: 10): "))
# lines = scan_multiple_barcodes_stable(expected_count=excepted_count, stability_threshold=stability_threshold)

# if lines:
#     print("\nスキャン完了:")
#     for i, line in enumerate(lines, 1):
#         print(f"{i}行目: {line}")

@app.get("/scan")
async def scan_endpoint(count: int = 2, stability: int = 10):
    """
    HTTP GETリクエストを受けてスキャンを開始する
    例: http://localhost:8000/scan?count=2&stability=10
    """
    result = scan_multiple_barcodes_stable(expected_count=count, stability_threshold=stability)
    
    if result:
        return {"status": "success", "results": result}
    else:
        raise HTTPException(status_code=400, detail="Scan cancelled or failed")

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)