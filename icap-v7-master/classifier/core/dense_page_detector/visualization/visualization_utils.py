from PIL import ImageDraw

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