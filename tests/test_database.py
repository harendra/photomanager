import pytest
import sqlite3
from unittest.mock import patch
import database

@pytest.fixture
def memory_db():
    """Fixture to set up an in-memory SQLite database for testing."""
    # Use patch to replace the get_db_connection function
    with patch('database.get_db_connection') as mock_get_conn:
        # Make the mock return a new in-memory database connection each time
        conn = sqlite3.connect(':memory:')
        conn.row_factory = sqlite3.Row
        mock_get_conn.return_value = conn

        # Create the table for the test
        database.create_table()
        yield conn
        conn.close()

def test_create_table(memory_db):
    """Test that the images table is created correctly."""
    cursor = memory_db.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='images';")
    assert cursor.fetchone() is not None

def test_insert_and_get_image(memory_db):
    """Test inserting and retrieving an image."""
    image_data = {
        'filepath': '/test/image1.jpg', 'filename': 'image1.jpg',
        'date_taken': '2023-01-01T12:00:00', 'date_modified': '2023-01-01T12:00:00',
        'filesize': 1024, 'width': 800, 'height': 600
    }
    database.insert_image(image_data)

    # Use the real get_image_by_id, which will be patched to use our in-memory db
    retrieved = database.get_image_by_id(1)
    assert retrieved is not None
    assert retrieved['filename'] == 'image1.jpg'

def test_get_all_filepaths(memory_db):
    """Test fetching all filepaths."""
    database.insert_image({'filepath': '/test/img1.jpg', 'filename': 'img1.jpg'})
    database.insert_image({'filepath': '/test/img2.png', 'filename': 'img2.png'})

    paths = database.get_all_filepaths()
    assert len(paths) == 2
    assert '/test/img1.jpg' in paths
    assert '/test/img2.png' in paths

def test_get_images_by_year_and_month(memory_db):
    """Test filtering images by year and month."""
    database.insert_image({'filepath': '2023_1.jpg', 'filename': '2023_1.jpg', 'date_taken': '2023-01-15T10:00:00'})
    database.insert_image({'filepath': '2023_2.jpg', 'filename': '2023_2.jpg', 'date_taken': '2023-02-20T10:00:00'})
    database.insert_image({'filepath': '2022_1.jpg', 'filename': '2022_1.jpg', 'date_taken': '2022-01-05T10:00:00'})

    # Test by year
    images_2023 = database.get_images_by_year_and_month('2023')
    assert len(images_2023) == 2

    # Test by year and month
    images_jan_2023 = database.get_images_by_year_and_month('2023', 1)
    assert len(images_jan_2023) == 1
    assert images_jan_2023[0]['filename'] == '2023_1.jpg'

def test_remove_images_by_path(memory_db):
    """Test removing images based on a folder path."""
    database.insert_image({'filepath': '/folder1/img1.jpg', 'filename': 'img1.jpg'})
    database.insert_image({'filepath': '/folder1/sub/img2.jpg', 'filename': 'img2.jpg'})
    database.insert_image({'filepath': '/folder2/img3.jpg', 'filename': 'img3.jpg'})

    database.remove_images_by_path('/folder1/')

    remaining_images = database.get_all_images()
    assert len(remaining_images) == 1
    assert remaining_images[0]['filename'] == 'img3.jpg'
