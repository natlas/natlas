from netaddr import IPNetwork, IPSet


class ScopeCollection:
    size = 0

    def __init__(self, scope_source: callable):  # type: ignore[valid-type]
        """
        name: A name for this collection of scopes
        scope_source: A callable that returns a collection of ScopeItem
        """
        self.scope_source = scope_source
        self.list: list[IPNetwork] = []
        self.set = IPSet()

    def update(self) -> None:
        self.list = [IPNetwork(item.target, False) for item in self.scope_source()]  # type: ignore[misc]
        self.set = IPSet(self.list)
        self.size = self.set.size
