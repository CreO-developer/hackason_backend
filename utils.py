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
from rembg import remove, new_session

# Firebaseの初期化
cred = credentials.Certificate('./firebase.json')
if not firebase_admin._apps:
    firebase_admin.initialize_app(cred, {"storageBucket": "prehackson22.appspot.com"})

bucket = storage.bucket()

# rembgのセッションを新しく作成
session = new_session("u2net")

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
    # 画像をPIL形式に変換
    image_pil = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))

    # rembgを使用して背景を透過させる
    output_image = remove(image_pil, session=session)

    # アルファマットを生成
    alpha_image = remove(image_pil, session=session, post_process_mask=True, only_mask=True)

    # 透過画像をRGB形式に変換
    alpha_image_rgb = alpha_image.convert("RGB")

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

    # 含まれている割合を計算
    include_ratio = white_area_of_include / whole_area_of_theme

    return hamidashi_ratio, include_ratio

def get_subject_image_path(num_of_questions:int, num_of_theme:int):
    image_path = f"./images/question{num_of_questions}/theme{num_of_theme}.png"
    return image_path

# 画像から人を検出する関数
def detect_people_in_image(image):
    hog = cv2.HOGDescriptor()
    hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())
    (rects, weights) = hog.detectMultiScale(image, winStride=(4, 4), padding=(8, 8), scale=1.05)
    return len(rects)

def get_score_num_of_people(image, theme_num:int, max_peaple_score:int):
    #  人数を検出
    num_of_people = detect_people_in_image(image)
    print(num_of_people)

    # お題によって適切な人数を取得
    appropriate_number = 0
    if theme_num >= 1 & theme_num <= 5:
        appropriate_number = 1
    elif theme_num >= 6 & theme_num <= 10:
        appropriate_number = 2
    elif theme_num >= 11 & theme_num <= 15:
        appropriate_number = 4
    else:
        appropriate_number = 0
    
    # 人数によるスコアを取得
    if num_of_people == appropriate_number:
        return max_peaple_score
    else:  
        return max_peaple_score - (np.abs(num_of_people - appropriate_number) * 5) if 15 - (np.abs(num_of_people - appropriate_number) * 5) > 0 else 0
