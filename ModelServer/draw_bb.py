import os
import cv2
import numpy as np
import matplotlib.pyplot as plt


def draw_bb(image_path_list, result, crop_point, img_path):
    boxed_image_path_list = []
    class_names = ['battery', 'damaged', 'pollution']

    # setting
    color = [(0, 255, 0), (255, 0, 0), (0, 0, 255)]
    thickness = 2

    # one picture unit
    for i in range(len(image_path_list)):
        image_path = image_path_list[i]
        image = cv2.imread(image_path)

        # detected object in one picture unit
        for c, box in zip(result[f'{i}']['cls'], result[f'{i}']['xyxy']):
            box = list(map(int, box))
            x_min = int(box[0] +crop_point[i][0])
            y_min = int(box[1] +crop_point[i][1])
            x_max = int(box[2] +crop_point[i][0])
            y_max = int(box[3] +crop_point[i][1])
            # Draw the rectangle
            cv2.rectangle(image, (x_min, y_min), (x_max, y_max), color[int(c)], thickness)

            # draw the label
            label = class_names[int(c)]
            label_position = (x_min, y_min - 10)
            cv2.putText(image, label, label_position, cv2.FONT_HERSHEY_SIMPLEX, 0.5, color[int(c)], thickness)

        # save boxed image
        boxed_image_path = os.path.join( img_path, f'boxed_image_{i}.jpg')
        boxed_image_path_list.append( boxed_image_path)
        cv2.imwrite( boxed_image_path, image)

    return boxed_image_path_list