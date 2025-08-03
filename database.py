import sqlite3

def get_db_connection():
    """Establishes a connection to the database."""
    conn = sqlite3.connect('photo_library.db')
    conn.row_factory = sqlite3.Row
    return conn

def create_table():
    """Creates the images table if it doesn't exist."""
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS images (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filepath TEXT NOT NULL UNIQUE,
            filename TEXT NOT NULL,
            date_taken TEXT,
            date_modified TEXT,
            filesize INTEGER,
            width INTEGER,
            height INTEGER,
            llm_tags TEXT
        )
    ''')
    conn.commit()
    conn.close()

def get_all_images(sort_by='date_taken', order='desc'):
    """Fetches all images from the database, with sorting."""
    conn = get_db_connection()
    # Basic validation to prevent SQL injection on column names
    if sort_by not in ['date_taken', 'filename'] or order not in ['asc', 'desc']:
        sort_by = 'date_taken'
        order = 'desc'

    images = conn.execute(f'SELECT * FROM images ORDER BY {sort_by} {order}').fetchall()
    conn.close()
    return images

def get_image_by_id(image_id):
    """Fetches a single image from the database by its ID."""
    conn = get_db_connection()
    image = conn.execute('SELECT * FROM images WHERE id = ?', (image_id,)).fetchone()
    conn.close()
    return image

def update_llm_tags(image_id, tags):
    """Updates the llm_tags for a specific image."""
    conn = get_db_connection()
    # Tags are stored as a comma-separated string
    tags_str = ",".join(tags)
    conn.execute('UPDATE images SET llm_tags = ? WHERE id = ?', (tags_str, image_id))
    conn.commit()
    conn.close()

def get_images_without_tags():
    """Fetches all images that have not been tagged yet."""
    conn = get_db_connection()
    images = conn.execute('SELECT * FROM images WHERE llm_tags IS NULL').fetchall()
    conn.close()
    return images

def search_images_by_tag(query):
    """Searches for images by a tag in the llm_tags column."""
    conn = get_db_connection()
    # The '%' are wildcards for the LIKE query
    search_term = f"%{query}%"
    images = conn.execute('SELECT * FROM images WHERE llm_tags LIKE ? ORDER BY date_taken DESC', (search_term,)).fetchall()
    conn.close()
    return images

def get_available_years():
    """Returns a sorted list of distinct years from the database."""
    conn = get_db_connection()
    # SUBSTR(date_taken, 1, 4) extracts the year from 'YYYY-MM-DD...'
    years = conn.execute("SELECT DISTINCT SUBSTR(date_taken, 1, 4) as year FROM images ORDER BY year DESC").fetchall()
    conn.close()
    return [row['year'] for row in years]

def remove_images_by_path(folder_path):
    """Removes all image records from the database that are in a specific folder."""
    conn = get_db_connection()
    # Use a wildcard to match all files in the folder and subfolders
    path_pattern = f"{folder_path}%"
    cursor = conn.execute("DELETE FROM images WHERE filepath LIKE ?", (path_pattern,))
    print(f"Deleted {cursor.rowcount} records from path: {folder_path}")
    conn.commit()
    conn.close()

def get_all_filepaths():
    """Returns a set of all filepaths currently in the database."""
    conn = get_db_connection()
    paths = conn.execute("SELECT filepath FROM images").fetchall()
    conn.close()
    return {row['filepath'] for row in paths}

def get_images_by_year(year):
    """Fetches all images from the database for a specific year."""
    conn = get_db_connection()
    # Using LIKE to match the start of the date_taken string
    year_pattern = f"{year}%"
    images = conn.execute("SELECT * FROM images WHERE date_taken LIKE ? ORDER BY date_taken ASC", (year_pattern,)).fetchall()
    conn.close()
    return images

def insert_image(image_data):
    """Inserts a new image record into the database."""
    conn = get_db_connection()
    # Using INSERT OR IGNORE to avoid errors on duplicate filepaths
    # This might happen if we re-scan a directory
    conn.execute('''
        INSERT OR IGNORE INTO images (filepath, filename, date_taken, date_modified, filesize, width, height)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        image_data['filepath'],
        image_data['filename'],
        image_data['date_taken'],
        image_data['date_modified'],
        image_data['filesize'],
        image_data['width'],
        image_data['height']
    ))
    conn.commit()
    conn.close()
