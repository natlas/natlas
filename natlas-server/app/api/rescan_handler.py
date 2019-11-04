from flask import current_app
from app import db


def mark_scan_dispatched(rescan):
	rescan.dispatchTask()
	db.session.add(rescan)
	db.session.commit()
	current_app.ScopeManager.updatePendingRescans()
	current_app.ScopeManager.updateDispatchedRescans()
	return


def mark_scan_completed(ip, scan_id):
	dispatched = current_app.ScopeManager.getDispatchedRescans()
	for scan in dispatched:
		if scan.target == ip:
			scan.completeTask(scan_id)
			db.session.add(scan)
			db.session.commit()
			current_app.ScopeManager.updateDispatchedRescans()
			return True
	return False
