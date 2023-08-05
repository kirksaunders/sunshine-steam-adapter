import os
from PIL import Image

def convert_to_png(src_img_path: str, dest_img_dir_path: str) -> str:
    # Create destination directory if it doesn't exist
    if not os.path.exists(dest_img_dir_path):
        os.makedirs(dest_img_dir_path)

    img = Image.open(src_img_path)
    new_path = os.path.join(dest_img_dir_path, f"{os.path.splitext(os.path.basename(src_img_path))[0]}.png")
    img.save(new_path)
    print(f"Converted {src_img_path} to png and saved to {new_path}")
    return new_path