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
