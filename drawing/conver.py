import os
from pdf2image import convert_from_path

def pdf_to_png_in_folder(input_folder, output_folder):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    for file_name in os.listdir(input_folder):
        if file_name.endswith('.pdf'):
            pdf_path = os.path.join(input_folder, file_name)
            print(f"Converting {pdf_path} to PNG...")
            images = convert_from_path(pdf_path, dpi=100)
            for i, img in enumerate(images):
                output_path = os.path.join(output_folder, f"{os.path.splitext(file_name)[0]}_page_{i+1}.png")
                img.save(output_path, 'PNG')

output_folder = 'output_pdf'
pdf_path = r'D:\compare_3d\drawing\data_drawing'
pdf_to_png_in_folder(pdf_path, output_folder)