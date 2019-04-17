$(function() {
		$('.expand-img').on('click', function() {
			$('.imagetitle').text($(this).find('img').attr('alt'));
			$('.imagepreview').attr('src', $(this).find('img').attr('src'));
			$('#imagemodal').modal('show');   
		});		
});


$(document).ready(function() {
    $('.dataTable').DataTable( {
        "columnDefs": [
            { "orderable": false, "targets": 'table-controls' }
        ]
    });
    $('[data-toggle="popover"]').popover()
});