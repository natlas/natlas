import * as $ from 'jquery';

function setModalDetails(modal: any, title: String, action: String, agentName: String, submitLabel: String): void {
	modal.find('.modal-title').text(title);
	modal.find('#agentNameForm').attr('action', action);
	modal.find('#change_name').text(submitLabel)
	if (agentName != "") {
		modal.find("#agent_name").attr('placeholder', agentName)
	}
}

function onModalShow(event: JQueryEventObject): void {
	var button = $(event.relatedTarget) // Button that triggered the modal
	var agentid = button.data('agentid') // Extract info from data-* attributes
	var agentname = button.data('agentname') // Extract info from data-* attributes
	var formaction = button.data('action')
	var modal = $(this)
	if (formaction == 'changename') {
		setModalDetails(modal, 'Change Name of ' + agentid, "/user/agent/"+agentid+"/newName", agentname, 'Change Name')
	} else if (formaction == 'newagent') {
		setModalDetails(modal, 'New Agent', '/user/agent/newAgent', "", 'New Agent')
	}
}

export function registerAgentModalEvents(): void {
	$('#agentmodal').on('show.bs.modal', onModalShow);
}