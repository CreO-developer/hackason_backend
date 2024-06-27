from ultralytics import YOLO

def object_detection(image):
    model = YOLO(model="yolov8n.pt")  # Detectionの最小Paramモデル
    results = model.predict(source=image)  # 推論

    # 出力の確認
    print(f'type:{type(results)}, len:{len(results)}')
    print(type(results[0]))

    # 検出されたpersonの人数を数える
    person_count = 0
    has_laptop = False
    has_car = False
    has_pottedplant = False
    has_cell_phone = False

    for result in results:
        # 'person'クラスのIDは通常0です。これを確認してください。
        person_count += (result.boxes.cls == 0).sum()
        
        # 'laptop', 'car', 'pottedplant', 'cell phone'のクラスIDを確認する
        has_laptop = has_laptop or (result.boxes.cls == 63).sum() > 0
        has_car = has_car or (result.boxes.cls == 2).sum() > 0
        has_pottedplant = has_pottedplant or (result.boxes.cls == 58).sum() > 0
        has_cell_phone = has_cell_phone or (result.boxes.cls == 67).sum() > 0

    print(f'Number of persons detected: {person_count}')
    print(f'Laptop detected: {has_laptop}')
    print(f'Car detected: {has_car}')
    print(f'Pottedplant detected: {has_pottedplant}')
    print(f'Cell phone detected: {has_cell_phone}')
    
    return person_count, has_laptop, has_car, has_pottedplant, has_cell_phone

