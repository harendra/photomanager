import pytest
import app as main_app
import json
from unittest.mock import patch

@pytest.fixture
def client():
    """Create a test client for the Flask app."""
    main_app.app.config['TESTING'] = True
    with main_app.app.test_client() as client:
        # We need to mock the load_config to simulate that config exists
        with patch('app.load_config') as mock_load_config:
            mock_load_config.return_value = True
            # Also mock the IMAGE_DIRS since load_config is patched
            main_app.IMAGE_DIRS = ['/fake/dir']
            yield client

def test_index_route(client):
    """Test the main gallery page."""
    # Mock the database calls made by the index route
    with patch('database.get_available_years') as mock_get_years, \
         patch('database.get_images_by_year_and_month') as mock_get_images:

        mock_get_years.return_value = ['2023']
        mock_get_images.return_value = [
            {'id': 1, 'filepath': '/fake/dir/img1.jpg', 'filename': 'img1.jpg', 'date_taken': '2023-01-01T12:00:00'}
        ]

        response = client.get('/')
        assert response.status_code == 200
        assert b"Photo Gallery" in response.data

def test_settings_page_get(client):
    """Test GET request to the settings page."""
    response = client.get('/settings')
    assert response.status_code == 200
    assert b"Manage Photo Directories" in response.data

def test_search_page_get(client):
    """Test GET request to the search page."""
    response = client.get('/search')
    assert response.status_code == 200
    assert b"Search Photos" in response.data

def test_image_api_endpoint(client):
    """Test the JSON API for a single image."""
    with patch('database.get_image_by_id') as mock_get_image:
        mock_get_image.return_value = {
            'id': 1, 'filepath': '/fake/dir/img1.jpg', 'filename': 'img1.jpg',
            'date_taken': '2023-01-01T12:00:00', 'width': 800, 'height': 600
        }

        response = client.get('/api/image/1?context=1,2,3')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['filename'] == 'img1.jpg'
        assert 'full_image_url' in data

def test_scan_status_api(client):
    """Test the scan status API."""
    # Set a mock status
    main_app.scan_status['is_scanning'] = True
    main_app.scan_status['message'] = 'Testing scan'

    response = client.get('/api/scan-status')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['is_scanning'] is True
    assert data['message'] == 'Testing scan'

    # Reset for other tests
    main_app.scan_status['is_scanning'] = False
