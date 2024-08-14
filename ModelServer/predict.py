def predict(model, img_list):

    result_data ={}
    results = model(img_list)
    for i, result in enumerate(results):
        result_data[f'{i}'] = {}
        result_data[f'{i}']['len'] = len(result.boxes.cls.tolist())
        result_data[f'{i}']['cls'] = result.boxes.cls.tolist()
        result_data[f'{i}']['conf'] = result.boxes.conf.tolist()
        result_data[f'{i}']['xyxy'] = result.boxes.xyxy.tolist()

    return result_data