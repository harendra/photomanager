# Desktop Photo App

This is a locally hosted Flask web application for browsing and searching a local photo collection. The app scans a user-defined directory, extracts image metadata, and uses a (mock) Large Language Model (LLM) to generate searchable tags for each image.

## Features

-   **Web-based Interface:** Access the app through your local web browser.
-   **Directory Scanner:** Recursively scans a directory for images (`.jpg`, `.jpeg`, `.png`, `.gif`, `.bmp`).
-   **Metadata Extraction:** Reads image dimensions and date taken (from EXIF).
-   **Local Database:** Uses SQLite to store all image metadata. No external database required.
-   **Thumbnail Generation:** Creates and caches thumbnails for fast gallery loading.
-   **LLM Tagging (Mock):** A background process simulates an LLM analyzing images and generating tags (e.g., "cat", "outdoor").
-   **Search:** A powerful search bar to find photos based on their generated tags.
-   **Image Viewer:** A full-screen viewer with metadata display and next/previous navigation.

## How to Run

### Prerequisites

-   Python 3.6+
-   A directory of photos you want to scan.

### 1. Installation

Clone this repository to your local machine or download the source code.

Navigate to the project directory in your terminal:
```bash
cd path/to/photo-app
```

It is recommended to use a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
```

Install the required Python packages:
```bash
pip install -r requirements.txt
```

### 2. Running the Application

Once the dependencies are installed, run the Flask application:
```bash
python app.py
```

You will see output indicating that the server is running, usually on `http://127.0.0.1:5000`.

### 3. First-Time Setup

-   Open your web browser and navigate to `http://127.0.0.1:5000`.
-   On your first visit, you will be redirected to a setup page.
-   Enter the **full, absolute path** to the directory containing your photos (e.g., `/Users/yourname/Pictures` or `C:\Users\yourname\Pictures`).
-   Click "Save and Scan".

### 4. Using the App

-   After the initial scan is triggered, you will be taken to the main gallery. The scan will run in the background. Images will appear as they are discovered.
-   The LLM tagging process also runs in the background. Tags will be added to images over time.
-   Use the search bar at the top to filter images by tags.
-   Click on any thumbnail to open the full image viewer.

## Project Structure

-   `app.py`: The main Flask application file containing all routes.
-   `database.py`: Handles all SQLite database operations.
-   `scanner.py`: Contains the logic for scanning directories and extracting metadata.
-   `llm_processor.py`: Contains the (mock) logic for processing images and generating tags.
-   `requirements.txt`: A list of Python dependencies.
-   `config.txt`: A file created after setup to store the path to your photo library.
-   `templates/`: Contains all HTML templates for the web interface.
-   `static/`: Contains static files (thumbnails will be cached here).
-   `photo_library.db`: The SQLite database file, created after the first run.
