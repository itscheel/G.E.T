from pdf2image import convert_from_path
from PIL import Image

import boto3
import matplotlib.pyplot as plt
import cv2
import pandas as pd
import numpy as np
import time
import os
from botocore.config import Config
BOUNDING_BOX_KEYS = ['Width', 'Height', 'Left', 'Top']

def select_random_sample_from_list(l):
    n = len(l)
    index = np.random.randint(n)
    return l[index]

def convert_img_to_bytes(file):
    with open(file, 'rb') as f:
        source_bytes = f.read()
    return source_bytes

def draw_bounding_box(img, bounding_box, text='', block_type = ''):
    block_type_colors = {
        'WORD': (255, 0, 0), 
        'LINE': (0, 255, 0), 
        'CELL': (0, 0, 255), 
        'TABLE': (255, 255, 0), 
        'PAGE': (255, 0, 255),
        'SELECTION_ELEMENT': (150, 150, 150),
    }
    color = block_type_colors[block_type] if block_type in block_type_colors.keys() else (0, 255, 255)

    width = img.shape[1]
    height = img.shape[0]
    w, h = int(bounding_box[0]*width), int(bounding_box[1]*height)
    x, y = int(bounding_box[2]*width), int(bounding_box[3]*height)
    cv2.rectangle(img, (x, y), (x+w, y+h), color, 3)
    cv2.putText(img, text, (x, y+20), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 0, 255), 2, cv2.LINE_AA)
    return img

def plot_image(image, title=''):
    fig = plt.figure(figsize=(15, 15))
    plt.title(title)
    plt.imshow(image)
    plt.show()

def plot_image_bounding_boxes(file_path, bounding_boxes, block_types=None, text=None, text_size=None):
    if block_types is None:
        block_types = ['' for i in range(len(bounding_boxes))]
    if text is None:
        text = ['' for i in range(len(bounding_boxes))]

    img_bounding_boxes = cv2.imread(file_path)
    for index, bounding_box in enumerate(bounding_boxes):
        draw_bounding_box(
            img_bounding_boxes,
            bounding_box,
            text=text[index],
            block_type=block_types[index],
        )
    plot_image(img_bounding_boxes, title=file_path)

def get_relationship_type_ids(ids, relationships):
    relationships_type = []
    relationships_ids = []
    for relationship in relationships:
        try:
            relationship = relationship[0]
            relationships_type.append(relationship['Type'])
            relationships_ids.append(
                [ids[ids == id_].index[0] for id_ in relationship['Ids']]
            )            
        except:
            relationships_type.append(None)
            relationships_ids.append(None)
    return relationships_type, relationships_ids

def get_father_ids(children_ids):
    father_id = [[] for index in range(len(children_ids))]
    for index, relationship_ids in enumerate(children_ids):
        if isinstance(relationship_ids, list):
            [father_id[id_].append(index) for id_ in relationship_ids]
    return father_id

def get_analyze_document(analyze_document, plot=False):

    # Data cleaning
    analyze_document['Relationship_type'], analyze_document['Relationship_ids'] = get_relationship_type_ids(
        analyze_document['Id'], analyze_document['Relationships']
    )
    analyze_document.drop('Relationships', axis=1, inplace=True)

    analyze_document['Father_id'] = get_father_ids(analyze_document['Relationship_ids'])

    analyze_document['Bounding_box'] = analyze_document['Geometry'].map(lambda x: tuple(x['BoundingBox'].values()))
    analyze_document.drop('Geometry', axis=1, inplace=True)

    analyze_document['Text'] = analyze_document['Text'].fillna('')

    # Plot image and bounding boxes
    if plot:
        plot_image_bounding_boxes(file_path, analyze_document['Bounding_box'], list(analyze_document['BlockType']))

    return analyze_document

def get_blocktypes_indexes(blocktype_serie, blocktypes):
        return [index for index, block in enumerate(blocktype_serie) if block in blocktypes]

def get_blocktype_bounding_boxes(analyze_document, blocktypes):
    blocktype_indexes = get_blocktypes_indexes(analyze_document['BlockType'], blocktypes)
    bounding_boxes = analyze_document.iloc[blocktype_indexes]
    return bounding_boxes

def get_table_values(analyze_document, file_path, plot=False):
    table_cells = analyze_document[
        ['BlockType', 'Text', 'RowIndex', 'ColumnIndex', 'Relationship_ids', 'Father_id', 'Bounding_box']
    ]
    table_cells = table_cells[table_cells['BlockType'] == 'CELL']
    table_cells['Father_id'] = table_cells['Father_id'].map(lambda x: x[0])

    cell_text = []
    for cell_children in table_cells['Relationship_ids']:
        cell_text.append(
            ' '.join(list(analyze_document['Text'].iloc[cell_children].values)) 
            if cell_children is not None else None
        )
    table_cells['Text'] = cell_text
    table_cells['Text'].fillna('', inplace=True)

    if(plot):
        plot_image_bounding_boxes(file_path, list(table_cells['Bounding_box']), text=list(table_cells['Text']))

    df_table = []
    for table_father in table_cells['Father_id'].unique():
        table_text = table_cells[table_cells['Father_id'] == table_father]
        for index, row in enumerate(table_text['RowIndex'].unique()):
            df_table.append(
                [table_father] + list(table_text[table_text['RowIndex'] == row]['Text'].values)
            )
    df_table = pd.DataFrame(df_table)

    null_columns = df_table.isnull().sum()
    null_columns = null_columns[null_columns == len(df_table)].index
    df_table.drop(null_columns, axis=1, inplace=True)

    return df_table

def is_point_inside_box(point, box):
    if box[2] <= point[0] and point[0] <= box[2] + box[0]:
        if box[3] <= point[1] and point[1] <= box[3] + box[1]:
            return True 
    return False

def is_box_inside_box(small_box, big_box):
    points = [
        (small_box[2], small_box[3]), 
        (small_box[2] + small_box[0], small_box[3]), 
        (small_box[2]               , small_box[3] + small_box[1]), 
        (small_box[2] + small_box[0], small_box[3] + small_box[1])
    ]
    for point in points:
        if not is_point_inside_box(point, big_box):
            return False
    return True

def is_box_partially_inside_box(small_box, big_box):
    points = [
        (small_box[2], small_box[3]), 
        (small_box[2] + small_box[0], small_box[3]), 
        (small_box[2]               , small_box[3] + small_box[1]), 
        (small_box[2] + small_box[0], small_box[3] + small_box[1])
    ]
    for point in points:
        if is_point_inside_box(point, big_box):
            return True
    return False

def are_boxes_inside_box(boxes, big_box):
    return [is_box_inside_box(box, big_box) for box in boxes]

def are_boxes_complete_or_partially_inside_box(boxes, big_box):
    return [is_box_inside_box(box, big_box) or is_box_partially_inside_box(box, big_box) for box in boxes]

def is_box_inside_any_box(box, boxes):
    for box_ in boxes:
        if box == box_:
            continue
        if is_box_inside_box(box, box_):
            return True
    return False

def get_text(analyze_document, file_path, plot=False):
    table_bounding_boxes = get_blocktype_bounding_boxes(analyze_document, ['TABLE'])
    line_word_bounding_boxes = get_blocktype_bounding_boxes(analyze_document, ['LINE', 'WORD'])

    if len(table_bounding_boxes) > 0:
        # Select line and word block type rows that do not belong to a table
        paragraph_content = []
        for table_bounding_box in table_bounding_boxes['Bounding_box']:
            paragraph_content.append(
                are_boxes_inside_box(
                    line_word_bounding_boxes['Bounding_box'].values, table_bounding_box
                )
            )
        selected_paragraphs = paragraph_content[0]
        for paragraph in paragraph_content[1:]:
            selected_paragraphs = [selected_paragraphs[idx] or paragraph[idx] for idx in range(len(selected_paragraphs))]
        selected_paragraphs = [not a for a in selected_paragraphs]
        text_indexes = line_word_bounding_boxes.iloc[selected_paragraphs].index
    else:
        text_indexes = line_word_bounding_boxes.index

    # Remove duplicate bounding boxes
    paragraph_content = analyze_document.iloc[text_indexes]
    paragraph_content = analyze_document.iloc[paragraph_content.Father_id.map(lambda x: x[0] in paragraph_content.index).index]
    paragraph_content = paragraph_content[['Text', 'Bounding_box']]
    paragraph_content = paragraph_content.iloc[
        [not(is_box_inside_any_box(bounding_box, paragraph_content['Bounding_box'])) for bounding_box in paragraph_content['Bounding_box']]
    ]
    paragraph_content.reset_index(drop=True, inplace=True)

    if plot:
        plot_image_bounding_boxes(file_path, paragraph_content['Bounding_box'])

    # Get lines
    lines_idx = []
    if len(paragraph_content) > 0:
        line = [paragraph_content['Bounding_box'][0]]
        line_idx = [0]
        x_coordinate = line[0][3]
        tolerance = line[0][1] / 2.0
        for index, bounding_box in enumerate(paragraph_content['Bounding_box'][1:]):
            if np.abs(x_coordinate - bounding_box[3]) < tolerance:
                line.append(bounding_box)
                line_idx.append(index+1)
            else:
                lines_idx.append(line_idx)
                line = [bounding_box]
                line_idx = [index+1]
                x_coordinate = line[0][3]
                tolerance = line[0][1] / 2.0
        lines_idx.append(line_idx)
    lines_text = []
    for line_idx in lines_idx:
        lines_text.append([paragraph_content['Text'][idx] for idx in line_idx])
    lines_text = pd.DataFrame(lines_text)
    
    return lines_text

def aws_analyze_document(file_path, plot=False):
    # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/textract.html#Textract.Client.analyze_document
    # AWS Textract request
    My_config = Config(
    region_name = 'us-west-2')
    client_textract = boto3.client('textract', config=My_config)
    analyze_document_original = pd.DataFrame(
        client_textract.analyze_document(
            Document={'Bytes': convert_img_to_bytes(file_path)},
            FeatureTypes=['TABLES'],
        )['Blocks']
    )
    analyze_document = get_analyze_document(analyze_document_original, plot=plot)
    return analyze_document   

def image_preprocessing(file_path, plot=False):
    return
    # AWS Textract has its own way to preprocess images
    image = cv2.imread(file_path, cv2.IMREAD_COLOR)
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    gray_image = cv2.bitwise_not(gray_image)
    ret, binary_image = cv2.threshold(gray_image, 32, 255, cv2.THRESH_BINARY)

    image = binary_image.copy()
    Image.fromarray(image).save(file_path)

    if plot:
        fig = plt.figure(figsize=(15, 15))
        plt.imshow(image)

def get_aws_analyze_document(file_path):
    if file_path.split('.')[-1] == 'pdf':
        pdf_pages = convert_from_path(file_path, dpi=200)
        file_paths = []
        for index, pdf_page in enumerate(pdf_pages):
            file_paths.append(file_path[:-4] + '_p%d.jpg' % index)
            pdf_page.save(file_paths[-1], 'JPEG')
            image_preprocessing(file_paths[-1], plot=False)
        df_tables = []
        df_text = []
        for file_path in file_paths:
            analyze_document = aws_analyze_document(file_path)
            df_tables.append(get_table_values(analyze_document, file_path, plot=False))
            df_text.append(get_text(analyze_document, file_path, plot=False))        
    else:
        image_preprocessing(file_path, plot=False)
        analyze_document = aws_analyze_document(file_path)
        df_tables = get_table_values(analyze_document, plot=False)
        df_text = get_text(analyze_document, plot=False)
    return (df_tables, df_text)
