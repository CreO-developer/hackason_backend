from fastapi import FastAPI, HTTPException, Response
import firebase_admin
from firebase_admin import credentials, storage
from pydantic import BaseModel
import uvicorn
from datetime import timedelta
import numpy as np
import cv2
import requests
from io import BytesIO

# from api.number_of_people import detect_people_in_image
# FastAPIのインスタンス作成
app = FastAPI()

# 初期化
cred = credentials.Certificate('./firebase.json')
firebase_admin.initialize_app(cred, {"storageBucket": "prehackson22.appspot.com"})

# storageのbucketインスタンスを作成
bucket = storage.bucket()

class Question(BaseModel):
    imageUrl: str # 自身で撮った画像のURL
    themeNumber: int # テーマ番号 1~5が1人用、6~10が2人用、11~15が3,4人用

@app.get("/")
async def root():
    return {"message": "Hello World"}

# テーマ1（図形）の問題 100点満点
@app.post("/mock/question1")
async def submit_score_question1(Question):
    # ここでスコアデータを処理します
    # 開発者の主観15点満点
    # 人数 15点満点
    # はみ出しているか35点満点
    # 枠がどれだけ埋まっているか35点満点
    return {"includeScore": 15 , "excludeScore": 15, "peopleScore": 35,"originalScore": 35}

# テーマ2（組体操）の問題 100点満点
@app.post("/mock/question2")
async def submit_score_question2(Question):
    # ここでスコアデータを処理します
    # 開発者の主観15点満点
    # 人数 15点満点
    # はみ出しているか35点満点
    # 枠がどれだけ埋まっているか35点満点
    return {"includeScore": 15 , "excludeScore": 15, "peopleScore": 35,"originalScore": 35}

# テーマ3（芸能人）の問題 150点満点
@app.post("/mock/question3")
async def submit_score_question3(Question):
    # ここでスコアデータを処理します
    #開発者の主観 20点
    #人数 20点
    #はみ出しているか　45点
    #枠がどれだけ埋まっているか　45点
    #表情: 20
    return {"includeScore": 15 , "excludeScore": 15, "peopleScore": 35,"originalScore": 35,"faceScore": 15}

# テーマ4（アニメ、漫画）の問題 150点満点
@app.post("/mock/question4")
async def submit_score_question4(Question):
    #ここでスコアデータを処理します
    #開発者の主観20点
    #人数20点
    #はみ出しているか45点
    #枠がどれだけ埋まっているか45点
    #表情: 20
    return {"includeScore": 15 , "excludeScore": 15, "peopleScore": 35,"originalScore": 35,"faceScore": 10}

@app.get("/get-image/{file_name}")
async def get_image(file_name: str):
    try:
        # ーーーーーーーーーーーーーーーーーーーーとらが変えるところ(できたらファイル分割してね)　ーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーー
        # Firebase Storageから画像をダウンロード
        blob = bucket.blob(file_name)
        image_url = blob.generate_signed_url(version='v4', expiration=timedelta(seconds=300), method='GET')
        response = requests.get(image_url)
        if response.status_code != 200:
            raise HTTPException(status_code=404, detail="Image not found")
        image_array = np.array(bytearray(response.content), dtype=np.uint8)
        image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
        #  人数を検出
        # numberOfPeople = detect_people_in_image(image)
        # print(numberOfPeople)

        if image is None:
            raise HTTPException(status_code=500, detail="Failed to decode image")
        
        # 画像をグレースケールに変換
        gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        # グレースケール画像をエンコードしてメモリに保存
        _, encoded_image = cv2.imencode('.jpg', gray_image)
        image_data = BytesIO(encoded_image.tobytes())

        # Firebase Storageにアップロード
        new_blob = bucket.blob(f"grayscale-{file_name}")
        new_blob.upload_from_file(image_data, content_type='image/jpeg')

        return {"message": f"Grayscale image uploaded successfully as grayscale-{file_name}"}
    except HTTPException as http_exc:
        return Response(content=str(http_exc.detail), status_code=http_exc.status_code, media_type='text/plain')
    except Exception as e:
        return Response(content=str(e), status_code=500, media_type='text/plain')
    
 # ーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーー
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="debug")
