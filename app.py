from flask import Flask, render_template, send_from_directory, request, redirect, url_for, flash
import database
import os
from PIL import Image
import threading
import llm_processor
import scanner

from datetime import datetime

app = Flask(__name__)
app.secret_key = 'supersecretkey' # Needed for flash messaging

# Custom Jinja2 filter for parsing date strings
def strptime_filter(date_string, format):
    return datetime.strptime(date_string, format)

app.jinja_env.filters['strptime'] = strptime_filter

def strftime_filter(date_obj, format):
    return date_obj.strftime(format)

app.jinja_env.filters['strftime'] = strftime_filter

CONFIG_FILE = 'config.txt'
IMAGE_DIR = ''

def load_config():
    global IMAGE_DIR
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            IMAGE_DIR = f.read().strip()
        return True
    return False

@app.route('/setup', methods=['GET', 'POST'])
def setup():
    if request.method == 'POST':
        directory = request.form['directory']
        if os.path.isdir(directory):
            with open(CONFIG_FILE, 'w') as f:
                f.write(directory)
            global IMAGE_DIR
            IMAGE_DIR = directory
            flash('Configuration saved! Starting initial scan in the background...', 'success')

            # Start the scan in a background thread
            scan_thread = threading.Thread(target=scanner.scan_directory, args=(IMAGE_DIR,), daemon=True)
            scan_thread.start()

            return redirect(url_for('index'))
        else:
            flash('The provided path is not a valid directory.', 'danger')
    return render_template('setup.html')

@app.route('/')
def index():
    if not IMAGE_DIR:
        return redirect(url_for('setup'))

    available_years = database.get_available_years()
    selected_year = request.args.get('year', None)

    if not selected_year and available_years:
        # Default to the most recent year if none is selected
        selected_year = available_years[0]

    images = []
    if selected_year:
        image_records = database.get_images_by_year(selected_year)
        # Convert Row objects to dictionaries and add a month_name attribute for grouping
        for record in image_records:
            image_dict = dict(record)
            # Truncate fractional seconds before parsing
            date_str = image_dict['date_taken'].split('.')[0]
            dt_object = datetime.strptime(date_str, '%Y-%m-%dT%H:%M:%S')
            image_dict['month_name'] = dt_object.strftime('%B')
            images.append(image_dict)

    return render_template('index.html', images=images, available_years=available_years, selected_year=selected_year)

THUMBNAIL_DIR = 'static/thumbnails'
THUMBNAIL_SIZE = (200, 150)

@app.route('/search')
def search():
    search_query = request.args.get('query')
    images = None
    if search_query:
        images = database.search_images_by_tag(search_query)

    return render_template('search.html', images=images)

@app.route('/image/<int:image_id>')
def image_viewer(image_id):
    image = database.get_image_by_id(image_id)
    if not image:
        return "Image not found", 404

    all_images = database.get_all_images(sort_by='date_taken', order='desc')
    all_ids = [img['id'] for img in all_images]

    current_index = all_ids.index(image_id)

    prev_id = all_ids[current_index - 1] if current_index > 0 else None
    next_id = all_ids[current_index + 1] if current_index < len(all_ids) - 1 else None

    return render_template('image_viewer.html', image=image, prev_id=prev_id, next_id=next_id)


@app.route('/thumbnail/<int:image_id>')
def thumbnail(image_id):
    image_record = database.get_image_by_id(image_id)
    if not image_record:
        return "Image not found", 404

    thumbnail_path = os.path.join(THUMBNAIL_DIR, f"{image_id}.jpg")

    if not os.path.exists(thumbnail_path):
        os.makedirs(THUMBNAIL_DIR, exist_ok=True)
        try:
            with Image.open(image_record['filepath']) as img:
                img.thumbnail(THUMBNAIL_SIZE)
                # Convert to RGB before saving as JPEG to handle RGBA images (e.g. PNGs)
                img.convert('RGB').save(thumbnail_path, 'JPEG')
        except FileNotFoundError:
            # If the original image is missing, create a placeholder
            img = Image.new('RGB', THUMBNAIL_SIZE, color = 'gray')
            img.save(thumbnail_path, 'JPEG')

    return send_from_directory(THUMBNAIL_DIR, f"{image_id}.jpg")

def initial_setup():
    database.create_table()
    if load_config():
        print(f"Loaded image directory: {IMAGE_DIR}")
        # Optional: Trigger a rescan on startup
        # print("Starting startup rescan...")
        # scan_thread = threading.Thread(target=scanner.scan_directory, args=(IMAGE_DIR,), daemon=True)
        # scan_thread.start()
    else:
        print("No config file found. Please set up via the web interface.")

if __name__ == '__main__':
    initial_setup()

    # Start the LLM processor in a background thread
    llm_thread = threading.Thread(target=llm_processor.start_llm_processing_loop, daemon=True)
    llm_thread.start()

    app.run(debug=True, use_reloader=False)
