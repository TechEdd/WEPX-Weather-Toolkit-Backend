import cv2
import numpy as np
import os
import json

def image_to_colormap_text(image_path, value_min, value_max):
    # Load the image
    img = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)
    if img is None:
        raise ValueError(f"Could not read the image file: {image_path}")

    # Ensure the image has alpha channel, if not add one
    if img.shape[2] == 3:  # If no alpha channel, add one
        alpha_channel = np.full((img.shape[0], img.shape[1], 1), 255, dtype=img.dtype)  # Fully opaque
        img = np.concatenate((img, alpha_channel), axis=2)

    # Convert BGR to RGBA
    img = cv2.cvtColor(img, cv2.COLOR_BGRA2RGBA)

    # Get the width (number of color stops)
    height, width, _ = img.shape

    # Extract a single row from the image to get the colormap
    # Assume colormap is horizontally aligned
    colormap_row = img[height // 2]  # Take the middle row of the image

    # Linearly scale values between value_min and value_max
    values = np.linspace(value_min, value_max, width)

    # Generate the output colormap structure
    colormap_lines = []
    prev_color = None
    for i in range(width):
        color = colormap_row[i].tolist()
        if color != prev_color:  # Skip consecutive duplicate colors
            entry = {"value": round(values[i], 2), "color": color}
            colormap_lines.append(json.dumps(entry))
            prev_color = color

    # Write to a file with each entry on one line
    output_file = os.path.splitext(image_path)[0] + ".txt"
    with open(output_file, "w") as f:
        f.write("[\n")
        f.write(",\n".join(colormap_lines))
        f.write("\n]")

    print(f"Colormap saved to {output_file}")


# Example usage
if __name__ == "__main__":
    image_path = input("Enter the path to your image: ").strip()
    value_min = float(input("Enter the minimum value: ").strip())
    value_max = float(input("Enter the maximum value: ").strip())
    image_to_colormap_text(image_path, value_min, value_max)
