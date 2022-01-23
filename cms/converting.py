def feet_tu_cm(height):
    height = str(height).split('.')
    height = round((12 * int(height[0]) + int(height[1])) * 2.54)
    if height < 50:
        height = 50
    if height > 260:
        height = 260
    return height

def cm_to_feet(value):
    value_ft = round(value // 30.48)
    value_in = round((value / 30.48 - value // 30.48) * 12)
    value = (float(str(value_ft) + "." + str(value_in)))
    if value < 1.8:
        value = 1.8
    if value > 8.7:
        value = 8.7
    return value


