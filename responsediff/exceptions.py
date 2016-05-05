"""Exceptions for responsediff module."""


class ResponseDiffException(Exception):
    """Base exception for this app."""


class DiffFound(ResponseDiffException):
    """Raised when a diff is found by the context manager."""

    def __init__(self, cmd, out):
        """Exception for when a diff command had output."""
        super(DiffFound, self).__init__('%s\n%s' % (cmd, out.decode('utf8')))


class UnexpectedStatusCode(ResponseDiffException):
    """Raised when the status_code has changed."""

    def __init__(self, expected, result):
        """Exception for when the result's status_code is different."""
        super(UnexpectedStatusCode, self).__init__(
            'Expected status code %s, got %s' % (expected, result)
        )


class FixtureCreated(ResponseDiffException):
    """
    Raised when a fixture was created.

    This purposely fails a test, to avoid misleading the user into thinking
    that the test was properly executed against a versioned fixture. Imagine
    one pushes a test without the fixture, it will break because of this
    exception in CI.

    However, this should only happen once per fixture - unless the user in
    question forgets to commit the generated fixture !
    """
    def __init__(self, fixture):
        super(FixtureCreated, self).__init__(
            'Created fixture in %s' % ', '.join(fixture),
        )
