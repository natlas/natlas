$(function() {
		$('.expand-img').on('click', function() {
			var selectAttr = 'src';
			if ($(this).find('img')[0].hasAttribute('data-path')) {
				selectAttr = 'data-path'
			}
			$('.imagetitle').text($(this).find('img').attr('alt'));
			$('.imagepreview').attr('src', $(this).find('img').attr(selectAttr));
			$('#imagemodal').modal('show');
		});
});

$(function() {
		$('.image-browser').on('click', function() {
			$('.imagetitle').html("<a href=/host/"+$(this).find('img').attr('data-ip')+"/" + $(this).find('img').attr('data-scan_id') + ">"+$(this).find('img').attr('alt')+"</a>");
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
	var updateURL = "https://api.github.com/repos/natlas/natlas/releases/latest";
	var latestURL = "https://github.com/natlas/natlas/releases/latest"
	$('#checkForUpdate').click(function() {
		var btn = $(this);
		$.ajax({
			url: updateURL,
			type:"GET",
			success: function(result){
				if (result.tag_name != $('#natlasVersion').text()) {
					btn.popover({content: "Update found: <a href=\"" + latestURL + "\">" +result.tag_name+"</a>", html:true}).popover('show');
				}
				else {
					btn.popover({content: "No Updates Found!", trigger:"focus"}).popover('show');
				}
			},
			error: function(error){
				console.log(error)
			}
		});
	});
})

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