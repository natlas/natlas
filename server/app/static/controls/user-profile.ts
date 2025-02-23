import * as $ from 'jquery';

function showToken(event: JQueryEventObject): void {
    const tokentarget = event.target.id.split('-')[1];
    $(event.target).hide();
    $(`#showtokenwrapper-${tokentarget}`).hide();
    $('#tokenval-' + tokentarget).show();
}

export function registerAgentEvents(): void {
    $('.showtoken').on('click', showToken);
}
