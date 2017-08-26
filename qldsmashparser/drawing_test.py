# To change this license header, choose License Headers in Project Properties.
# To change this template file, choose Tools | Templates
# and open the template in the editor.

import os
import random
from PIL import Image, ImageDraw, ImageFont
random.seed()

table = {'Foo': {'Foo': 'N/A', 'Bar': 2, 'Baz': 1}, 'Bar': {'Foo': 3, 'Bar': 'N/A', 'Baz': 4}, 'Baz': {'Foo': 4, 'Bar': 1, 'Baz': 'N/A'}}

TOP_PADDING = 10
LEFT_PADDING = 10
ROW_PADDING = 5
COLUMN_PADDING = 10
LINE_WIDTH = 2
CELL_PADDING = 2
LINE_COLOUR = 'black'
HEADING_COLOUR = 'black'
CELL_COLOUR = 'black'

#img = Image.new('RGBA', (500, 500), (0, 0, 0, 0))
img = Image.new('RGBA', (500, 500), 'white')
canvas = ImageDraw.Draw(img)
heading_font = ImageFont.truetype('Ubuntu-Medium.ttf', size=20)
#cell_font = ImageFont.truetype('Ubuntu-Medium.ttf', size=14)

def autosize_font(width, text):
    point_size = 1
    font = ImageFont.truetype('Ubuntu-Medium.ttf', size=point_size)
    size = font.getsize(text)
    while size[1] < width:
        font = ImageFont.truetype('Ubuntu-Medium.ttf', size=point_size)
        size = font.getsize(text)
        point_size += 1
    return font

def draw_text_vertically(source, text, font, position, fill):
    size = font.getsize(text)
    temp = Image.new('RGBA', size)
    draw = ImageDraw.Draw(temp)
    draw.text((0, 0), text, fill, font)
    rotated = temp.rotate(90, expand=True)
    source.paste(rotated, position, rotated)
    return rotated.size

def generate_colour_for_number(value, scale_upper_bound=100):
    """
    This will just be a scale between red and green and
    non-numeric values being gray because I said so
    """
    try:
        number = int(value)
    except ValueError:
        return (224, 224, 224, 255)
    scale = number / scale_upper_bound
    red = int(255 - (255 * scale))
    green = int(255 * scale)
    blue = 0
    print(value, red, green, blue)
    return (red, green, blue, 255)
    pass

#canvas.rectangle([(100, 200), (300, 400)], 'blue')
print(canvas.textsize('dickbutt'))
left_border = 0
box_height = 0
row_line_offsets = [] #Draw lines across the image at this Y position (offset
#from where the top heading ends)
row_positions = {}
row_heights = {}
for key in table.keys():
    size = canvas.textsize(key, heading_font)
    if size[0] > left_border:
        left_border = size[0]
    row_heights[key] = (ROW_PADDING * 3) + size[1]
    box_height += ROW_PADDING
    row_positions[key] = box_height
    box_height += (ROW_PADDING * 2) + size[1]
    row_line_offsets.append(box_height)
left_border += LEFT_PADDING + COLUMN_PADDING

top_border = 0
for key, value in table.items():
    for inner_key, inner_value in value.items():
        size = heading_font.getsize(inner_key)
        if size[0] > top_border:
            #Using the text width since it will be rotated
            top_border = size[0]
top_border += TOP_PADDING + ROW_PADDING

canvas.line([(left_border, 0), (left_border, box_height + top_border - ROW_PADDING)], LINE_COLOUR, LINE_WIDTH)

column_positions = {}
last_column_position = left_border
for key, value in table.items():
    for inner_key, inner_value in value.items():
        size = heading_font.getsize(inner_key)
        if inner_key in column_positions:
            position = column_positions[inner_key]
        else: 
            #last_column_position += size[1]
            column_positions[inner_key] = position = last_column_position
            draw_text_vertically(img, inner_key, heading_font, (last_column_position, TOP_PADDING), HEADING_COLOUR)
            last_column_position += size[1]
            position += size[1] + COLUMN_PADDING
            canvas.line([(position, 0), (position, box_height + top_border - ROW_PADDING)], LINE_COLOUR, LINE_WIDTH)
            canvas.line([(0, top_border), (last_column_position, top_border)], LINE_COLOUR, LINE_WIDTH)
            last_column_position = position
        #canvas.rectangle([(column_positions[inner_key], row_positions[key] + top_border), (column_positions[inner_key] + 5, row_positions[key] + top_border + 5)], 'red')
        text = str(inner_value)
        text_font = autosize_font((size[1] + 0)-(CELL_PADDING * 2), text)
        #text_position = (column_positions[inner_key] + (size[1] - text_font.getsize(text)[0]), row_positions[key] + top_border + CELL_PADDING)
        text_x = column_positions[inner_key] + CELL_PADDING
        if (text_font.getsize(text)[0] + CELL_PADDING) < size[1]:
            text_x += size[1] - (text_font.getsize(text)[0] + CELL_PADDING)
        text_position = (text_x, row_positions[key] + top_border + CELL_PADDING)
        background_x = column_positions[inner_key] + LINE_WIDTH
        background_y = ((row_positions[key] + top_border) - CELL_PADDING) - LINE_WIDTH
        background_width = ((size[1] + COLUMN_PADDING) - LINE_WIDTH * 1.5)
        background_height = row_heights[key]
        background_box = [(background_x, background_y), (background_x + background_width, background_y + background_height)]
        #background_colour = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
        background_colour = generate_colour_for_number(inner_value, 5)
        canvas.rectangle(background_box, background_colour)
        canvas.text(text_position, text, CELL_COLOUR, text_font)
    canvas.text((0, row_positions[key] + top_border), key, HEADING_COLOUR, heading_font)
        
for offset in row_line_offsets:
    canvas.line([(0, top_border + offset), (last_column_position, top_border + offset)], LINE_COLOUR, LINE_WIDTH)
        
canvas.line([(0, top_border), (last_column_position, top_border)], LINE_COLOUR, LINE_WIDTH)

img = img.crop((0, 0, last_column_position, box_height + top_border - ROW_PADDING))
        
#vertical_position = 0
#for key in table.keys():        
#    canvas.text((0, vertical_position), key, 'black', font)
#    vertical_position += 10 + size[1]
#    canvas.line([(0, vertical_position), (img.width, vertical_position)], 'blue', 2)
#    vertical_position += 5
    
#canvas.line([(left_border + 10, 0), (left_border + 10, vertical_position - 5)], 'blue', 2)

#draw_text_vertically(img, 'Vaginas! Haha', (left_border + 15, 5), 'green')

print(img)
#print(img.show(command='qiv'))
print(img.save('boobs.png'))
os.system('qiv boobs.png')
