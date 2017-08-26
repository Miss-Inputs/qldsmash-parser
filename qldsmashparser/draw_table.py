from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
import cProfile
from qldsmashparser import *
import datetime


TOP_PADDING = 10
LEFT_PADDING = 10
ROW_PADDING = 5
COLUMN_PADDING = 10
LINE_WIDTH = 2
CELL_PADDING = 2
LINE_COLOUR = 'black'
HEADING_COLOUR = 'black'
CELL_COLOUR = 'black'

def autosize_font(width, height, text):
    point_size = 1
    font = ImageFont.truetype('Ubuntu-Medium.ttf', size=point_size)
    size = font.getsize(text)
    while size[0] < width and size[1] < height:
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
    This'd be a whole lot easier if I could use the HSV colour space tbh
    """
    try:
        number = float(value)
    except ValueError:
        return (224, 224, 224, 255)
    scale = number / scale_upper_bound
    red = int(255 - (255 * scale))
    green = int(255 * scale)
    blue = 0
    return (red, green, blue, 255)

def draw_table(table, colour_scale=None):
    """
    Yeah I know, I need to break this up a bit into smaller pieces
    Anyway, this actually draws the thing, and table better be
    a dict where the values are other dicts
    If you use colour_scale, it should be a number, it's for making colours
    in the background of cells that scale along with the numerical value
    of that cell, so if your values are 0-5 put 5 and if they're 0-100 put
    100 and I can't be bothered testing for any numbers being negative and
    what that would do
    """
    
    img = Image.new('RGBA', (5000, 5000), 'white')
    canvas = ImageDraw.Draw(img)
    heading_font = ImageFont.truetype('Ubuntu-Medium.ttf', size=20)
    
    left_border = 0
    box_height = 0
    row_line_offsets = []
    #Draw lines across the image at this Y position (offset
    #from where the top heading ends) (later)
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

    canvas.line([
                (left_border, 0),
                (left_border, box_height + top_border - ROW_PADDING)
                ], LINE_COLOUR, LINE_WIDTH)

    column_positions = {}
    last_column_position = left_border
    for key, value in table.items():
        for inner_key, inner_value in value.items():
            size = heading_font.getsize(inner_key)
            if inner_key in column_positions:
                position = column_positions[inner_key]
            else: 
                column_positions[inner_key] = position = last_column_position
                draw_text_vertically(img, inner_key, heading_font,
                                     (last_column_position, TOP_PADDING), HEADING_COLOUR)
                last_column_position += size[1]
                position += size[1] + COLUMN_PADDING
                canvas.line([
                            (position, 0), 
                            (position, box_height + top_border - ROW_PADDING)
                            ], LINE_COLOUR, LINE_WIDTH)
                last_column_position = position
            try:
                text = str(round(float(inner_value), 2))
                #I can't be stuffed importing the decimal package to remove trailing zeros
                text = text.rstrip('0').rstrip('.') if '.' in text else text
            except ValueError:
                text = inner_value
            text_font = autosize_font((size[1] + COLUMN_PADDING - (LINE_WIDTH * 1.5))-(CELL_PADDING * 2),
                                      row_heights[key] - (CELL_PADDING * 2) - (LINE_WIDTH * 1.5) - ROW_PADDING, text)
            text_x = column_positions[inner_key] + CELL_PADDING
            if (text_font.getsize(text)[0] + CELL_PADDING) < size[1]:
                text_x += size[1] - (text_font.getsize(text)[0] + CELL_PADDING)
            text_position = (text_x, row_positions[key] + top_border + CELL_PADDING)
            if colour_scale is not None:
                background_x = column_positions[inner_key] + LINE_WIDTH
                background_y = ((row_positions[key] + top_border) - CELL_PADDING) - LINE_WIDTH
                background_width = ((size[1] + COLUMN_PADDING) - LINE_WIDTH * 1.5)
                background_height = row_heights[key]
                background_box = [(background_x, background_y), 
                    (background_x + background_width, background_y + background_height)]
                background_colour = generate_colour_for_number(inner_value, colour_scale)
                canvas.rectangle(background_box, background_colour)
            canvas.text(text_position, text, CELL_COLOUR, text_font)
        canvas.text((0, row_positions[key] + top_border), key, HEADING_COLOUR, heading_font)

    for offset in row_line_offsets:
        canvas.line([
                    (0, top_border + offset),
                    (last_column_position, top_border + offset)
                    ], LINE_COLOUR, LINE_WIDTH)

    canvas.line([(0, top_border), (last_column_position, top_border)], LINE_COLOUR, LINE_WIDTH)

    return img.crop((0, 0, last_column_position, box_height + top_border - ROW_PADDING))

def main():
    #PR season starts at RotA 19 apparently (7 Dec 2016)
    table = get_act_matchup_table('set_win_rate', datetime.date(2016, 12, 7))
    image = draw_table(table, 100)
    image.save('output_win_rate.png')

if __name__ == "__main__":
    #main()
    cProfile.run('main()')