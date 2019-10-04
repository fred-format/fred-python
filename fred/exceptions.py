class FREDDecodeError(ValueError):
    """Subclass of ValueError with additional properties.

    Attributes:
        msg:
            The unformatted error message
        pos:
            The start index of doc where parsing failed
        lineno:
            The line corresponding to pos
        colno:
            The column corresponding to pos
    """

    doc = None
    line = property(lambda self: self.lineno)
    column = property(lambda self: self.colno)

    @classmethod
    def from_token(cls, msg, tk):
        """
        Create exception from token object.

        If a string is passed, set lineno and colno to None.
        """
        line_no = getattr(tk, "line", None)
        col_no = getattr(tk, "column", None)
        return cls(msg, line_no, col_no)

    def __init__(self, msg, lineno, colno):
        # lineno = doc.count('\n', 0, pos) + 1
        # colno = pos - doc.rfind('\n', 0, pos)
        # errmsg = '%s: line %d column %d (char %d)' % (msg, lineno, colno, pos)
        error_msg = msg
        ValueError.__init__(self, error_msg)
        self.msg = msg
        self.lineno = lineno
        self.colno = colno

    def __reduce__(self):
        return self.__class__, (self.msg, self.lineno, self.colno)