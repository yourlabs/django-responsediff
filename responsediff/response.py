"""Response object manages fixtures and does diff."""

import inspect
import os
import subprocess
import tempfile

from django.utils import six

from .exceptions import (
    DiffFound,
    FixtureCreated,
    UnexpectedStatusCode,
)


def diff(first, second):
    """Return the command and diff output between first and second paths."""
    cmd = 'diff -u1 %s %s | sed "1,2 d"' % (first, second)
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
    out, err = proc.communicate()
    return cmd, out


class Response(object):
    """
    Object to use in tests.

    Consider this example:

    .. code-block:: python

        class TestYourView(TestCase):
            def test_your_page(self):
                result = test.Client().get(your_url)

                # Factory to create a Response for this test
                expected = Response.for_test(self)

                # Generate the fixture if necessary, otherwise GNU diff-it
                expected.assertNoDiff(result)

    This would create a directory in the directory containing TestYourView,
    named ``responsediff_fixtures``, with a sub-directory
    ``TestYourView.test_your_page`` and a file ``content`` with
    response.content in there, if it does not already exist, and raise
    ``FixtureCreated`` to inform the user that no test has actually been run,
    and that the fixture has just been created.

    User should add the generated fixture to the repository. Then, next time
    this test is run, it will run GNU diff between ``response.content`` and the
    previously-generated fixture, if a diff is found then assertNoDiff() will
    raise a DiffFound exception, printing out the diff file.
    """

    def __init__(self, path):
        """
        Instanciate a response object with a path to a fixture.

        Note that the ``for_test()`` class-method will generate a path.
        """
        self.path = path

    def assertNoDiff(self, response):  # noqa
        """
        Compare a response object with the fixture.

        If the fixture doesn't exist, create it and raise FixtureCreated(),
        otherwise run GNU-diff and raise DiffFound if it finds any diff.
        """
        if not os.path.exists(self.path):
            os.makedirs(self.path)

        created = []

        if not os.path.exists(self.content_path):
            with open(self.content_path, 'wb+') as f:
                f.write(response.content)
            created.append(self.content_path)

        if not os.path.exists(self.status_code_path):
            with open(self.status_code_path, 'w+') as f:
                f.write(six.text_type(response.status_code))
            created.append(self.status_code_path)

        if created:
            raise FixtureCreated(created)

        fh, dump_path = tempfile.mkstemp('_responsediff')
        with os.fdopen(fh, 'wb') as f:
            f.write(response.content)

        cmd, out = diff(self.content_path, dump_path)

        if out:
            raise DiffFound(cmd, out)

        with open(self.status_code_path, 'r') as f:
            expected = int(f.read())

        if expected != response.status_code:
            raise UnexpectedStatusCode(expected, response.status_code)

    @property
    def status_code_path(self):
        """Return the path to the file for the response.status_code."""
        return os.path.join(self.path, 'status_code')

    @property
    def content_path(self):
        """Return the path to the file for the response.content contents."""
        return os.path.join(self.path, 'content')

    @classmethod
    def for_test(cls, case, *args, **kwargs):
        """Instanciate a Response with a path for the case in question."""
        name = '.'.join(case.id().split('.')[-2:])

        path = os.path.join(
            os.path.abspath(os.path.dirname(inspect.getfile(type(case)))),
            'response_fixtures',
            name
        )

        return cls(path, *args, **kwargs)
