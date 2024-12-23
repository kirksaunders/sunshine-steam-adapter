from pathlib import Path
from PIL import Image

def convert_to_png(src_img_path: Path, dest_img_dir_path: Path) -> Path:
    # Create destination directory if it doesn't exist
    dest_img_dir_path.mkdir(parents=True, exist_ok=True)

    img = Image.open(src_img_path)
    new_path = dest_img_dir_path / f"{src_img_path.stem}.png"
    img.save(new_path)
    print(f"Converted {src_img_path} to png and saved to {new_path}")
    return new_path