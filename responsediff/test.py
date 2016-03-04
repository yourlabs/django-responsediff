"""Convenience mixin for TestCases."""

from .response import Response


class ResponseDiffTestMixin(object):
    """Adds assertResponseDiffEmpty() method."""

    def assertResponseDiffEmpty(self, result):  # noqa
        """Test that result matches fixtures."""
        Response.for_test(self).assertNoDiff(result)
