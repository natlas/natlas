from netaddr import IPNetwork, IPSet


class ScopeCollection:
    list = []
    set = IPSet()
    size = 0

    def __init__(self, scope_source: callable):
        """
        name: A name for this collection of scopes
        scope_source: A callable that returns a collection of ScopeItem
        """
        self.scope_source = scope_source

    def update(self):
        self.list = [IPNetwork(item.target, False) for item in self.scope_source()]
        self.set = IPSet(self.list)
        self.size = self.set.size
