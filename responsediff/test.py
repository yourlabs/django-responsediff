"""Convenience mixin for TestCases."""
import re

from django import test
from django.db import connections
from django.test.utils import CaptureQueriesContext

from .exceptions import DiffsFound
from .response import Response


class ResponseDiffTestMixin(object):
    """Adds assertResponseDiffEmpty() method."""

    def assertResponseDiffEmpty(self, result):  # noqa
        """Test that result matches fixtures."""
        Response.for_test(self).assertNoDiff(result)

    def assertWebsiteSame(self, url=None, client=None):  # noqa
        covered, diffs, created = self.responsediff_website_crawl(url, client)

        if created or diffs:
            raise DiffsFound(diffs, created)

        return covered

    def responsediff_website_crawl(self, url=None, client=None, covered=None,
                                   diffs=None, created=None):
        """
        Test your website with one call to this method.

        It returns the list of covered URLs. But before, it tests that all
        fixtures for this test have been covered, or fails, requiring you the
        to remove obsolete files to succeed again.
        """
        url = url or '/'
        client = client or test.Client()
        covered = covered or []
        diffs = diffs or {}
        created = created or {}

        conn = connections['default']
        with CaptureQueriesContext(conn) as queries:
            response = client.get(url)
        metadata = {'query_count': len(queries)}

        _diffs, _created = Response.for_test(self, url).make_diff(
            response,
            metadata=metadata
        )
        covered.append(url)
        created.update(_created)
        diffs.update(_diffs)

        results = re.findall(
            '"((http://testserver)?/[^"]*)',
            response.content.decode('utf8')
        )

        for result in results:
            sub_url = re.sub(
                'http://testserver',
                '',
                result[0]
            )

            if sub_url in covered:
                continue

            self.responsediff_website_crawl(
                sub_url,
                client=client,
                covered=covered,
                diffs=diffs,
                created=created
            )

        return covered, diffs, created
