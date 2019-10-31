$('#tagmodal').on('show.bs.modal', function (event) {
  var button = $(event.relatedTarget) // Button that triggered the modal
  var scopeid = button.data('scopeid') // Extract info from data-* attributes
  var scopetarget = button.data('scopetarget') // Extract info from data-* attributes
  var tagaction = button.data('action')
  var tagstr = $('#scopeTags-'+scopeid).text().trim() // Trim whitespace in jinja formatting leaves whitespace
  var tags = tagstr.split(', ')
  var modal = $(this)
  $("select[name='tagname']").val("")
  if (tagaction == 'add') {
    modal.find('.modal-title').text('Add tag to ' + scopetarget)
    modal.find('#tagScopeForm').attr('action', "/admin/scope/"+scopeid+"/tag")
    modal.find('#tagScopeSubmit').text('Add Tag')
    if (tagstr != ''){
      tags.forEach((item, index) => {
        $("option[value=\"" + item.trim() + "\"]").attr({'hidden': '', 'disabled': ''}) // hide this option because it's already added
      });
    }
  } else {
    modal.find('.modal-title').text('Remove tag from ' + scopetarget)
    modal.find('#tagScopeForm').attr('action', "/admin/scope/"+scopeid+"/untag")
    modal.find('#tagScopeSubmit').text('Remove Tag')

    // Set all options to hidden & disabled by default
    $("select[name='tagname'] > option").each(function() {
      $(this).attr({'hidden': '', 'disabled': ''})
    });

    // Enable options that are relevant
    tags.forEach((item, index) => {
      $("option[value=\"" + item.trim() + "\"]").removeAttr('hidden disabled')
    });
  }
})

$('#tagmodal').on('hide.bs.modal', function (event) {
  var modal = $(this)

  // Set all options to enabled and visible by default
  $("select[name='tagname'] > option").each(function() {
    $(this).removeAttr('hidden disabled')
  });
})