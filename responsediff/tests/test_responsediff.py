import os
import shutil
import unittest

from django import test
from django.utils import six

from responsediff.exceptions import (
    DiffFound,
    FixtureCreated,
    UnexpectedStatusCode,
)
from responsediff.response import Response


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

        if os.path.exists(expected.path):  # pragma: no cover
            # Only makes sense when you're running the tests over and over
            # locally, makes no sense on single-usage containers like travis,
            # hence "no cover" above.
            shutil.rmtree(expected.path)

        with self.assertRaises(FixtureCreated) as raises_result:
            expected.assertNoDiff(result)

        msg = (
            raises_result.exception.message
            if six.PY2 else raises_result.exception.args[0]
        )

        assert expected.content_path in msg
        assert expected.status_code_path in msg

        # should have been created
        assert os.path.exists(expected.content_path)

        # should pass now
        expected.assertNoDiff(result)

        with open(expected.content_path, 'w') as f:
            f.write('bla')

        with self.assertRaises(DiffFound) as e:
            expected.assertNoDiff(result)

        expected_diff = '''
@@ -1 +1 @@
-bla
\ No newline at end of file
+<h1>Not Found</h1><p>The requested URL /admin/ was not found on this server.</p>
\ No newline at end of file
'''.lstrip()

        diff = e.exception.message if six.PY2 else e.exception.args[0]
        result_diff = '\n'.join(diff.split('\n')[1:])
        assert result_diff == expected_diff

        # Let's fix it and test status code now
        with open(expected.content_path, 'wb') as f:
            f.write(result.content)

        # Let's mess with the status code now
        with open(expected.path + '/status_code', 'w') as f:
            f.write('418')  # RFC 2324 LOL

        with self.assertRaises(UnexpectedStatusCode) as e:
            expected.assertNoDiff(result)
