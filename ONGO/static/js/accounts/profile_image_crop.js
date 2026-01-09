// Profile Photo Upload Modal with Cropper.js
document.addEventListener('DOMContentLoaded', function () {
    // Elements
    const openModalBtn = document.getElementById('openProfilePhotoModal');
    const modal = document.getElementById('profilePhotoModal');
    const closeModalBtn = document.getElementById('closePhotoModal');
    const cancelBtn = document.getElementById('cancelPhotoUpload');
    const fileInput = document.getElementById('profilePhotoInput');
    const fileInputLabel = document.getElementById('fileInputLabel');
    const cropperImage = document.getElementById('cropperImage');
    const saveBtn = document.getElementById('saveProfilePhoto');
    const uploadForm = document.getElementById('profilePhotoForm');
    const imagePreviewContainer = document.querySelector('.image-preview-container');

    // State
    let cropper = null;
    let selectedFile = null;

    // Constants
    const MAX_FILE_SIZE = 5 * 1024 * 1024; // 5MB
    const ALLOWED_TYPES = ['image/png', 'image/jpeg', 'image/jpg', 'image/webp'];

    // Open Modal
    if (openModalBtn) {
        openModalBtn.addEventListener('click', function (e) {
            e.preventDefault();
            openModal();
        });
    }

    // Close Modal Functions
    function closeModal() {
        modal.classList.add('hidden');
        document.body.classList.remove('modal-open');
        resetModal();
    }

    function resetModal() {
        if (cropper) {
            cropper.destroy();
            cropper = null;
        }
        fileInput.value = '';
        cropperImage.src = '';
        selectedFile = null;
        imagePreviewContainer.classList.remove('has-image');
        saveBtn.disabled = true;
    }

    function openModal() {
        modal.classList.remove('hidden');
        document.body.classList.add('modal-open');
    }

    // Close Modal Events
    if (closeModalBtn) {
        closeModalBtn.addEventListener('click', closeModal);
    }

    if (cancelBtn) {
        cancelBtn.addEventListener('click', closeModal);
    }

    // Close on overlay click
    modal.addEventListener('click', function (e) {
        if (e.target === modal) {
            closeModal();
        }
    });

    // File Input Change
    fileInput.addEventListener('change', function (e) {
        const file = e.target.files[0];
        if (file) {
            handleFileSelect(file);
        }
    });

    // Handle File Selection
    function handleFileSelect(file) {
        // Validate file type
        if (!ALLOWED_TYPES.includes(file.type)) {
            Swal.fire({
                icon: 'error',
                title: 'Invalid File Type',
                text: 'Please select a PNG, JPG, or WEBP image file.',
                confirmButtonColor: '#ef4444'
            });
            fileInput.value = '';
            return;
        }

        // Validate file size
        if (file.size > MAX_FILE_SIZE) {
            Swal.fire({
                icon: 'error',
                title: 'File Too Large',
                text: 'Image size must be less than 5MB.',
                confirmButtonColor: '#ef4444'
            });
            fileInput.value = '';
            return;
        }

        selectedFile = file;

        // Read and display image
        const reader = new FileReader();
        reader.onload = function (e) {
            cropperImage.src = e.target.result;
            imagePreviewContainer.classList.add('has-image');
            initializeCropper();
            saveBtn.disabled = false;
        };
        reader.readAsDataURL(file);
    }

    // Initialize Cropper.js
    function initializeCropper() {
        if (cropper) {
            cropper.destroy();
        }

        cropper = new Cropper(cropperImage, {
            aspectRatio: 1, // Square/Circle crop
            viewMode: 1, // Restrict crop box to canvas
            dragMode: 'move', // Move image, not crop box
            cropBoxResizable: false, // Fixed crop box size
            cropBoxMovable: false, // Fixed crop box position
            guides: false,
            center: false,
            highlight: false,
            background: false,
            autoCropArea: 0.8,
            responsive: true,
            restore: false,
            checkCrossOrigin: false,
            checkOrientation: false,
            modal: true,
            scalable: true,
            zoomable: true,
            zoomOnWheel: true,
            wheelZoomRatio: 0.1,
            minCropBoxWidth: 200,
            minCropBoxHeight: 200,
        });
    }

    // Save Profile Photo
    saveBtn.addEventListener('click', function () {
        if (!cropper || !selectedFile) {
            Swal.fire({
                icon: 'warning',
                title: 'No Image Selected',
                text: 'Please select an image first.',
                confirmButtonColor: '#ef4444'
            });
            return;
        }

        // Disable button and show loading
        saveBtn.disabled = true;
        const originalText = saveBtn.innerHTML;
        saveBtn.innerHTML = '<div class="loading-spinner inline-block mr-2"></div> Uploading...';

        // Get cropped canvas
        cropper.getCroppedCanvas({
            width: 500,
            height: 500,
            fillColor: '#fff',
            imageSmoothingEnabled: true,
            imageSmoothingQuality: 'high',
        }).toBlob(function (blob) {
            if (!blob) {
                Swal.fire({
                    icon: 'error',
                    title: 'Crop Failed',
                    text: 'Failed to process image. Please try again.',
                    confirmButtonColor: '#ef4444'
                });
                saveBtn.disabled = false;
                saveBtn.innerHTML = originalText;
                return;
            }

            // Create FormData
            const formData = new FormData();
            const croppedFile = new File([blob], `profile_photo_${Date.now()}.jpg`, {
                type: 'image/jpeg'
            });

            formData.append('profile_photo', croppedFile);

            // Get CSRF token
            const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
            formData.append('csrfmiddlewaretoken', csrfToken);

            // Submit form
            fetch(uploadForm.action, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': csrfToken
                }
            })
                .then(response => {
                    if (response.ok) {
                        // Reload page to show updated photo
                        window.location.reload();
                    } else {
                        throw new Error('Upload failed');
                    }
                })
                .catch(error => {
                    console.error('Upload error:', error);
                    Swal.fire({
                        icon: 'error',
                        title: 'Upload Failed',
                        text: 'Failed to upload image. Please try again.',
                        confirmButtonColor: '#ef4444'
                    });
                    saveBtn.disabled = false;
                    saveBtn.innerHTML = originalText;
                });

        }, 'image/jpeg', 0.9);
    });
});
