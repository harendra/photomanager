from flask import Flask, render_template, send_from_directory, request, redirect, url_for, flash, jsonify
import database
import os
import json
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

CONFIG_FILE = 'config.json'
IMAGE_DIRS = []

def load_config():
    global IMAGE_DIRS
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            config_data = json.load(f)
            IMAGE_DIRS = config_data.get('image_dirs', [])
        return True
    return False

def save_config():
    with open(CONFIG_FILE, 'w') as f:
        json.dump({'image_dirs': IMAGE_DIRS}, f, indent=4)

@app.route('/setup', methods=['GET', 'POST'])
def setup():
    if request.method == 'POST':
        directory = request.form['directory']
        if os.path.isdir(directory):
            global IMAGE_DIRS
            IMAGE_DIRS = [directory]
            save_config()
            flash('Configuration saved! Starting initial scan in the background...', 'success')

            scan_thread = threading.Thread(target=scanner.scan_directory, args=(IMAGE_DIRS,), daemon=True)
            scan_thread.start()

            return redirect(url_for('index'))
        else:
            flash('The provided path is not a valid directory.', 'danger')
    return render_template('setup.html')

@app.route('/')
def index():
    if not IMAGE_DIRS:
        return redirect(url_for('setup'))

    available_years = database.get_available_years()
    selected_year = request.args.get('year', None)

    if not selected_year and available_years:
        selected_year = available_years[0]

    images = []
    if selected_year:
        image_records = database.get_images_by_year(selected_year)
        for record in image_records:
            image_dict = dict(record)
            date_str = image_dict['date_taken'].split('.')[0]
            dt_object = datetime.strptime(date_str, '%Y-%m-%dT%H:%M:%S')
            image_dict['month_name'] = dt_object.strftime('%B')
            images.append(image_dict)

    return render_template('index.html', images=images, available_years=available_years, selected_year=selected_year)

THUMBNAIL_DIR = 'static/thumbnails'

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'add_folder':
            directory = request.form.get('directory')
            if directory and os.path.isdir(directory) and directory not in IMAGE_DIRS:
                IMAGE_DIRS.append(directory)
                save_config()
                flash(f"Added directory: {directory}. Scanning in the background.", 'success')
                # Scan just the new directory
                scan_thread = threading.Thread(target=scanner.scan_directories, args=([directory],), daemon=True)
                scan_thread.start()

        elif action == 'remove_folder':
            folder_path = request.form.get('folder_path')
            if folder_path in IMAGE_DIRS:
                IMAGE_DIRS.remove(folder_path)
                save_config()
                database.remove_images_by_path(folder_path)
                flash(f"Removed directory and its images: {folder_path}", 'success')

        elif action == 'rescan':
            flash("Started full library rescan in the background.", 'info')
            scan_thread = threading.Thread(target=scanner.scan_directories, args=(IMAGE_DIRS,), daemon=True)
            scan_thread.start()

        return redirect(url_for('settings'))

    return render_template('settings.html', image_dirs=IMAGE_DIRS)

@app.route('/search')
def search():
    search_query = request.args.get('query')
    images = None
    if search_query:
        images = database.search_images_by_tag(search_query)

    return render_template('search.html', images=images)

@app.route('/api/image/<int:image_id>')
def image_api(image_id):
    image_record = database.get_image_by_id(image_id)
    if not image_record:
        return jsonify({'error': 'Image not found'}), 404

    image_data = dict(image_record)

    context_ids_str = request.args.get('context', '')
    if context_ids_str:
        context_ids = [int(id) for id in context_ids_str.split(',')]
        if image_id in context_ids:
            current_index = context_ids.index(image_id)
            prev_id = context_ids[current_index - 1] if current_index > 0 else None
            next_id = context_ids[current_index + 1] if current_index < len(context_ids) - 1 else None
            image_data['prev_id'] = prev_id
            image_data['next_id'] = next_id

    image_data['full_image_url'] = url_for('full_image', image_id=image_id)
    return jsonify(image_data)

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
                img.thumbnail((200, 200))
                img.convert('RGB').save(thumbnail_path, 'JPEG')
        except FileNotFoundError:
            img = Image.new('RGB', (200, 200), color = 'gray')
            img.save(thumbnail_path, 'JPEG')

    return send_from_directory(THUMBNAIL_DIR, f"{image_id}.jpg")

@app.route('/image/full/<int:image_id>')
def full_image(image_id):
    image_record = database.get_image_by_id(image_id)
    if not image_record:
        return "Image not found", 404

    directory, filename = os.path.split(image_record['filepath'])
    return send_from_directory(directory, filename)

def initial_setup():
    # Clean up old config file if it exists
    if os.path.exists('config.txt'):
        os.remove('config.txt')

    database.create_table()
    if load_config():
        print(f"Loaded image directories: {IMAGE_DIRS}")
    else:
        print("No config file found. Please set up via the web interface.")

if __name__ == '__main__':
    initial_setup()

    llm_thread = threading.Thread(target=llm_processor.start_llm_processing_loop, daemon=True)
    llm_thread.start()

    app.run(debug=True, use_reloader=False)
