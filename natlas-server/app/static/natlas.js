import './util/error-tracking';
import $ from 'jquery';
import { isNewerVersionAvailable } from './util/version-check';
import { initializeStatusUpdates } from './util/system-status';
import 'natlas.scss';
import './vendor/dataTables.js';
import './vendor/dataTables.tailwindcss.js';
import Alpine from 'alpinejs'

window.Alpine = Alpine


Alpine.start()

$(function() {
    $('.expand-img').on('click', function() {
        var selectAttr = 'src';
        var $img = $(this).find('img');
        if ($img.length && $img[0].hasAttribute('data-path')) {
            selectAttr = 'data-path';
        }
        $('.imagetitle').text($img.attr('alt'));
        $('.imagepreview').attr('src', $img.attr(selectAttr));
        $('#imagemodal').removeClass('hidden');
    });

    // Close modal when clicking the close button
    $('#imagemodal button[data-dismiss="modal"]').on('click', function(e) {
        e.preventDefault();
        $('#imagemodal').addClass('hidden');
    });

    // Close modal when clicking outside the modal content
    $('#imagemodal').on('click', function(e) {
        // If the click target is not within the modal content, close the modal.
        if ($(e.target).closest('.modal-content').length === 0) {
            $('#imagemodal').addClass('hidden');
        }
    });
});


$(function() {
    $('.image-browser').on('click', function() {
        $('.imagetitle').html(`<a href=/host/${$(this).find('img').attr('data-ip')}/${$(this).find('img').attr('data-scan_id')}>${$(this).find('img').attr('alt')}</a>`);
        $('.imagepreview').attr('src', $(this).find('img').attr('data-path'));
        $('#imagemodal').modal('show');
    });
});

$(document).ready(function() {
    $('#checkForUpdate').click(function() {
        var btn = $(this);
        isNewerVersionAvailable()
            .then(result => {
                let params;
                if (result.isNewerAvailable) {
                    params = {
                        content: `Update found: <a href="${result.downloadUrl}">${result.version}</a>`,
                        html: true
                    };
                } else {
                    params = {
                        content: 'No Updates Found!',
                        trigger: 'focus'
                    };
                }
                btn.popover(params).popover('show');
            })
            .catch(console.log);
    });
});

$(document).ready(function() {
    $('.dataTable').DataTable({
        'columnDefs': [
            { 'orderable': false, 'targets': 'table-controls' }
        ]
    });
});

$(document).ready(function() {
    const times = document.body.getElementsByTagName('time');
    for (let i = 0; i < times.length; i++) {
        const localDate = new Date(times[i].dateTime);
        times[i].textContent = localDate.toLocaleString();
    }
});

$(document).ready(function() {
    if (window.location.pathname === '/host/random/') {
        var permalink = document.getElementsByClassName('date-submitted')[0].childNodes[3].href;
        history.replaceState(null, '', permalink);
    }
});

initializeStatusUpdates();
