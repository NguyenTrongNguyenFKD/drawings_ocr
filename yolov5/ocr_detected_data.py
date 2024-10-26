import os
import cv2
import easyocr
from PIL import Image
import math
import re
import math
import csv

names = {
    0: 'table',
    1: 'material',
    2: 'part_number',
    3: 'finish',  
    4: 'dwg_no',
    5: 'drawn',
    6: 'ds_engineer',
    7: 'note',
    8: 'material_size'
}
 
def yolo_to_corners(txt_file, img_width, img_height):
    corners = []
    with open(txt_file, 'r') as file:
        for line in file.readlines():
            class_id, center_x, center_y, width, height = map(float, line.split())
            # Convert YOLO format to (x1, y1, x2, y2)
            x1 = (center_x - width / 2) * img_width
            y1 = (center_y - height / 2) * img_height
            x2 = (center_x + width / 2) * img_width
            y2 = (center_y + height / 2) * img_height
            corners.append((class_id, x1, y1, x2, y2))
    corners.sort(key=lambda x: x[0])
    return corners

def convert_txt_to_4point_coordinates(labels_dir, images_dir):
    object_list = []
    for txt_file in os.listdir(labels_dir):
        if txt_file.endswith('.txt'):
            img = {}
            image_name = txt_file.replace('.txt', '.png')
            image_path = os.path.join(images_dir, image_name)
            image = cv2.imread(image_path)
            img_height, img_width = image.shape[:2]
            txt_file_path = os.path.join(labels_dir, txt_file)
            corners = yolo_to_corners(txt_file_path, img_width, img_height)
            img[image_path] = corners
            object_list.append(img)
    return object_list


def is_within_bbox(bbox, x1, y1, x2, y2):
    bbox_x1, bbox_y1 = min(b[0] for b in bbox), min(b[1] for b in bbox)
    bbox_x2, bbox_y2 = max(b[0] for b in bbox), max(b[1] for b in bbox)
    bbox_area = (bbox_x2 - bbox_x1) * (bbox_y2 - bbox_y1)
    inter_x1, inter_y1 = max(bbox_x1, x1), max(bbox_y1, y1)
    inter_x2, inter_y2 = min(bbox_x2, x2), min(bbox_y2, y2)
    if inter_x1 >= inter_x2 or inter_y1 >= inter_y2:
        return False
    intersection_area = (inter_x2 - inter_x1) * (inter_y2 - inter_y1)
    return intersection_area >= 0.5 * bbox_area

def intable(table, bbox):
    for region in table:
        if not isinstance(region, (list, tuple)) or len(region) != 4:
            raise ValueError("Mỗi phần tử trong table phải là một tuple hoặc list chứa đúng 4 giá trị.")
        x_intersect_min = max(region[0], bbox[0])
        y_intersect_min = max(region[1], bbox[1])
        x_intersect_max = min(region[2], bbox[2])
        y_intersect_max = min(region[3], bbox[3])
        bbox_area = (bbox[2] - bbox[0]) * (bbox[3] - bbox[1])
        if x_intersect_max <= x_intersect_min or y_intersect_max <= y_intersect_min:
            continue 
        intersect_area = (x_intersect_max - x_intersect_min) * (y_intersect_max - y_intersect_min)
        overlap_ratio = intersect_area / bbox_area
        if overlap_ratio >= 0.8:
            return True  
    return False  

def  process_string(string):
    if string[0] == "material":
        if re.search(r'material[:\s]*', string[1], flags=re.IGNORECASE):
            if ':' in string[1][string[1].lower().index("material") + len("material"):]:
                str = re.sub(r'^.*?material[:\s]*', '', string[1], flags=re.IGNORECASE)
                return str
            return re.sub(r'material\s*', '', string[1], flags=re.IGNORECASE)
    if string[0] == "part_number":
        if re.search(r'part number[:\s]*', string[1], flags=re.IGNORECASE):
            if ':' in string[1][string[1].lower().index("part number") + len("part number"):]:
                str = re.sub(r'^.*?part number[:\s]*', '', string[1], flags=re.IGNORECASE)
                return str
            return re.sub(r'part number\s*', '', string[1], flags=re.IGNORECASE)
        
        if re.search(r'part no[:\s]*', string[1], flags=re.IGNORECASE):
            if ':' in string[1][string[1].lower().index("part no") + len("part no"):]:
                str = re.sub(r'^.*?part no[:\s]*', '', string[1], flags=re.IGNORECASE)
                return str
            return re.sub(r'part no\s*', '', string[1], flags=re.IGNORECASE)
        # str = re.sub(r'identify with part number', '', string[1], flags=re.IGNORECASE)
        # str = re.sub(r'part number', '', string[1], flags=re.IGNORECASE)
        # str = re.sub(r'part no', '', string[1], flags=re.IGNORECASE)
        # str = re.sub(r'identifying no', '', string[1], flags=re.IGNORECASE)       
        # str = re.sub(r'identify', '', string[1], flags=re.IGNORECASE)
        # print(str)
    return string[1]
            
        

def Get_data_formPDF(list_find,object_list):
    csv_file_path = 'output_data.csv'
    with open(csv_file_path, mode='w', newline='', encoding='utf-8') as csvfile:
        csv_writer = csv.writer(csvfile)
        csv_writer.writerow(['class_name', 'extracted_text'])
        for obj in object_list:
            for key, data in obj.items():
                print(f"Processing image: {key}")
                csv_writer.writerow([f"Processing image: {key}"])
                reader = easyocr.Reader(['en']) 
                ocr_results = reader.readtext(key, detail=1)
                datas = []
                table = []
                for class_id, x1, y1, x2, y2 in data:
                    if class_id == 0:
                        table.append((x1, y1, x2, y2))
                        continue
                    if class_id not in list_find[1:]:                              
                        continue
                    strings = ""
                    flag_table = False
                    if intable(table,(x1, y1, x2, y2)):
                            flag_table = True
                    for (bbox, text, confidence) in ocr_results:
                        if is_within_bbox(bbox, x1, y1, x2, y2):
                            strings = strings +" "+ text
                    # print(class_id, ":", strings)
                    datas.append((names[class_id],strings, flag_table))
                for d in datas:
                    processed_data = process_string(d)
                    # print(d[0],d[2],":",processed_data)
                    
                    csv_writer.writerow((d[0],d[2],":",processed_data))

    
def main():
    # Example usage:
    labels_dir = r"./runs/detect/exp8/labels"
    images_dir = r"./datasets/test" 
    object_list = convert_txt_to_4point_coordinates(labels_dir, images_dir)
    list_find = [0,1,2,3,4]
    Get_data_formPDF(list_find,object_list)
    # for obj in object_list:
    #     for key, data in obj.items():
    #         print(f"Processing image: {key}")
    #         images = cv2.imread(key)
    #         reader = easyocr.Reader(['en']) 
    #         ocr_results = reader.readtext(key, detail=1)
    #         for class_id, x1, y1, x2, y2 in data:
    #             strings = ""
    #             cv2.rectangle(images, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)
    #             for (bbox, text, confidence) in ocr_results:
    #                 if is_within_bbox(bbox, x1, y1, x2, y2):
    #                     strings = strings + text
    #             print(class_id, ":", strings)
    #         output_image_path = os.path.join(images_dir, os.path.basename(key))
    #         cv2.imwrite(output_image_path, images)
    #         print(f"Saved processed image to {output_image_path}")

                
    
    
    
if __name__ == "__main__":
    main()