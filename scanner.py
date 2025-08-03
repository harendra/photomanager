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
                return datetime.strptime(date_str, '%Y:%m:%d %H:%M:%S').isoformat()
    except (AttributeError, KeyError, IndexError, ValueError):
        pass

    mod_time = os.path.getmtime(image_path)
    return datetime.fromtimestamp(mod_time).isoformat()

def process_single_image(filepath):
    """Processes a single image file and returns its metadata dictionary."""
    try:
        with Image.open(filepath) as img:
            width, height = img.size

        date_taken = get_date_taken(filepath)
        date_modified = datetime.fromtimestamp(os.path.getmtime(filepath)).isoformat()
        filesize = os.path.getsize(filepath)

        return {
            'filepath': filepath,
            'filename': os.path.basename(filepath),
            'date_taken': date_taken,
            'date_modified': date_modified,
            'filesize': filesize,
            'width': width,
            'height': height
        }
    except UnidentifiedImageError:
        print(f"Could not identify image file: {filepath}")
    except Exception as e:
        print(f"Error processing {filepath}: {e}")
    return None

def scan_directories(dir_list):
    """
    Performs a smart scan of all directories in the list.
    Adds new images, and removes images that are no longer on disk.
    """
    print("Starting smart scan...")
    database.create_table()

    # 1. Get all filepaths from the database
    db_filepaths = database.get_all_filepaths()

    # 2. Find all image files on disk
    disk_filepaths = set()
    for directory in dir_list:
        if not os.path.isdir(directory):
            continue
        for root, _, files in os.walk(directory):
            for file in files:
                if any(file.lower().endswith(ext) for ext in SUPPORTED_EXTENSIONS):
                    disk_filepaths.add(os.path.join(root, file))

    # 3. Determine what's new and what's deleted
    new_files = disk_filepaths - db_filepaths
    deleted_files = db_filepaths - disk_filepaths

    # 4. Add new files to the database
    if new_files:
        print(f"Found {len(new_files)} new images to add.")
        for filepath in new_files:
            image_data = process_single_image(filepath)
            if image_data:
                database.insert_image(image_data)
                print(f"Added: {filepath}")

    # 5. Remove deleted files from the database
    if deleted_files:
        print(f"Found {len(deleted_files)} images to remove.")
        conn = database.get_db_connection()
        for filepath in deleted_files:
            conn.execute("DELETE FROM images WHERE filepath = ?", (filepath,))
            print(f"Removed: {filepath}")
        conn.commit()
        conn.close()

    print("Smart scan complete.")
