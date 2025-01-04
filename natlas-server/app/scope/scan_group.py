from datetime import datetime

from flask import current_app

from app.scope.scan_manager import IPScanManager
from app.scope.scope_collection import ScopeCollection


class ScanGroup:
    """
    A scan group two scope collections:
    - One for scanning scope
    - One for blacklisted scope
    """

    def __init__(self, scope: str, blacklist: str):
        from app.models.scope_item import ScopeItem

        self.scope = ScopeCollection(ScopeItem.getScope)
        self.blacklist = ScopeCollection(ScopeItem.getBlacklist)
        self.effective_size = (self.scope.set - self.blacklist.set).size
        self.scan_manager = None

    def get_scope_size(self) -> int:
        return self.scope.size

    def get_blacklist_size(self) -> int:
        return self.blacklist.size

    def get_effective_size(self) -> int:
        return self.effective_size  # type: ignore[no-any-return]

    def get_scan_manager(self) -> None | IPScanManager:
        return self.scan_manager

    def get_last_cycle_start(self) -> None | datetime:
        if self.scan_manager is None:
            return None
        return self.scan_manager.rng.cycle_start_time  # type: ignore[unreachable]

    def get_completed_cycle_count(self) -> int:
        if self.scan_manager is None:
            return 0
        return self.scan_manager.rng.completed_cycle_count  # type: ignore[unreachable]

    def update(self) -> None:
        self.scope.update()
        self.blacklist.update()
        self.update_scan_manager()
        self.effective_size = (self.scope.set - self.blacklist.set).size

    def update_scan_manager(self) -> None:
        try:
            self.scan_manager = IPScanManager(  # type: ignore[assignment]
                self.scope.set,
                self.blacklist.set,
                current_app.config["CONSISTENT_SCAN_CYCLE"],
            )
        except Exception as e:
            if self.scan_manager is None or self.scan_manager.get_total() == 0:  # type: ignore[unreachable]
                errmsg = "Scan manager could not be instantiated because there was no scope configured."
                current_app.logger.warning(f"{datetime.utcnow()!s} - {errmsg}\n")
            else:
                raise e
