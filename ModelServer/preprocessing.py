import os
import random
from PIL import Image


def preprocess(model, img_path_list, img_path):
    Pad = 0.2
    cropped_image_path_list = []

    # model predict 
    results = model(img_path_list)

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
        image = Image.open(img_path_list[i])
        image_width, image_height = image.size
        image_width = int(image_width)
        image_height =int(image_height)

        # battery found
        if x1_list:
            xmin = min(x1_list)
            ymin = min(y1_list)
            xmax = max(x2_list)
            ymax = max(y2_list)

            # find crop box
            X1 = int(xmin -image_width *(0.05* random.randint(0, 1)) +Pad)
            Y1 = int(ymin -image_height*(0.05* random.randint(0, 1)) +Pad)
            X2 = int(xmax +image_width *(0.05* random.randint(0, 1)) +Pad)
            Y2 = int(ymax +image_height*(0.05* random.randint(0, 1)) +Pad)
            
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
            cropped_image = image.crop((Crop_x1, Crop_y1, Crop_x2, Crop_y2))

        # battery not found
        else:
            cropped_image = image
            print(f'not found battery_{i} in PREPROCESS')

        # save cropped image
        cropped_image_path = os.path.join( img_path, f'cropped_img_{i}.jpg')
        cropped_image_path_list.append( cropped_image_path)
        cropped_image.save( cropped_image_path)
            
    return cropped_image_path_list