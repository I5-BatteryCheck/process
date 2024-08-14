def predict(model, image_list):
    criteria = 0.35
    result_data ={}
    results = model(image_list)
    for i, result in enumerate(results):
        result_data[f'{i}'] = {}
        result_data[f'{i}']['cls'] = []
        result_data[f'{i}']['xyxy'] = []

        for cls, xyxy, conf in zip(result.boxes.cls.tolist(),
                                   result.boxes.xyxy.tolist(), 
                                   result.boxes.conf.tolist()):
            if conf > criteria:
                result_data[f'{i}']['cls'].append(cls)
                result_data[f'{i}']['xyxy'].append(xyxy)

        result_data[f'{i}']['len'] = len(result_data[f'{i}']['cls'])
    return result_data