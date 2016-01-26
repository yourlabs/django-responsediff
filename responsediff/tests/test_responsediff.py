import os
import shutil
import unittest

from django import test
from django.utils import six

from responsediff.exceptions import DiffFound, FixtureCreated
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

        if os.path.exists(expected.path):
            shutil.rmtree(expected.path)

        with self.assertRaises(FixtureCreated):
            expected.assertNoDiff(result)

        # should have been created
        assert os.path.exists(expected.content_path)

        # should pass now
        expected.assertNoDiff(result)

        with open(expected.content_path, 'w') as f:
            f.write('bla')

        with self.assertRaises(DiffFound) as e:
            expected.assertNoDiff(result)

        expected = '''
@@ -1 +1 @@
-bla
\ No newline at end of file
+<h1>Not Found</h1><p>The requested URL /admin/ was not found on this server.</p>
\ No newline at end of file
'''.lstrip()

        diff = e.exception.message if six.PY2 else e.exception.args[0]
        result = '\n'.join(diff.split('\n')[1:])
        assert result == expected
