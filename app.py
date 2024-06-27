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
import logging

from utils import get_image_from_firebase
from utils import get_subject_image_path
from utils import get_percent_from_theme, peaple_and_developer_score, get_face_score

# from api.number_of_people import detect_people_in_image
# FastAPIのインスタンス作成
app = FastAPI()

# Firebaseの初期化
cred = credentials.Certificate('./firebase.json')
if not firebase_admin._apps:
    firebase_admin.initialize_app(cred, {"storageBucket": "prehackson22.appspot.com"})

# storageのbucketインスタンスを作成
bucket = storage.bucket()

# ログの設定
logging.basicConfig(level=logging.INFO)

class Question(BaseModel):
    imageUrl: str  # 自身で撮った画像のURL
    themeNumber: int  # テーマ番号 1~5が1人用、6~10が2人用、11~15が3,4人用

@app.get("/")
async def root():
    return {"message": "Hello World"}

# テーマ1（図形）の問題 100点満点
@app.post("/mock/question1")
async def submit_score_question1(question: Question):
  
    # ここでスコアデータを処理します
    # 開発者の主観15点満点
    # 人数 15点満点
    # はみ出しているか35点満点
    # 枠がどれだけ埋まっているか35点満点
    # num_of_questions = 1
    # # Firebase Storageから画像をダウンロード
    # image = await get_image_from_firebase(question.imageUrl)
    # if image is None:
    #     raise HTTPException(status_code=500, detail="Failed to decode image")

    # # 人数によるスコアを取得
    # peaple_score = get_score_num_of_people(image, question.themeNumber)

    # # お題の画像を取得
    # theme_image_path = get_subject_image_path(num_of_questions, question.themeNumber)
    
    # # はみ出している割合と含まれている割合を計算
    # exclude_ratio, include_ratio = get_percent_from_theme(image, theme_image_path)

    # include_score = include_ratio * 35
    # exclude_score = (1 - exclude_ratio) * 35

    # logging.info(f"include_ratio: {include_ratio}, hamidashi_ratio: {exclude_ratio}")

    # return {"includeScore": include_score , "excludeScore": exclude_score, "peopleScore": peaple_score, "originalScore": 15}
  return {"includeScore": 35 , "excludeScore": 35, "peopleScore": 15,"originalScore": 15}
@app.post("/question1")
async def submit_score_question1(question: Question):
    # ここでスコアデータを処理します
    # 開発者の主観15点満点
    # 人数 15点満点
    # はみ出しているか35点満点
    # 枠がどれだけ埋まっているか35点満点
    num_of_questions = 1
    # Firebase Storageから画像をダウンロード
    image = await get_image_from_firebase(question.imageUrl)

    if image is None:
        raise HTTPException(status_code=500, detail="Failed to decode image")

    # 人数によるスコアを取得
    max_peaple_score = 15
    peaple_score, original_score_raito = peaple_and_developer_score(image, question.themeNumber, max_peaple_score)

    print(f'peaple_score: {peaple_score}')

    # 開発者の主観スコア
    original_score = original_score_raito * 15

    # お題の画像を取得
    theme_image_path = get_subject_image_path(num_of_questions, question.themeNumber)
    
    # はみ出している割合と含まれている割合を計算
    exclude_ratio, include_ratio = get_percent_from_theme(image, theme_image_path)

    include_score = include_ratio * 35
    exclude_score = (1 - exclude_ratio) * 35

    logging.info(f"include_ratio: {include_ratio}, hamidashi_ratio: {exclude_ratio}")

    return {"includeScore": int(include_score) , "excludeScore": int(exclude_score), "peopleScore": int(peaple_score), "originalScore": original_score}

# テーマ2（組体操）の問題 100点満点
@app.post("/mock/question2")
async def submit_score_question2(question: Question):
    # ここでスコアデータを処理します
    # 開発者の主観15点満点
    # 人数 15点満点
    # はみ出しているか35点満点
    # 枠がどれだけ埋まっているか35点満点
    return {"includeScore": 20 , "excludeScore": 35, "peopleScore":5,"originalScore": 15}

@app.post("/question2")
async def submit_score_question2(question: Question):
    # ここでスコアデータを処理します
    # 開発者の主観15点満点
    # 人数 15点満点
    # はみ出しているか35点満点
    # 枠がどれだけ埋まっているか35点満点

    num_of_questions = 2
    # Firebase Storageから画像をダウンロード
    image = await get_image_from_firebase(question.imageUrl)
    if image is None:
        raise HTTPException(status_code=500, detail="Failed to decode image")
    
    # 人数によるスコアを取得
    max_peaple_score = 15
    peaple_score, original_score_raito = peaple_and_developer_score(image, question.themeNumber, max_peaple_score)

    print(f'peaple_score: {peaple_score}')

    # 開発者の主観スコア
    original_score = original_score_raito * 15
    # お題の画像を取得
    theme_image_path = get_subject_image_path(num_of_questions, question.themeNumber)

    # はみ出している割合と含まれている割合を計算
    exclude_ratio, include_ratio = get_percent_from_theme(image, theme_image_path)

    include_score = include_ratio * 35
    exclude_score = (1 - exclude_ratio) * 35

    exclude_score = 0 if exclude_score < 0 else exclude_score

    logging.info(f"include_ratio: {include_ratio}, hamidashi_ratio: {exclude_ratio}")
   
    return {"includeScore": int(include_score) , "excludeScore": int(exclude_score), "peopleScore": int(peaple_score), "originalScore": original_score}

# テーマ3（芸能人）の問題 150点満点
@app.post("/mock/question3")
async def submit_score_question3(question: Question):
    # ここでスコアデータを処理します
    #開発者の主観 20点
    #人数 20点
    #はみ出しているか　45点
    #枠がどれだけ埋まっているか　45点
    #表情: 20
    return {"includeScore": 30 , "excludeScore": 30, "peopleScore": 10,"originalScore": 10,"faceScore": 0}

@app.post("/question3")
async def submit_score_question3(question: Question):
    # ここでスコアデータを処理します
    # 開発者の主観 20点
    # 人数 20点
    # はみ出しているか 45点
    # 枠がどれだけ埋まっているか 45点
    # 表情: 20

    num_of_questions = 3
    # Firebase Storageから画像をダウンロード
    image = await get_image_from_firebase(question.imageUrl)
    if image is None:
        raise HTTPException(status_code=500, detail="Failed to decode image")

   # 人数によるスコアを取得
    max_peaple_score = 20
    peaple_score, original_score_raito = peaple_and_developer_score(image, question.themeNumber, max_peaple_score)

    print(f'peaple_score: {peaple_score}')

    # 開発者の主観スコア
    original_score = original_score_raito * 20

    # お題の画像を取得
    theme_image_path = get_subject_image_path(num_of_questions, question.themeNumber)
    
    # はみ出している割合と含まれている割合を計算
    exclude_ratio, include_ratio = get_percent_from_theme(image, theme_image_path)

    include_score = include_ratio * 45
    exclude_score = (1 - exclude_ratio) * 45

    logging.info(f"include_ratio: {include_ratio}, hamidashi_ratio: {exclude_ratio}")

    # 表情のスコアを取得
    emotional_ratio =  get_face_score(image)
    emotion_score = emotional_ratio * 20

    return {"includeScore": int(include_score) , "excludeScore": int(exclude_score), "peopleScore": int(peaple_score), "originalScore": original_score, "faceScore": emotion_score}

# テーマ4（アニメ、漫画）の問題 150点満点
@app.post("/mock/question4")
async def submit_score_question4(question: Question):
    #ここでスコアデータを処理します
    #開発者の主観20点
    #人数20点
    #はみ出しているか45点
    #枠がどれだけ埋まっているか45点
    #表情: 20
    return {"includeScore": 35 , "excludeScore": 10, "peopleScore": 10,"originalScore": 10,"faceScore": 10}

@app.post("/question4")
async def submit_score_question4(question: Question):
    # ここでスコアデータを処理します
    # 開発者の主観 20点
    # 人数 20点
    # はみ出しているか 45点
    # 枠がどれだけ埋まっているか 45点
    # 表情: 20

    num_of_questions = 4
    # Firebase Storageから画像をダウンロード
    image = await get_image_from_firebase(question.imageUrl)
    if image is None:
        raise HTTPException(status_code=500, detail="Failed to decode image")

    # 人数によるスコアを取得
    max_peaple_score = 20
    peaple_score, original_score_raito = peaple_and_developer_score(image, question.themeNumber, max_peaple_score)

    print(f'peaple_score: {peaple_score}')

    # 開発者の主観スコア
    original_score = original_score_raito * 20

    # お題の画像を取得
    theme_image_path = get_subject_image_path(num_of_questions, question.themeNumber)
    
    # はみ出している割合と含まれている割合を計算
    exclude_ratio, include_ratio = get_percent_from_theme(image, theme_image_path)

    include_score = include_ratio * 45
    exclude_score = (1 - exclude_ratio) * 45

    logging.info(f"include_ratio: {include_ratio}, hamidashi_ratio: {exclude_ratio}")

    # 表情のスコアを取得
    emotional_ratio =  get_face_score(image, num_of_questions, question.themeNumber)
    emotion_score = emotional_ratio * 20


    return {"includeScore": int(include_score) , "excludeScore": int(exclude_score), "peopleScore": int(peaple_score), "originalScore": original_score, "faceScore": int(emotion_score)}

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
