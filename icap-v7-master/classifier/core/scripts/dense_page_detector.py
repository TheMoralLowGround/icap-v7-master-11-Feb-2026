import os
import json
import numpy as np
import pandas as pd
import shutil
from PIL import Image, ImageDraw
from sklearn.linear_model import LogisticRegression
import joblib


def word_density_calculator(file_path, dpi=600, height=800, width=1200):
    # Load the image
    img = Image.open(file_path)
    img.info["dpi"] = (dpi, dpi)
    # Convert the image to grayscale
    gray_image = img.convert("L")
    gray_image = gray_image.resize((width, height), Image.BILINEAR)
    gray_image.info["dpi"] = (dpi, dpi)
    # Convert grayscale image to a 2D matrix
    matrix = list(gray_image.getdata())
    # Reshape the matrix to the image size
    matrix = [
        matrix[i : i + gray_image.width]
        for i in range(0, len(matrix), gray_image.width)
    ]
    # calculate distance between words
    distance, chunks = find_distance(matrix)
    avg_span = avg_distance(distance)
    # print(chunks)
    # draw_lines(gray_image,chunks)
    # return find_max_horizontal_line_length(matrix)
    return avg_span


def find_max_horizontal_line_length(image_matrix, threshold=225):
    max_distance = 0
    max_count = 0
    gap = 2
    for row in range(0, len(image_matrix) - 5):
        first_black_pixel = -1
        last_black_pixel = -1
        for c in range(0, len(image_matrix[0]) - 5):
            if image_matrix[row][c] <= threshold:
                last_black_pixel = c
                if first_black_pixel == -1:
                    first_black_pixel = c
            elif c - last_black_pixel == gap:
                if -3 <= ((last_black_pixel - first_black_pixel) - max_distance) <= 3:
                    max_count += 1
                elif (last_black_pixel - first_black_pixel) > max_distance + 3:
                    max_distance = last_black_pixel - first_black_pixel
                    max_count = 1
                last_black_pixel = -1
                first_black_pixel = -1

        if c == (len(image_matrix[0]) - 6):
            if -3 <= ((last_black_pixel - first_black_pixel) - max_distance) <= 3:
                max_count += 1
            elif (last_black_pixel - first_black_pixel) > max_distance + 3:
                max_distance = last_black_pixel - first_black_pixel
                max_count = 1
    return max_distance, max_count


def remove_horizontal_lines(image_matrix, row, threshold):
    gap = 1
    min_distance = 200
    first_black_pixel = -1
    last_black_pixel = -1

    for c in range(0, len(image_matrix[0])):

        if (
            c >= len(image_matrix) - 1
            and last_black_pixel - first_black_pixel >= min_distance
        ):
            for i in range(first_black_pixel, last_black_pixel + 1):
                image_matrix[row][i] = 255
            last_black_pixel = -1
            first_black_pixel = -1

        if image_matrix[row][c] <= threshold:
            last_black_pixel = c
            if first_black_pixel == -1:
                first_black_pixel = c

        elif (
            c - last_black_pixel >= gap
            and last_black_pixel - first_black_pixel >= min_distance
        ):
            for i in range(first_black_pixel, last_black_pixel + 1):
                image_matrix[row][i] = 255
            last_black_pixel = -1
            first_black_pixel = -1

        else:
            last_black_pixel = -1
            first_black_pixel = -1

            # print(last_black_pixel-first_black_pixel)

    return image_matrix


def find_distance(image_matrix, threshold=225):
    row_gap = 5
    distance = []
    chunks = []

    for r in range(0, len(image_matrix) - 5, row_gap):
        # for c in range(5,len(image_matrix)-5):
        # if image_matrix[r][c]<=threshold:
        # find_lines(image_matrix, r, 0,threshold)
        image_matrix = remove_horizontal_lines(image_matrix, r, threshold)
        # distance.append(calculate_gaps(image_matrix, r, 0,threshold))
        d, c = chunk_size(image_matrix, r, threshold)
        distance.append(d)
        chunks.append(c)
    """           
    matrix = np.array(image_matrix, dtype=np.uint8)

    # Convert the array to a grayscale image
    image = Image.fromarray(matrix, mode = 'L')
    image.show()
    """
    return distance, chunks


def chunk_size(image_matrix, r, threshold):
    gap = 6
    distance = []
    chunk = []
    first_pixel = None
    last_pixel = None

    for c in range(len(image_matrix[0])):
        if image_matrix[r][c] <= threshold and c != len(image_matrix[0]) - 1:
            last_pixel = c
            if first_pixel == None:
                first_pixel = c

        elif last_pixel != None and c - last_pixel >= gap:
            chunk.append((first_pixel, r, last_pixel, r))
            distance.append(last_pixel - first_pixel)
            first_pixel = None
            last_pixel = None

        if c == len(image_matrix[0]) - 1 and first_pixel != None:
            chunk.append((first_pixel, r, last_pixel, r))
            distance.append(last_pixel - first_pixel)

    return distance, chunk


def avg_distance(all_distance):
    # print(all_distance)
    avg_coverage = []
    count = 0
    total_distance = 0
    row_count = 0
    for i in all_distance:
        if len(i) > 0:
            row_count += 1
            count += len(i)
            s = round(sum(i) / 1200, 4)
            avg_coverage.append(s)
            # print(s)
            total_distance += s
            # print(total_distance)
        else:
            avg_coverage.append(0)
    """
    #print(row_count, count)
    if count!=0:
        return total_distance/len(all_distance)
    else:
        return 0
    """
    return avg_coverage


def draw_lines(img, coordinates):
    # Open the image
    draw = ImageDraw.Draw(img)
    for box in coordinates:
        if len(box) > 0:
            for lines in box:
                # Extract coordinates
                left, top, right, bottom = lines

                # Draw box
                draw.rectangle([(left, top), (right, bottom)], fill="red", width=3)

    # Show the image
    img.show()


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
