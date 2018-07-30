"""Convenience mixin for TestCases."""
import re

from django import test
from django.db import connections
from django.test.utils import CaptureQueriesContext

from .exceptions import DiffsFound
from .response import Response


def strip_parameters(names, url):
    """Remove GET parameters from url."""
    for name in names:
        url = re.sub(name + '=[^&]*&?', '', url)

    if url.endswith('?'):
        url = url[:-1]

    return url


class ResponseDiffTestMixin(object):
    """Adds assertResponseDiffEmpty() method."""

    def assertResponseDiffEmpty(self, result, selector=None):  # noqa
        """
        Test that result matches fixtures.

        When a selector is specified, the result will be parsed as HTML and
        only elements matching this selector will be tested.
        """
        Response.for_test(self).assertNoDiff(result, selector)

    def assertWebsiteSame(self, url=None, client=None, selector=None):  # noqa
        covered, diffs, created = self.responsediff_website_crawl(
            url, client, selector=selector)

        if created or diffs:
            raise DiffsFound(diffs, created)

        return covered

    def responsediff_website_crawl(self, url=None, client=None, covered=None,
                                   diffs=None, created=None, selector=None):
        """
        Test your website with one call to this method.

        It returns the list of covered URLs. But before, it tests that all
        fixtures for this test have been covered, or fails, requiring you the
        to remove obsolete files to succeed again.
        """
        url = url or '/'
        client = client or test.Client()
        if not covered:
            covered = getattr(self, 'covered', [])
        diffs = diffs if diffs is not None else {}
        created = created if created is not None else {}

        conn = connections['default']
        with CaptureQueriesContext(conn) as queries:
            response = client.get(url)
        self.process_response(response)
        metadata = {'query_count': len(queries)}

        _diffs, _created = Response.for_test(self, url).make_diff(
            response,
            metadata=metadata,
            # Don't apply selector on first url, so we do the layout once
            selector=selector if covered else None,
        )
        covered.append(url)
        created.update(_created)
        diffs.update(_diffs)

        if hasattr(response, 'streaming_content'):
            return covered, diffs, created

        results = re.findall(
            'href="((http://testserver)?/[^"]*)',
            response.content.decode('utf8')
        )

        for result in results:
            sub_url = re.sub(
                'http://testserver',
                '',
                result[0]
            )

            sub_url = self.transform_url(sub_url)

            if sub_url in covered:
                continue

            if self.skip_url(sub_url):
                continue

            self.responsediff_website_crawl(
                sub_url,
                client=client,
                covered=covered,
                diffs=diffs,
                created=created,
                selector=selector,
            )

        return covered, diffs, created

    def get_content_replace_patterns(self, response):
        """Return a list of pattern:replacement for response contents."""
        return [
            ('\n.*csrfmiddlewaretoken.*\n', ''),
            ('\n.*webpack.bundle.*\n', ''),
        ]

    def process_response(self, response):
        """Taint the response before saving."""
        if hasattr(response, 'streaming_content'):
            return

        for replace in self.get_content_replace_patterns(response):
            response.content = re.sub(
                replace[0],
                replace[1],
                response.content.decode('utf8')
            ).encode('utf8')

    def skip_url(self, url):
        """Return true if the url should be skipped, skips STATIC_URL."""
        from django.conf import settings
        return url.startswith(settings.STATIC_URL)

    def transform_url(self, url):
        """Return the URL to use in the registry, use this to remove params."""
        return strip_parameters(
            getattr(self, 'strip_parameters', []),
            url,
        )
