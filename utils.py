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
from PIL import Image, ImageOps
from ultralytics import YOLO
from deepface import DeepFace
from yolo import object_detection

# Firebaseの初期化
cred = credentials.Certificate('./firebase.json')
if not firebase_admin._apps:
    firebase_admin.initialize_app(cred, {"storageBucket": "prehackson22.appspot.com"})

bucket = storage.bucket()




async def get_image_from_firebase(image_url):
    try:
        blob = bucket.blob(image_url)
        image_url = blob.generate_signed_url(version='v4', expiration=timedelta(seconds=300), method='GET')
        response = requests.get(image_url)
        if response.status_code != 200:
            return None
        image_array = np.array(bytearray(response.content), dtype=np.uint8)
        image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
        return image
    except Exception as e:
        print(f"Error fetching image from Firebase: {e}")
        return None

def get_percent_from_theme(image, theme_image_path):
    # YOLOセグメンテーションモデルのロード
    yolo_model = YOLO(model="yolov8n-seg.pt")
    # 画像をPIL形式に変換
    image_pil = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))

    # YOLOによるセグメンテーションを実行
    results = yolo_model.predict(source=np.array(image_pil))

    # セグメンテーションマスクを取得
    segmentation_masks = results[0].masks.data
    classes = results[0].boxes.cls

    # 'person'クラスのIDは通常0です。これを確認してください。
    person_class_id = 0

    # 人に対するマスクを抽出
    person_mask = np.zeros(segmentation_masks[0].shape, dtype=np.uint8)
    person_count = 0
    for i, mask in enumerate(segmentation_masks):
        if classes[i] == person_class_id:
            person_mask = np.maximum(person_mask, mask.cpu().numpy())
            person_count += 1

    if person_count == 0:
        return 0, 0

    # 人にマスクされた箇所を白、それ以外を黒にするバイナリマスクを生成
    binary_mask = (person_mask > 0).astype(np.uint8) * 255

    # バイナリマスクをRGB形式に変換
    alpha_image_rgb = Image.fromarray(binary_mask).convert("RGB")

    # PNG画像ファイルのパス
    image_path = theme_image_path

    # 画像を読み込む
    image_flactal = Image.open(image_path).convert("L")

    # 透過画像と背景画像を合成するために背景を準備
    back_im1 = alpha_image_rgb.copy()
    back_im2 = alpha_image_rgb.copy()

    # 透過画像に白い領域を合成
    back_im1.paste(image_flactal, (0, 0), image_flactal)
    back_im2.paste(image_flactal, (0, 0), ImageOps.invert(image_flactal))

    # PIL ImageからNumPy配列に変換
    image_flactal_np = np.array(image_flactal)
    back_im1_np = np.array(back_im1)
    back_im2_np = np.array(back_im2)

    # 白い領域の面積を計算
    whole_area_of_theme = cv2.countNonZero(image_flactal_np)
    white_area_of_hamidashi = cv2.countNonZero(cv2.cvtColor(back_im1_np, cv2.COLOR_RGB2GRAY))
    white_area_of_include = cv2.countNonZero(cv2.cvtColor(back_im2_np, cv2.COLOR_RGB2GRAY))

    print(whole_area_of_theme)
    print(white_area_of_hamidashi)
    print(white_area_of_include)

    # はみ出している割合を計算
    hamidashi_ratio = (white_area_of_hamidashi / whole_area_of_theme) - 1
    hamidashi_ratio = 0 if hamidashi_ratio < 0 else hamidashi_ratio
    hamidashi_ratio = 1 if hamidashi_ratio > 1 else hamidashi_ratio

    # 含まれている割合を計算
    include_ratio = white_area_of_include / whole_area_of_theme

    print(f'hamidashi_ratio: {1 - hamidashi_ratio}')
    print(f'include_ratio: {include_ratio}')

    return (1 - hamidashi_ratio), include_ratio


def get_subject_image_path(num_of_questions:int, num_of_theme:int):
    image_path = f"./images/question{num_of_questions}/theme{num_of_theme}.png"
    return image_path


def peaple_and_developer_score(image, theme_num:int, max_peaple_score:int):
    #  人数を検出
    num_of_people, has_laptop, has_car, has_pottedplant, has_cell_phone = object_detection(image)
    print(f'num_of_people: {num_of_people}')

    print(f'theme_num: {theme_num}')

    # 開発者の主観スコア
    developer_score_ratio = 0.5
    if has_laptop:
        developer_score_ratio += 0.25
    if has_car:
        developer_score_ratio += 0.25
    if has_pottedplant:
        developer_score_ratio += 0.25
    if has_cell_phone:
        developer_score_ratio -= 0.25
    if num_of_people > 5:
        developer_score_ratio += 0.25
    
    if developer_score_ratio > 1:
        developer_score_ratio = 1
    if developer_score_ratio < 0:
        developer_score_ratio = 0

    # お題によって適切な人数を取得
    appropriate_number = 0
    if theme_num >= 1 and theme_num < 6:
        appropriate_number = 1
    elif theme_num >= 6 and theme_num < 11:
        appropriate_number = 2
    elif theme_num >= 11 and theme_num < 16:
        appropriate_number = 4
    else:
        appropriate_number = 0
    
    print(f'appropriate_number: {appropriate_number}')
    
    # 人数によるスコアを取得
    if num_of_people == appropriate_number:
        return max_peaple_score, developer_score_ratio
    elif num_of_people == 0:
        return 0, developer_score_ratio
    else:  
        return max_peaple_score - (np.abs(num_of_people - appropriate_number) * 5) if 15 - (np.abs(num_of_people - appropriate_number) * 5) > 0 else 0, developer_score_ratio
    

def get_face_score(image, num_of_question:int, theme_num:int):
    try:
        # DeepFaceを使用して感情を判定
        results = DeepFace.analyze(image, actions=['age', 'gender', 'emotion'])

        # 最初の顔情報を取得
        result = results[0]
        
        print(f'emotion_result: {result}')

        # 感情によるスコアを取得
        emotion_score_ratio = 0.4
        if num_of_question == 3:
            target_emotion = 'happy'
        elif num_of_question == 4:
            switcher = {
                1: 'angry',
                2: 'sad',
                3: 'neutral',
                4: 'happy',
                0: 'surprise'
            }
            target_emotion = switcher.get(theme_num % 5, 'neutral')
        else:
            target_emotion = 'neutral'

        add_score_ratio = result['emotion'][target_emotion] * 0.6 / 100
        emotion_score_ratio = emotion_score_ratio + add_score_ratio

    except Exception as e:
        print(f'Error in DeepFace analysis: {e}')
        # 顔が読み取れなかった場合のデフォルトのスコア
        emotion_score_ratio = 0.4

    return emotion_score_ratio
