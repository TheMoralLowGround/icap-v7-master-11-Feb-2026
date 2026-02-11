from PIL import Image
from core.dense_page_detector.processing.line_processing import find_distance
from core.dense_page_detector.processing.utils import avg_distance

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
