document.addEventListener('DOMContentLoaded', () => {
    // Config
    const ASPECT_RATIOS = {
        desktop: 1920 / 700,
        mobile: 768 / 900
    };

    // DOM Elements
    const desktopInput = document.getElementById('desktopImageInput');
    const desktopPreview = document.getElementById('desktopPreview');
    
    const mobileInput = document.getElementById('mobileImageInput');
    const mobilePreview = document.getElementById('mobilePreview');
    
    // Modal Elements (from base_admin_list.html)
    const cropperModal = document.getElementById('cropperModal');
    const closeCropperModal = document.getElementById('closeCropperModal');
    
    // We attach our cropper to the existing modal image
    const baseCropperImage = document.getElementById('cropperImage');
    const applyCropBtn = document.getElementById('applyCrop');
    const cancelCropBtn = document.getElementById('cancelCrop');
    
    // Retrieve the text info element so we can update it
    const textInfoContainer = cropperModal.querySelector('.text-center.mb-6');
    let textInfo = null;
    if (textInfoContainer) {
        textInfo = textInfoContainer.querySelector('div');
    }

    let cropper = null;
    let currentInputTarget = null;
    let currentPreviewTarget = null;
    let currentFilename = '';
    
    function openModal() {
        cropperModal.classList.remove('hidden');
        // Minor delay for transition
        setTimeout(() => {
            cropperModal.classList.remove('opacity-0', 'pointer-events-none');
        }, 10);
    }

    function closeModal() {
        cropperModal.classList.add('opacity-0', 'pointer-events-none');
        setTimeout(() => {
            cropperModal.classList.add('hidden');
            if (cropper) {
                cropper.destroy();
                cropper = null;
            }
            if (baseCropperImage) {
                baseCropperImage.src = '';
                baseCropperImage.classList.add('hidden');
            }
            // Reset input value to allow selecting same file again if crop cancelled
            if (currentInputTarget && (!currentInputTarget.files || currentInputTarget.files.length === 0)) {
                currentInputTarget.value = '';
            }
        }, 300);
    }
    
    if (closeCropperModal) closeCropperModal.addEventListener('click', closeModal);
    if (cancelCropBtn) cancelCropBtn.addEventListener('click', closeModal);

    function initCropper(file, targetType) {
        if (!file) return;
        currentFilename = file.name;
        
        const url = URL.createObjectURL(file);
        
        // Setup Modal UI labels based on target
        if(targetType === 'desktop') {
            if (textInfo) {
                textInfo.innerHTML = `
                <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                Desktop landscape crop (1920:700)`;
            }
            currentInputTarget = desktopInput;
            currentPreviewTarget = desktopPreview;
        } else {
            if (textInfo) {
                textInfo.innerHTML = `
                <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                Mobile portrait crop (768:900)`;
            }
            currentInputTarget = mobileInput;
            currentPreviewTarget = mobilePreview;
        }

        baseCropperImage.src = url;
        baseCropperImage.classList.remove('hidden');
        baseCropperImage.style.display = 'block';
        baseCropperImage.style.maxWidth = '100%';
        
        // Show loader initially
        const cropperLoader = document.getElementById('cropperLoader');
        if (cropperLoader) {
            cropperLoader.style.display = 'flex';
        }

        openModal();

        // Initialize Cropper cleanly
        if (cropper) {
            cropper.destroy();
        }
        
        cropper = new Cropper(baseCropperImage, {
            aspectRatio: targetType === 'desktop' ? ASPECT_RATIOS.desktop : ASPECT_RATIOS.mobile,
            viewMode: 1,
            autoCropArea: 1,
            background: true,
            zoomable: true,
            scalable: false,
            ready: function () {
                // Hide loader when cropper is fully initialized
                const cropperLoader = document.getElementById('cropperLoader');
                if (cropperLoader) {
                    cropperLoader.style.display = 'none';
                }
            }
        });
    }

    if (desktopInput) {
        desktopInput.addEventListener('change', (e) => {
            if (e.target.files && e.target.files[0]) {
                initCropper(e.target.files[0], 'desktop');
            }
        });
    }

    if (mobileInput) {
        mobileInput.addEventListener('change', (e) => {
            if (e.target.files && e.target.files[0]) {
                initCropper(e.target.files[0], 'mobile');
            }
        });
    }

    if (applyCropBtn) {
        applyCropBtn.addEventListener('click', () => {
            if (!cropper) return;

            // Use exact sizes based on target constraints
            const cropWidth = currentInputTarget === desktopInput ? 1920 : 768;
            const cropHeight = currentInputTarget === desktopInput ? 700 : 900;

            const canvas = cropper.getCroppedCanvas({
                width: cropWidth,
                height: cropHeight,
                imageSmoothingEnabled: true,
                imageSmoothingQuality: 'high',
            });
            
            if (!canvas) {
                Swal.fire('Error', 'Image cropping failed. Please try a different image.', 'error');
                return;
            }

            canvas.toBlob((blob) => {
                // Update frontend preview
                const objectUrl = URL.createObjectURL(blob);
                currentPreviewTarget.src = objectUrl;
                currentPreviewTarget.classList.remove('hidden');
                
                // Hide the placeholder text inside the container view
                const placeholder = currentPreviewTarget.parentElement.querySelector('div');
                if (placeholder) placeholder.classList.add('hidden');

                // Replace input file object completely 
                // Using DataTransfer to create a new File list
                const dataTransfer = new DataTransfer();
                const newFile = new File([blob], `cropped_${currentFilename}`, { type: 'image/jpeg' });
                dataTransfer.items.add(newFile);
                currentInputTarget.files = dataTransfer.files;

                closeModal();
                
                if (typeof Swal !== 'undefined') {
                    Swal.fire({
                        toast: true,
                        position: 'top-end',
                        icon: 'success',
                        title: 'Image cropped and attached!',
                        showConfirmButton: false,
                        timer: 2500
                    });
                }
            }, 'image/jpeg', 0.9);
        });
    }

    // Handle Cropper Controls existing in base form
    const rotateLeftBtn = document.getElementById('rotateLeft');
    const rotateRightBtn = document.getElementById('rotateRight');
    const zoomInBtn = document.getElementById('zoomIn');
    const zoomOutBtn = document.getElementById('zoomOut');

    if(rotateLeftBtn) rotateLeftBtn.addEventListener('click', () => cropper?.rotate(-45));
    if(rotateRightBtn) rotateRightBtn.addEventListener('click', () => cropper?.rotate(45));
    if(zoomInBtn) zoomInBtn.addEventListener('click', () => cropper?.zoom(0.1));
    if(zoomOutBtn) zoomOutBtn.addEventListener('click', () => cropper?.zoom(-0.1));
});
