from typing import TYPE_CHECKING

from app import db, scope_manager

if TYPE_CHECKING:
    from app.models.rescan_task import RescanTask

"""
TODO: Yeah this whole thing is probably broken. I'm amazed it ever worked.
I think previously it would automatically rebind objects to the current session.
"""


def mark_scan_dispatched(rescan: "RescanTask") -> None:
    rescan.dispatchTask()
    db.session.add(rescan)
    db.session.commit()
    scope_manager.update_pending_rescans()
    scope_manager.update_dispatched_rescans()


def mark_scan_completed(ip, scan_id) -> bool:  # type: ignore[no-untyped-def]
    dispatched = scope_manager.get_dispatched_rescans()
    for scan in dispatched:
        if scan.target == ip:
            scan.completeTask(scan_id)
            db.session.add(scan)
            db.session.commit()
            scope_manager.update_dispatched_rescans()
            return True
    return False
