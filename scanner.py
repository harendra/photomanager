import os
from PIL import Image, UnidentifiedImageError
from datetime import datetime
import database

# EXIF tag for date taken
EXIF_DATE_TAG = 36867

SUPPORTED_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.gif', '.bmp']

def get_date_taken(image_path):
    """
    Extracts the date taken from an image's EXIF data.
    Falls back to file modification time if EXIF data is not available.
    """
    try:
        with Image.open(image_path) as img:
            exif_data = img._getexif()
            if exif_data and EXIF_DATE_TAG in exif_data:
                date_str = exif_data[EXIF_DATE_TAG]
                # EXIF date format is 'YYYY:MM:DD HH:MM:SS'
                return datetime.strptime(date_str, '%Y:%m:%d %H:%M:%S').isoformat()
    except (AttributeError, KeyError, IndexError):
        # Fallback to file modification time
        pass

    # Fallback to file modification time if EXIF fails
    mod_time = os.path.getmtime(image_path)
    return datetime.fromtimestamp(mod_time).isoformat()


def scan_directory(path):
    """
    Scans a directory for images, extracts metadata, and stores it in the database.
    """
    database.create_table()
    for root, _, files in os.walk(path):
        for file in files:
            if any(file.lower().endswith(ext) for ext in SUPPORTED_EXTENSIONS):
                filepath = os.path.join(root, file)
                try:
                    with Image.open(filepath) as img:
                        width, height = img.size

                    date_taken = get_date_taken(filepath)
                    date_modified = datetime.fromtimestamp(os.path.getmtime(filepath)).isoformat()
                    filesize = os.path.getsize(filepath)

                    image_data = {
                        'filepath': filepath,
                        'filename': file,
                        'date_taken': date_taken,
                        'date_modified': date_modified,
                        'filesize': filesize,
                        'width': width,
                        'height': height
                    }
                    database.insert_image(image_data)
                    print(f"Scanned: {filepath}")

                except UnidentifiedImageError:
                    print(f"Could not identify image file: {filepath}")
                except Exception as e:
                    print(f"Error processing {filepath}: {e}")
