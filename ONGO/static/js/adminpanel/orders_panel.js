
document.addEventListener('DOMContentLoaded', function () {
    if (typeof lucide !== 'undefined') {
        lucide.createIcons();
    }
    setupStatusDropdowns();
});

function setupStatusDropdowns() {
    var statusSelects = document.querySelectorAll('.js-status-select');
    statusSelects.forEach(function (select) {
        select.dataset.originalStatus = select.value;
        select.addEventListener('change', function (e) {
            handleStatusChange(e.target);
        });
    });
}

async function handleStatusChange(selectEl) {
    var newStatus = selectEl.value;
    var originalStatus = selectEl.dataset.originalStatus;
    var orderId = selectEl.dataset.orderId;
    var itemId = selectEl.dataset.itemId;
    var type = selectEl.dataset.type;

    if (newStatus === 'cancelled' || newStatus === 'returned') {
        var confirmed = await showConfirm(newStatus);
        if (!confirmed) {
            selectEl.value = originalStatus;
            return;
        }
    }

    selectEl.disabled = true;

    var success = false;
    if (type === 'order') {
        success = await updateOrderStatus(orderId, newStatus);
    } else if (type === 'item') {
        success = await updateItemStatus(orderId, itemId, newStatus);
    }

    if (success) {
        await showSuccess('Status updated successfully');
        window.location.reload();
    } else {
        selectEl.value = originalStatus;
        selectEl.disabled = false;
    }
}

async function updateOrderStatus(orderId, status) {
    var url = '/admin/orders/status/' + orderId + '/';
    return await sendRequest(url, status);
}

async function updateItemStatus(orderId, itemId, status) {
    var url = '/admin/orders/' + orderId + '/' + itemId;
    return await sendRequest(url, status);
}

async function sendRequest(url, status) {
    var csrfToken = getCookie('csrftoken');
    try {
        var formData = new FormData();
        formData.append('status', status);

        var response = await fetch(url, {
            method: 'POST',
            headers: { 'X-CSRFToken': csrfToken },
            body: formData
        });

        var data = await response.json();
        if (response.ok && data.success) {
            return true;
        } else {
            showError(data.error || 'Update failed');
            return false;
        }
    } catch (e) {
        console.error(e);
        showError('Network error');
        return false;
    }
}

async function showConfirm(status) {
    if (typeof Swal !== 'undefined') {
        var result = await Swal.fire({
            title: 'Are you sure?',
            text: 'Mark as ' + status + '? Irreversible.',
            icon: 'warning',
            showCancelButton: true,
            confirmButtonColor: '#d33',
            confirmButtonText: 'Yes'
        });
        return result.isConfirmed;
    }
    return confirm('Mark as ' + status + '?');
}

async function showSuccess(msg) {
    if (typeof Swal !== 'undefined') {
        await Swal.fire({
            icon: 'success',
            title: 'Updated',
            text: msg,
            toast: true,
            position: 'top-end',
            timer: 1000,
            showConfirmButton: false
        });
    } else {
        alert(msg);
    }
}

function showError(msg) {
    if (typeof Swal !== 'undefined') {
        Swal.fire({ icon: 'error', title: 'Error', text: msg });
    } else {
        alert(msg);
    }
}

function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
