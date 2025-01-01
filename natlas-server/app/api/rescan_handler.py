from flask import current_app

from app import db


def mark_scan_dispatched(rescan):  # type: ignore[no-untyped-def]
    rescan.dispatchTask()
    db.session.add(rescan)
    db.session.commit()
    current_app.ScopeManager.update_pending_rescans()  # type: ignore[attr-defined]
    current_app.ScopeManager.update_dispatched_rescans()  # type: ignore[attr-defined]


def mark_scan_completed(ip, scan_id):  # type: ignore[no-untyped-def]
    dispatched = current_app.ScopeManager.get_dispatched_rescans()  # type: ignore[attr-defined]
    for scan in dispatched:
        if scan.target == ip:
            scan.completeTask(scan_id)
            db.session.add(scan)
            db.session.commit()
            current_app.ScopeManager.update_dispatched_rescans()  # type: ignore[attr-defined]
            return True
    return False
