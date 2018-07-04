# -*- coding: utf-8 -*-
import os
import re
import shutil

from django import http
from django import test

import mock

from responsediff.exceptions import DiffsFound
from responsediff.response import Response
from responsediff.test import ResponseDiffTestMixin

import six


class MixinTest(ResponseDiffTestMixin, test.TestCase):
    def get_client(self, fixtures):
        client = mock.Mock()

        client.get.side_effect = [
            http.HttpResponse(
                content='\n'.join([
                    'href="{}"'.format(i) for i in fixtures
                ]),
            ),
        ] + [
            http.HttpResponse(content=url) for url in fixtures
        ]

        return client

    def test_assertNoDiff(self):  # noqa
        self.assertResponseDiffEmpty(test.Client().get('/admin/'))

    def test_assertNoDiffSelector(self):  # noqa
        self.assertResponseDiffEmpty(test.Client().get('/admin/'), 'h1, p')

    def test_assertNoDiffSelector_non_ascii(self):  # noqa
        response = test.Client().get('/admin/')

        response.content = '<h1>à</h1>' if six.PY3 else u'<h1>à</h1>'

        # Should fail, but not with a decoding error
        with self.assertRaises(DiffsFound):
            self.assertResponseDiffEmpty(response, 'h1')

    def test_assertWebsiteSame(self):  # noqa
        subject = Response.for_test(self, url='/')

        # Ensure we're clean
        if os.path.exists(os.path.dirname(subject.content_path)):
            # pragma: no cover
            shutil.rmtree(os.path.dirname(subject.content_path))

        # First run should fail
        with self.assertRaises(DiffsFound):
            self.assertWebsiteSame()

        # Second run should pass
        self.assertWebsiteSame()

        # Let's break it
        with open(subject.content_path, 'w') as f:
            f.write('is this magic or actual software test engineering ?')

        # Should be broken
        with self.assertRaises(DiffsFound):
            self.assertWebsiteSame()

    def test_websiteTest(self):  # noqa
        path = Response.for_test(self).path
        if os.path.exists(path):  # pragma: no cover
            # Only makes sense when you're running the tests over and over
            # locally, makes no sense on single-usage containers like travis,
            # hence "no cover" above.
            shutil.rmtree(path)

        fixtures = [
            '/notrailing',
            '/notrailing?foo=bar',
            '/trailing/',
            '/trailing/?foo=bar',
        ]

        client = self.get_client(fixtures)
        covered, diffs, created = self.responsediff_website_crawl(client=client)

        expected_covered = ['/'] + fixtures
        assert covered == expected_covered

        expected_created = [
            'MixinTest.test_websiteTest/content',
            'MixinTest.test_websiteTest/metadata',
            'MixinTest.test_websiteTest/trailing/metadata',
            'MixinTest.test_websiteTest/trailing/content',
            'MixinTest.test_websiteTest/trailing/foo=bar.metadata',
            'MixinTest.test_websiteTest/trailing/foo=bar.content',
            'MixinTest.test_websiteTest/notrailing.content',
            'MixinTest.test_websiteTest/notrailing.metadata',
            'MixinTest.test_websiteTest/notrailingfoo=bar.metadata',
            'MixinTest.test_websiteTest/notrailingfoo=bar.content',
        ]
        result_created = [
            re.sub(
                '.*MixinTest.test_websiteTest',
                'MixinTest.test_websiteTest',
                c
            ) for c in created
        ]
        assert sorted(result_created) == sorted(expected_created)

        for path in created.keys():
            if 'MixinTest.test_websiteTest/content' in path:
                break

        with open(path, 'w') as f:
            f.write('fail please')

        covered, diffs, created = self.responsediff_website_crawl(
            client=self.get_client(fixtures)
        )

        expected = six.b('''
@@ -1 +1,4 @@
-fail please
\ No newline at end of file
+href="/notrailing"
+href="/notrailing?foo=bar"
+href="/trailing/"
+href="/trailing/?foo=bar"
\ No newline at end of file
        ''')

        assert list(diffs.values())[0].strip() == expected.strip()

    def test_recursion(self):
        subject = Response.for_test(self, url='/')

        # Ensure we're clean
        if os.path.exists(os.path.dirname(subject.content_path)):
            # pragma: no cover
            shutil.rmtree(os.path.dirname(subject.content_path))

        client = mock.Mock()
        client.get.return_value = http.HttpResponse(content='href="/a" href="/b"')

        result = self.responsediff_website_crawl(client=client)
        assert result[0] == ['/', '/a', '/b']
