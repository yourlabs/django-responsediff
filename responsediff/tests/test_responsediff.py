import json
import os
import unittest

from django import test
from django.utils import six

import pytest

from responsediff.exceptions import DiffsFound
from responsediff.response import Response
from responsediff.test import strip_parameters


@pytest.mark.parametrize('fixture,expected', [
    ('aoeu/?_a=aoeu', 'aoeu/'),
    ('aoeu?_a=aoeu', 'aoeu'),
    ('aoeu?_a=aoeu&b=2', 'aoeu?b=2'),
])
def test_strip_parameters(fixture, expected):  # noqa: D103
    assert strip_parameters(['_a'], fixture) == expected


class TestResponseDiff(unittest.TestCase):
    def test_path(self):
        expected = os.path.join(
            os.path.abspath(os.path.dirname(__file__)),
            'response_fixtures',
            'TestResponseDiff.test_path'
        )

        assert Response.for_test(self).path == expected

    def test_story(self):
        result = test.Client().get('/admin/')
        expected = Response.for_test(self)

        if os.path.exists(expected.content_path):  # pragma: no cover
            # Only makes sense when you're running the tests over and over
            # locally, makes no sense on single-usage containers like travis,
            # hence "no cover" above.
            os.unlink(expected.content_path)

        if os.path.exists(expected.metadata_path):  # pragma: no cover
            os.unlink(expected.metadata_path)

        with self.assertRaises(DiffsFound) as raises_result:
            expected.assertNoDiff(result)

        msg = (
            raises_result.exception.message
            if six.PY2 else raises_result.exception.args[0]
        )

        assert expected.content_path in msg
        assert expected.metadata_path in msg

        # should have been created
        assert os.path.exists(expected.content_path)

        # should pass now
        expected.assertNoDiff(result)

        with open(expected.content_path, 'w') as f:
            f.write('bla')

        with self.assertRaises(DiffsFound) as e:
            expected.assertNoDiff(result)

        expected_diff = '''
@@ -1 +1 @@
-bla
\ No newline at end of file
+<h1>Not Found</h1><p>The requested URL /admin/ was not found on this server.</p>
\ No newline at end of file
'''.lstrip()

        diff = e.exception.message if six.PY2 else e.exception.args[0]
        result_diff = '\n'.join(diff.split('\n')[2:])
        assert result_diff == expected_diff

        # Let's fix it and test status code now
        with open(expected.content_path, 'wb') as f:
            f.write(result.content)

        # Let's mess with the status code now
        with open(expected.metadata_path, 'w') as f:
            json.dump(
                {
                    'status_code': 418,  # RFC 2324 LOL
                },
                f,
                indent=4
            )

        with self.assertRaises(DiffsFound) as e:
            expected.assertNoDiff(result)
