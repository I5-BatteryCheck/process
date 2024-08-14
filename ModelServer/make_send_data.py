def make_send_data(uploaded_data, fine_result):
    # criteria
    damaged_criteria = 0.01
    pollution_criteria =0.05

    # classes
    classes =['BATTERY', 'DAMAGED', 'POLLUTION']
    
    # measure battery exist & defect level
    damaged_level = 0
    pollution_level = 0
    battery_exist_list = [1] *len(fine_result)
    image_num = len(fine_result)
    for i in range(image_num):
        num  =fine_result[f'{i}']['len']
        cls  =fine_result[f'{i}']['cls']
        xyxy =fine_result[f'{i}']['xyxy']

        # measure battery exist
        if (num == 0) or (0 not in cls):
            battery_exist_list[i] = 0
            continue
        
        # measure defect level
        battery = [[],[],[],[]]
        for cl, xy in zip(cls, xyxy):
            damaged_area =0
            pollution_are=0
            if cl ==0:
                battery_exist_list[i] += 1
                battery[0].append(xy[0])
                battery[1].append(xy[1])
                battery[2].append(xy[2])
                battery[3].append(xy[3])
            elif cl ==1:
                damaged_area  +=(xy[2]-xy[0]) *(xy[3]-xy[1])
            else:
                pollution_are +=(xy[2]-xy[0]) *(xy[3]-xy[1])

        fine_result[f'{i}']['battery_outline'] = {
            'xmin' : min(battery[0]),
            'ymin' : min(battery[1]),
            'xmax' : max(battery[2]),
            'ymax' : max(battery[3])}
        battery_area = (max(battery[2])-min(battery[0])) *(max(battery[3])-min(battery[1])) +1
        damaged_level   +=damaged_area  /battery_area
        pollution_level +=pollution_are /battery_area

    # Result
    # 3 picture in not exist -> false
    battery_exist = 1
    for i in battery_exist_list:
        battery_exist*=i

    # Result defect
    if battery_exist ==0:
        fine_result['result'] = "BOTH"
        fine_result['isNormal'] = False
    elif damaged_level> damaged_criteria and pollution_level> pollution_criteria:
        fine_result['result'] = "BOTH"
        fine_result['isNormal'] = False
    elif damaged_level<= damaged_criteria and pollution_level> pollution_criteria:
        fine_result['result'] = "POLLUTION"
        fine_result['isNormal'] = False
    elif damaged_level> damaged_criteria and pollution_level<= pollution_criteria:
        fine_result['result'] = "DAMAGED"
        fine_result['isNormal'] = False
    else:
        fine_result['result'] = "NORMAL"
        fine_result['isNormal'] = True



    # Make data to send Mainserver
    data2MS = {}
    data2MS['result']=fine_result['result']
    data2MS['testDate'] = uploaded_data['time']
    data2MS['temperature'] = uploaded_data['Temperature']
    data2MS['humidity'] = uploaded_data['humidity']
    data2MS['illuminance'] = uploaded_data['lightLevel']
    data2MS['gas'] = uploaded_data['gas']
    data2MS['frequencies'] = uploaded_data['frequencies']
    data2MS['fft_magnitude'] = uploaded_data['fft_magnitude']
    data2MS["damagedLevel"] = round(damaged_level *100, 1)
    data2MS["pollutionLevel"] = round(pollution_level *100, 1)
    data2MS['cameraDefects'] = []
    for i in range(image_num):
        cameraDefects = {}
        cameraDefects['cameraNumber'] = i+1
        cameraDefects['batteryOutline'] = {}
        cameraDefects['defects'] = []
        for cls, xyxy in zip(fine_result[f'{i}']['cls'], fine_result[f'{i}']['xyxy']):
            if cls ==0:
                cameraDefects['batteryOutline'] ={
                    'xmin' : int(fine_result[f'{i}']['battery_outline']['xmin']),
                    'ymin' : int(fine_result[f'{i}']['battery_outline']['ymin']),
                    'xmax' : int(fine_result[f'{i}']['battery_outline']['xmax']),
                    'ymax' : int(fine_result[f'{i}']['battery_outline']['ymax'])}
            else:
                cameraDefects['defects'].append({
                    'type' : classes[int(cls)],
                    'xmin' : int(xyxy[0]),
                    'ymin' : int(xyxy[1]),
                    'xmax' : int(xyxy[2]),
                    'ymax' : int(xyxy[3])})

        data2MS['cameraDefects'].append(cameraDefects)

    # Make data to send RaspberryPi server
    data2RP = {'isNormal' : fine_result['isNormal']}


    return data2RP, data2MS