import os
import joblib
import numpy as np
from core.dense_page_detector.processing.image_processing import word_density_calculator
from sklearn.linear_model import LogisticRegression

def detect_dense_pages(
    img_folders, model_path, threshold=0.35, supported_formats=(".tiff", ".tif", ".png")
):
    model = joblib.load(model_path)
    img_details = {}
    for folder_path in img_folders:
        for foldername, subfolders, filenames in sorted(os.walk(folder_path)):
            for filename in sorted(filenames):
                # Check if the file has a .xml extension
                if filename.endswith(supported_formats):
                    file_path = os.path.join(foldername, filename)
                    chunk_size = word_density_calculator(file_path)
                    img_details[file_path] = chunk_size
                    # print(chunk_size)
                else:
                    file_path = os.path.join(foldername, filename)
                    # print(supported_formats," file formats are only supported. error in ", file_path)
      
    b = list(img_details.values())
    b_single_flat = np.array(b).reshape(len(b), -1)
    pred_prob = model.predict_proba(b_single_flat)
    results = []
    for prob in pred_prob:
        if prob[1] >= threshold:
            results.append(1)
        else:
            results.append(0)
    count = 0
    for file_path in img_details:
        img_details[file_path] = results[count]
        count += 1
    return img_details