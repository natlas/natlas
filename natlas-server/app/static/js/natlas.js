$(function() {
		$('.expand-img').on('click', function() {
			$('.imagetitle').text($(this).find('img').attr('alt'));
			$('.imagepreview').attr('src', $(this).find('img').attr('data-path'));
			$('#imagemodal').modal('show');
		});
});

var modal_content_loaded = false;
function loadModalContent() {
  if (modal_content_loaded){
    return
  }
  let xhr = new XMLHttpRequest();
  xhr.open("GET", "/searchmodal")
  xhr.send();
  xhr.onload = function() {
    $('#searchHelpContent').html(xhr.response);
    modal_content_loaded = true;
  }
}

$(document).ready(function() {
    $('.dataTable').DataTable( {
        "columnDefs": [
            { "orderable": false, "targets": 'table-controls' }
        ]
    });
    $('[data-toggle="popover"]').popover()
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
    $('html, body').animate({scrollTop:0}, '300');
  });

});