document.addEventListener('DOMContentLoaded', () => {
    const gallery = document.querySelector('.gallery');
    if (!gallery) return;

    // Get the context of all visible image IDs
    const imageLinks = gallery.querySelectorAll('.photo-thumbnail-link');
    const contextIds = Array.from(imageLinks).map(link => link.dataset.imageId);

    imageLinks.forEach(link => {
        link.addEventListener('click', (event) => {
            event.preventDefault();
            const imageId = link.dataset.imageId;
            openViewer(imageId, contextIds);
        });
    });
});

function openViewer(imageId, contextIds) {
    // Create viewer modal
    const viewerHtml = `
        <div class="photo-viewer" id="photo-viewer">
            <span class="viewer-close">&times;</span>
            <span class="viewer-prev">&lsaquo;</span>
            <span class="viewer-next">&rsaquo;</span>
            <div class="viewer-content">
                <img src="" alt="Loading..." id="viewer-img">
                <div class="viewer-info">
                    <p id="viewer-filename"></p>
                    <p id="viewer-date"></p>
                </div>
            </div>
        </div>
    `;
    document.body.insertAdjacentHTML('beforeend', viewerHtml);

    const viewer = document.getElementById('photo-viewer');
    const closeBtn = viewer.querySelector('.viewer-close');
    const prevBtn = viewer.querySelector('.viewer-prev');
    const nextBtn = viewer.querySelector('.viewer-next');

    closeBtn.addEventListener('click', () => viewer.remove());
    prevBtn.addEventListener('click', () => {
        const currentId = document.getElementById('viewer-img').dataset.currentId;
        const currentIndex = contextIds.indexOf(currentId);
        if (currentIndex > 0) {
            const prevId = contextIds[currentIndex - 1];
            load_image_data(prevId, contextIds);
        }
    });
    nextBtn.addEventListener('click', () => {
        const currentId = document.getElementById('viewer-img').dataset.currentId;
        const currentIndex = contextIds.indexOf(currentId);
        if (currentIndex < contextIds.length - 1) {
            const nextId = contextIds[currentIndex + 1];
            load_image_data(nextId, contextIds);
        }
    });

    load_image_data(imageId, contextIds);
}

function load_image_data(imageId, contextIds) {
    const viewerImg = document.getElementById('viewer-img');
    const filenameEl = document.getElementById('viewer-filename');
    const dateEl = document.getElementById('viewer-date');
    const prevBtn = document.querySelector('.viewer-prev');
    const nextBtn = document.querySelector('.viewer-next');

    // Show loading state
    viewerImg.src = ''; // Or a loading spinner URL
    filenameEl.textContent = 'Loading...';
    dateEl.textContent = '';

    const contextParam = contextIds.join(',');
    fetch(`/api/image/${imageId}?context=${contextParam}`)
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                filenameEl.textContent = data.error;
                return;
            }

            viewerImg.src = data.full_image_url;
            viewerImg.dataset.currentId = data.id;
            filenameEl.textContent = data.filename;
            dateEl.textContent = `Taken: ${data.date_taken.split('T')[0]}`;

            // Update nav buttons
            prevBtn.style.display = data.prev_id ? 'block' : 'none';
            nextBtn.style.display = data.next_id ? 'block' : 'none';

            // Preload next and previous images
            if (data.next_id) {
                const nextImg = new Image();
                nextImg.src = `/api/image/${data.next_id}`;
            }
            if (data.prev_id) {
                const prevImg = new Image();
                prevImg.src = `/api/image/${data.prev_id}`;
            }
        })
        .catch(error => {
            console.error('Error fetching image data:', error);
            filenameEl.textContent = 'Error loading image.';
        });
}
