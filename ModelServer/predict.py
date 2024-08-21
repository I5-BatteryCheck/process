"""
******************************************************************************************
 * FileName      : prediect.py
 * Description   : Function to Perform Model Prediction and Organize Results
 * Author        : Dae ho Kang
 * Last modified : 2024.08.14
 ******************************************************************************************
"""


def predict(model, image_list, criteria):
    conf_criteria = criteria['conf_criteria']
    result_data ={}
    results = model(image_list)
    for i, result in enumerate(results):
        result_data[f'{i}'] = {}
        result_data[f'{i}']['cls'] = []
        result_data[f'{i}']['xyxy'] = []
        result_data[f'{i}']['conf'] = []

        for cls, xyxy, conf in zip(result.boxes.cls.tolist(),
                                   result.boxes.xyxy.tolist(), 
                                   result.boxes.conf.tolist()):
            if conf > conf_criteria:
                result_data[f'{i}']['cls'].append(cls)
                result_data[f'{i}']['xyxy'].append(xyxy)
                result_data[f'{i}']['conf'].append(conf)

        result_data[f'{i}']['len'] = len(result_data[f'{i}']['cls'])
        
    return result_data



#=========================================================================================
#
# SW_Bootcamp I5
#
#=========================================================================================