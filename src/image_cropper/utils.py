import rasterio


def load_image(image_path):
    
    return rasterio.open(image_path)

def save_cropped_image(image_data, output_path):
    with rasterio.open(output_path, 'w', driver='GTiff', height=image_data.shape[0], width=image_data.shape[1], count=3, dtype=image_data.dtype) as dst:
        dst.write(image_data)

def extract_image_attributes(image_data):
    # Placeholder for extracting attributes from image data
    return {
        "mean": image_data.mean(),
        "min": image_data.min(),
        "max": image_data.max(),
    }