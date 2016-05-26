"""Exceptions for responsediff module."""


class ResponseDiffException(Exception):
    """Base exception for this app."""


class DiffsFound(ResponseDiffException):
    """Raised when a test has failed."""

    def __init__(self, diffs, created):
        """Exception for when a diff command had output."""
        message = [''] + [  # one empty line
            '[created] %s:\n%s' % (k, v[:60]) for k, v in created.items()
        ] + [
            '%s\n%s' % (cmd, out.decode('utf8'))
            for cmd, out in diffs.items()
        ]
        super(DiffsFound, self).__init__('\n'.join(message))
