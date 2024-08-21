"""
******************************************************************************************
 * FileName      : Model_Server.py
 * Description   : Flask Server for Serving the Model
 * Author        : Dae ho Kang
 * Last modified : 2024.08.18
 ******************************************************************************************
"""



from ensemble_boxes import *

def ensemble(predicts, cropped_image_list):
    
    n_model = len(predicts)
    n_image = len(cropped_image_list)
    
    iou_thr = 0.5
    weights = [1] *n_model
    skip_box_thr = 0.0001
    
    img_w = []
    img_h = []
    for image in cropped_image_list:
        w, h = image.size
        img_w.append(w)
        img_h.append(h)
    
    result = {}
    for i in range(n_image):
        result[f'{i}'] = {}
    
    for i in range(n_image):

        labels_list = []
        scores_list = []
        boxes_list  = [[] for i in range(n_model)]
        for m in range(n_model):
            labels_list.append(predicts[m][f'{i}']['cls']) 
            scores_list.append(predicts[m][f'{i}']['conf'])
            
            for xyxy in predicts[m][f'{i}']['xyxy']:
                ins = []
                ins.append(xyxy[0] / img_w[i])
                ins.append(xyxy[1] / img_h[i])
                ins.append(xyxy[2] / img_w[i])
                ins.append(xyxy[3] / img_h[i])
                boxes_list[m].append(ins)
        
        boxes, scores, labels = weighted_boxes_fusion(
            boxes_list, scores_list, labels_list, 
            weights=weights, iou_thr=iou_thr, skip_box_thr=skip_box_thr)
        
        labels = list(labels)
        scores = list(scores)
        new_boxes = []
        for xyxy in boxes:
            ins = []
            ins.append(xyxy[0] * img_w[i])
            ins.append(xyxy[1] * img_h[i])
            ins.append(xyxy[2] * img_w[i])
            ins.append(xyxy[3] * img_h[i])
            new_boxes.append(ins)
            
        result[f'{i}']['cls'] = labels
        result[f'{i}']['xyxy'] = new_boxes
        result[f'{i}']['conf'] = scores
        result[f'{i}']['len'] = len(labels)

    return result



#=========================================================================================
#
# SW_Bootcamp I5
#
#=========================================================================================
