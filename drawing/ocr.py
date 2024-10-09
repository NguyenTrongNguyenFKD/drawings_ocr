import easyocr
from pdf2image import convert_from_path
from PIL import Image
import os
import cv2
import math
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
import re
import math

def pdf_to_png(pdf_path, output_folder):
    images = convert_from_path(pdf_path, dpi=120)
    png_files = []
    for i, img in enumerate(images):
        output_path = os.path.join(output_folder, f"page_{i+1}.png")
        img.save(output_path, 'PNG')
        png_files.append(output_path)
    return png_files


    reader = easyocr.Reader(['en'])  
    result = reader.readtext(image_path, detail=1)
    image = cv2.imread(image_path)
    height, width = image.shape[:2]
    x = int(width * 0.1)
    y = int(height * 0.1)
    for i, (bbox, text, prob) in enumerate(result):
        if 'material' in text.lower():
            # Lấy tọa độ bounding box (bbox)
            x_min = int(min(bbox[0][0], bbox[3][0]))  # Tọa độ x nhỏ nhất
            y_min = int(min(bbox[0][1], bbox[1][1]))  # Tọa độ y nhỏ nhất
            x_max = int(max(bbox[1][0], bbox[2][0]))  # Tọa độ x lớn nhất
            y_max = int(max(bbox[2][1], bbox[3][1]))  # Tọa độ y lớn nhất

            x_min = max(x_min - x, 0)
            y_min = max(y_min - y, 0)
            x_max = min(x_max + x, image.shape[1])
            y_max = min(y_max + y, image.shape[0])

            cropped_image = image[y_min:y_max, x_min:x_max]

            cropped_image_path = 'cropped_material.png'
            cv2.imwrite(cropped_image_path, cropped_image)
            print(f"Đã cắt và lưu hình ảnh: {cropped_image_path}")
            break 
        
def merge_bboxes(bbox1, bbox2):
    x_min = min(min(point[0] for point in bbox1), min(point[0] for point in bbox2))
    y_min = min(min(point[1] for point in bbox1), min(point[1] for point in bbox2))
    x_max = max(max(point[0] for point in bbox1), max(point[0] for point in bbox2))
    y_max = max(max(point[1] for point in bbox1), max(point[1] for point in bbox2))
    merged_bbox = [(x_min, y_min), (x_max, y_min), (x_max, y_max), (x_min, y_max)]
    return merged_bbox

def merge_close_texts(result, distance_threshold=15):
    temp_text = None
    prev_bbox = None
    gr_list = []
    temp_list = []
    joined_list = []
    for i, (bbox, text, _) in enumerate(result):
        if i in joined_list:
            continue 
        if not  temp_list:
            total_box = bbox
            prev_bbox = (text,bbox)
            temp_list.append(prev_bbox)
            joined_list.append(i)
        else:
            for j, (sbox, stext, _) in enumerate(result):
                if j in joined_list:
                    continue
                distance = bbox_edge_distance(sbox, total_box)
                if distance < distance_threshold:
                    total_box = merge_bboxes(total_box, sbox)
                    temp_list.append((stext,sbox))
                    joined_list.append(j)
            gr_list.append(temp_list)
            temp_list =[]
    for i, group in enumerate(gr_list):
        gr_list[i] = sorted(group, key=lambda x: get_y_min(x[1]))
    return gr_list
            

def bbox_edge_distance(bbox1, bbox2):
    x1_min, y1_min = min(point[0] for point in bbox1), min(point[1] for point in bbox1)
    x1_max, y1_max = max(point[0] for point in bbox1), max(point[1] for point in bbox1)
    x2_min, y2_min = min(point[0] for point in bbox2), min(point[1] for point in bbox2)
    x2_max, y2_max = max(point[0] for point in bbox2), max(point[1] for point in bbox2)
    dx = max(0, x2_min - x1_max, x1_min - x2_max)  # Khoảng cách theo trục x
    dy = max(0, y2_min - y1_max, y1_min - y2_max)  # Khoảng cách theo trục y
    return math.sqrt(dx**2 + dy**2)

def distance_point_to_rect(material_center, bbox):
    center_x, center_y = material_center
    x_min = min([point[0] for point in bbox])
    x_max = max([point[0] for point in bbox])
    y_min = min([point[1] for point in bbox])
    y_max = max([point[1] for point in bbox])
    dx = max(x_min - center_x, 0, center_x - x_max)  # Khoảng cách dọc theo trục x
    dy = max(y_min - center_y, 0, center_y - y_max)  # Khoảng cách dọc theo trục y
    distance = math.sqrt(dx**2 + dy**2)
    return distance

def get_x_min(bbox):
    return min(point[0] for point in bbox)

def get_y_min(bbox):
    return min(point[1] for point in bbox)



def Find_nearKey(image_path):
    reader = easyocr.Reader(['en'])  
    result = reader.readtext(image_path, detail=1)
    result_fit = merge_close_texts(result)
    res_list = []
    for g in result_fit:
        combined_text = ' '.join(t for t, b in g)
        res_list.append(combined_text)
        
    for b in res_list:
        if 'material' in b.lower():
            key_text = b.lower()
            # print(key_text)
            cleaned_text = re.search(r'material(.*?)(?=\.|$)', key_text, flags=re.IGNORECASE)
            # cleaned_text = re.search(r'material\s*:(.*?)(?=\s*material|\.|$)', key_text, flags=re.IGNORECASE)
            if cleaned_text is not None:
                cleaned_text = cleaned_text.group(1).strip()
                if len(cleaned_text) >= 4:
                    nearest_text = cleaned_text
                    print(nearest_text)
                    return nearest_text
                    
                    
def process_pdf(pdf_path, output_folder):
    png_files = pdf_to_png(pdf_path, output_folder)
    for png_file in png_files:
        print(f"Processing {png_file}...")
        Find_nearKey(png_file)
        
output_folder = 'output_images'
if not os.path.exists(output_folder):
    os.makedirs(output_folder)
pdf_path = r'D:\compare_3d\drawing\data_drawing\8151716 X2_Redacted.pdf'
process_pdf(pdf_path, output_folder)

# D:/compare_3d/drawing/data_drawing/930-73886_-_REDACTED.pdf
# D:/compare_3d/drawing/data_drawing/72745020_Rev_B_redacted.pdf