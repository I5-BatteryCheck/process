from PIL import Image, ImageDraw, ImageFont


def draw_bb(image_list, result, crop_point):
    boxed_image_list = []
    class_names = ['battery', 'damaged', 'pollution']

    # setting
    color = [(0, 255, 0), (255, 0, 0), (0, 0, 255)]
    thickness = 2

    # one picture unit
    for i in range(len(image_list)):
        image = image_list[i]

        # detected object in one picture unit
        for c, box in zip(result[f'{i}']['cls'], result[f'{i}']['xyxy']):
            box = list(map(int, box))
            x_min = int(box[0] +crop_point[i][0])
            y_min = int(box[1] +crop_point[i][1])
            x_max = int(box[2] +crop_point[i][0])
            y_max = int(box[3] +crop_point[i][1])

            # Draw the rectangle
            draw = ImageDraw.Draw(image)
            draw.rectangle([x_min, y_min, x_max, y_max], 
                           outline=color[int(c)], width=thickness)
            
            # draw the label
            label = class_names[int(c)]
            label_position = (x_min, y_min - 30)
            font = ImageFont.truetype("arial.ttf", size=30)
            draw.text(label_position, label, font=font, fill=color[int(c)])

        # save boxed image
        boxed_image_list.append(image)

    return boxed_image_list