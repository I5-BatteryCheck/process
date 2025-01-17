"""
******************************************************************************************
 * FileName      : preprocessing.py
 * Description   : Function to Black Crop Images for Enhanced Detection
 * Author        : Dae ho Kang
 * Last modified : 2024.08.14
 ******************************************************************************************
"""


import random
from PIL import Image, ImageDraw


def preprocess(model, img_list, pad):
    cons_pad = pad['cons_pad']
    rand_pad = pad['rand_pad']
    cropped_image_list = []
    crop_point = []
    # model predict 
    results = model(img_list)

    # one picture unit
    for i, result in enumerate(results):
        x1_list = []
        y1_list = []
        x2_list = []
        y2_list = []

        # get xyxy_data
        for x1, y1, x2, y2 in result.boxes.xyxy.tolist():
            x1_list.append(x1)
            y1_list.append(y1)
            x2_list.append(x2)
            y2_list.append(y2)

        # open image
        image = img_list[i]
        image_width, image_height = image.size
        image_width = int(image_width)
        image_height =int(image_height)

        # battery found
        if x1_list:
            xmin = min(x1_list)
            ymin = min(y1_list)
            xmax = max(x2_list)
            ymax = max(y2_list)

            a = max([xmax-xmin, ymax-ymin])

            # find crop box
            X1 = int(xmin -a *(rand_pad *random.randint(0, 1) +cons_pad))
            Y1 = int(ymin -a *(rand_pad *random.randint(0, 1) +cons_pad))
            X2 = int(xmax +a *(rand_pad *random.randint(0, 1) +cons_pad))
            Y2 = int(ymax +a *(rand_pad *random.randint(0, 1) +cons_pad))
            
            # black crop 
            black_image = Image.new('RGB', image.size, (0, 0, 0))
            mask = Image.new('L', image.size, 0)
            draw = ImageDraw.Draw(mask)
            draw.rectangle([X1,Y1,X2,Y2], fill=255)
            result_image = Image.composite(image, black_image, mask)

            W = X2-X1
            H = Y2-Y1
            CX = (X1+X2)//2
            CY = (Y1+Y2)//2
            
            if W > H :
                A = W
            else :
                A = H
            
            Crop_x1 = CX-(A//2)
            Crop_x2 = CX+(A//2)
            Crop_y1 = CY-(A//2)
            Crop_y2 = CY+(A//2)
            
            if Crop_x1 <0:
                Crop_x1 = 0
                Crop_x2 = A
                
            if Crop_y1 <0:
                Crop_y1 = 0
                Crop_y2 = A
                
            if Crop_x2 > image_width:
                Crop_x1 = image_width - A
                Crop_x2 = image_width
            
            if Crop_y2 > image_height:
                Crop_y1 = image_height - A
                Crop_y2 = image_height

            # crop image & save
            cropped_image = result_image.crop((Crop_x1, Crop_y1, Crop_x2, Crop_y2))

        # battery not found
        else:
            cropped_image = image
            print(f'not found battery_{i} in PREPROCESS')
            Crop_x1, Crop_y1 = 0, 0
        # save cropped image

        cropped_image_list.append(cropped_image)
        crop_point.append([Crop_x1, Crop_y1])
            
    return cropped_image_list, crop_point



#=========================================================================================
#
# SW_Bootcamp I5
#
#=========================================================================================