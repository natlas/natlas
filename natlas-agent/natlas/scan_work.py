from queue import Queue
from typing import Any


class ScanWorkItem:
    def __init__(self, target_data: dict[str, Any]) -> None:
        self.target_data = target_data

    def complete(self) -> None:
        pass


class ManualScanWorkItem(ScanWorkItem):
    def __init__(
        self, queue: Queue[dict[str, Any]], target_data: dict[str, Any]
    ) -> None:
        super().__init__(target_data)
        self.queue = queue

    def complete(self) -> None:
        super()
        self.queue.task_done()
