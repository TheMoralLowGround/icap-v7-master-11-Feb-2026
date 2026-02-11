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
