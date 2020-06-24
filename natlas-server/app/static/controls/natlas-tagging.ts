import * as $ from 'jquery';

function setModalDetails(modal: any, title: string, action: string, submitLabel: string): void {
    modal.find('.modal-title').text(title);
    modal.find('#tagScopeForm').attr('action', action);
    modal.find('#tagScopeSubmit').text(submitLabel);
}

function onModalShow(event: JQueryEventObject): void {
    const button = $(event.relatedTarget); // Button that triggered the modal
    const scopeid = button.data('scopeid'); // Extract info from data-* attributes
    const scopetarget = button.data('scopetarget'); // Extract info from data-* attributes
    const tagaction = button.data('action');
    const tagstr = $(`#scopeTags-${scopeid}`).text().trim(); // Trim whitespace in jinja formatting leaves whitespace
    const tags = tagstr.split(', ');
    const modal = $(this);
    $("select[name='tagname']").val('');
    if (tagaction === 'add') {
        setModalDetails(modal, `Add tag to ${scopetarget}`, `/admin/scope/${scopeid}/tag`, 'Add Tag');
        if (tagstr !== '') {
            for (const item of tags) {
                $('option[value="' + item.trim() + '"]').attr({ hidden: '', disabled: ''});
            }
        }
    } else {
        setModalDetails(modal, `Remove tag from ${scopetarget}`, `/admin/scope/${scopeid}/untag`, 'Remove Tag');

        // Set all options to hidden & disabled by default
        $("select[name='tagname'] > option").each(function() {
            $(this).attr({ hidden: '', disabled: ''});
        });

        // Enable options that are relevant
        for (const item of tags) {
            $('option[value="' + item.trim() + '"]').removeAttr('hidden disabled');
        }
    }
}

function onModalHide(): void {
    // Set all options to enabled and visible by default
    $("select[name='tagname'] > option").each(function() {
        $(this).removeAttr('hidden disabled');
    });
}

export function registerTagModalEvents(): void {
    $('#tagmodal').on('show.bs.modal', onModalShow);

    $('#tagmodal').on('hide.bs.modal', onModalHide);
}
