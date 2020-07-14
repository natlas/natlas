import './util/error-tracking';
import $ from 'jquery';
import dataTable from 'datatables.net-bs4'; // TODO: Switch to a NPM native

import { isNewerVersionAvailable } from './util/version-check';
import { initializeStatusUpdates } from './util/system-status';
import { registerTagModalEvents } from './controls/natlas-tagging';
import { registerAgentEvents } from './controls/user-profile';
import { registerParticleEvents, authFormSwitcher } from './pages/login';
import { getReducedMotion } from './util/media-queries';
import 'natlas.scss';
import 'bootstrap';

// Install Datatables.net library onto existing jQuery
dataTable(window, $);

$(function() {
    $('.expand-img').on('click', function() {
        var selectAttr = 'src';
        if ($(this).find('img')[0].hasAttribute('data-path')) {
            selectAttr = 'data-path';
        }
        $('.imagetitle').text($(this).find('img').attr('alt'));
        $('.imagepreview').attr('src', $(this).find('img').attr(selectAttr));
        $('#imagemodal').modal('show');
    });
});

$(function() {
    $('.image-browser').on('click', function() {
        $('.imagetitle').html(`<a href=/host/${$(this).find('img').attr('data-ip')}/${$(this).find('img').attr('data-scan_id')}>${$(this).find('img').attr('alt')}</a>`);
        $('.imagepreview').attr('src', $(this).find('img').attr('data-path'));
        $('#imagemodal').modal('show');
    });
});

var modalContentLoaded = false;
window.loadModalContent = function() {
    if (modalContentLoaded) {
        return;
    }
    const xhr = new XMLHttpRequest();
    xhr.open('GET', '/searchmodal');
    xhr.send();
    xhr.onload = function() {
        $('#searchHelpContent').html(xhr.response);
        modalContentLoaded = true;
    };
};

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
    $('[data-toggle="popover"]').popover();
});

$(document).ready(function() {
    var btn = $('#backtotop');
    btn.tooltip();
    $(window).scroll(function() {
        if ($(window).scrollTop() > 300) {
            btn.addClass('show');
        } else {
            btn.removeClass('show');
        }
    });

    btn.on('click', function(e) {
        e.preventDefault();
        if (getReducedMotion().matches) {
            window.scroll(0, 0);
        } else {
            $('html, body').animate({scrollTop:0}, '300');
        }
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

registerTagModalEvents();
registerAgentEvents();
initializeStatusUpdates();
registerParticleEvents();
authFormSwitcher();
