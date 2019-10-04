class Context:
    @property
    def path(self) -> str:
        base = "/".join(self._paths)
        return base + "/" + str(self._field) if self._field else base

    def __init__(self):
        self._paths = []
        self._field = None

    def push_path(self, path):
        self._paths.append(path)

    def pop_path(self):
        self._paths.pop()

    def set_field(self, field):
        self._field = field

    def type_error(self, msg):
        raise TypeError(f"({self.path}) {msg}")

    def value_error(self, msg):
        raise ValueError(f"({self.path}) {msg}")
