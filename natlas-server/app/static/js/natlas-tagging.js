$('#tagmodal').on('show.bs.modal', function (event) {
  var button = $(event.relatedTarget) // Button that triggered the modal
  var scopeid = button.data('scopeid') // Extract info from data-* attributes
  var scopetarget = button.data('scopetarget') // Extract info from data-* attributes
  var tagaction = button.data('action')
  var tagstr = $('#scopeTags-'+scopeid).text().trim() // Trim whitespace in jinja formatting leaves whitespace
  var tags = tagstr.split(', ')
  var modal = $(this)
  if (tagaction == 'add') {
    modal.find('.modal-title').text('Add tag to ' + scopetarget)
    modal.find('#tagScopeForm').attr('action', "/admin/scope/"+scopeid+"/tag")
    modal.find('#tagScopeSubmit').text('Add Tag')
    if (tagstr != ''){
      tags.forEach(function(item) {
        $("option[value=" + item.trim() + "]").attr('hidden', '') // hide this option because it's already added
        $("option[value=" + item.trim() + "]").attr('disabled', '') // disable this option because it's hidden
      });
    }


  } else {
    modal.find('.modal-title').text('Remove tag from ' + scopetarget)
    modal.find('#tagScopeForm').attr('action', "/admin/scope/"+scopeid+"/untag")
    modal.find('#tagScopeSubmit').text('Remove Tag')
    $("select[name='tagname']")[0].options.length = 0;

    tags.forEach(function(item) {
      $("#tagname").append(
        $('<option>', {
          value: item.trim(),
          text: item.trim()
        })
      );
    });
  }
})