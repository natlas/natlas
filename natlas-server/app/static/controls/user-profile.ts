import * as $ from 'jquery';

function setModalDetails(modal: any, title: string, action: string, agentName: string, submitLabel: string): void {
    modal.find('.modal-title').text(title);
    modal.find('#agentNameForm').attr('action', action);
    modal.find('#change_name').text(submitLabel);
    if (agentName !== '') {
        modal.find('#agent_name').attr('placeholder', agentName);
    }
}

function onModalShow(event: JQueryEventObject): void {
    const button = $(event.relatedTarget); // Button that triggered the modal
    const agentid = button.data('agentid'); // Extract info from data-* attributes
    const agentname = button.data('agentname'); // Extract info from data-* attributes
    const formaction = button.data('action');
    const modal = $(this);
    if (formaction === 'changename') {
        setModalDetails(modal, `Change Name of ${agentid}`, `/user/agent/${agentid}/newName`, agentname, 'Change Name');
    } else if (formaction === 'newagent') {
        setModalDetails(modal, 'New Agent', '/user/agent/newAgent', '', 'New Agent');
    }
}

function showToken(event: JQueryEventObject): void {
    const tokentarget = event.target.id.split('-')[1];
    $(event.target).hide();
    $(`#showtokenwrapper-${tokentarget}`).hide();
    $('#tokenval-' + tokentarget).show();
}

export function registerAgentEvents(): void {
    $('#agentmodal').on('show.bs.modal', onModalShow);
    $('.showtoken').on('click', showToken);
}
