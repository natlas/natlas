from datetime import datetime, UTC
from typing import Union
from flask import current_app
from .scope_collection import ScopeCollection
from .scan_manager import IPScanManager


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
        return self.effective_size

    def get_scan_manager(self) -> Union[None, IPScanManager]:
        return self.scan_manager

    def get_last_cycle_start(self) -> Union[None, datetime]:
        if self.scan_manager is None:
            return None
        else:
            return self.scan_manager.rng.cycle_start_time

    def get_completed_cycle_count(self) -> int:
        if self.scan_manager is None:
            return 0
        else:
            return self.scan_manager.rng.completed_cycle_count

    def update(self):
        self.scope.update()
        self.blacklist.update()
        self.update_scan_manager()
        self.effective_size = (self.scope.set - self.blacklist.set).size

    def update_scan_manager(self):
        try:
            self.scan_manager = IPScanManager(
                self.scope.set,
                self.blacklist.set,
                current_app.config["CONSISTENT_SCAN_CYCLE"],
            )
        except Exception as e:
            if self.scan_manager is None or self.scan_manager.get_total() == 0:
                errmsg = "Scan manager could not be instantiated because there was no scope configured."
                current_app.logger.warning(f"{str(datetime.now(UTC))} - {errmsg}\n")
            else:
                raise e
