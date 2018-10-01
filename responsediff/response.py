"""Response object manages fixtures and does diff."""

import inspect
import json
import os
import subprocess
import tempfile

from bs4 import BeautifulSoup

from .exceptions import DiffsFound


# https://docs.microsoft.com/fr-fr/windows/desktop/FileIO/naming-a-file#naming-conventions
CROSSPLATFORM_COMPATIBLE_NOT = (
    '<', '>', ':', '"', '\\', '|', '?', '*')


def crossplatform_compatible(value):
    """Strip out caracters incompatible between platforms."""
    for i in CROSSPLATFORM_COMPATIBLE_NOT:
        value = value.replace(i, '')
    return value


def diff(first, second):
    """Return the command and diff output between first and second paths."""
    cmd = 'diff -U 1 %s %s | sed "1,2 d"' % (first, second)
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
    response.content in there, and another called ``metadata`` with additional
    information about the response in there such as the status code. The test
    would fail with a DiffsFound error containing the list of created files to
    inform the user that no test has actually been run, and that the fixture
    has just been created.

    User should add the generated fixture to the repository. Then, next time
    this test is run, it will run GNU diff between ``response.content`` and its
    metadata and the previously-generated fixture, if a diff is found then
    assertNoDiff() will raise a DiffsFound exception, printing out the diffs
    and commands used for the diffs, leaving temporary files behind for further
    investigation.
    """

    def __init__(self, path):
        """
        Instanciate a response object with a path to a fixture.

        Note that the ``for_test()`` class-method will generate a path.
        """
        self.path = path

    def assertNoDiff(self, response, selector=None):  # noqa
        """Backward compatibility method for pre-assertWebsiteSame versions."""
        diffs, created = self.make_diff(response, selector=selector)

        if created or diffs:
            raise DiffsFound(diffs, created)

    def make_diff(self, response, metadata=None, selector=None):  # noqa: C901
        """
        Compare a response object with the fixture.

        If the fixture doesn't exist, create it, otherwise run GNU-diff and
        return a list of diff outputs with their commands.

        Return created file list and dict of diffs.
        """
        if not os.path.exists(os.path.dirname(self.content_path)):
            os.makedirs(os.path.dirname(self.content_path))

        diffs = {}
        created = {}

        metadata = metadata or {}
        metadata['status_code'] = response.status_code
        if 'Location' in response:
            metadata['Location'] = response['Location']

        is_html = response['Content-Type'].startswith('text/html')
        is_streaming = hasattr(response, 'streaming_content')

        if selector and is_html and not is_streaming:
            soup = BeautifulSoup(response.content, 'html5lib')
            elements = soup.select(selector)
            content = '\n---\n'.join(map(str, elements))
            mode = 'w+'
        else:
            try:
                content = response.content
            except AttributeError:
                content = b'\n'.join(
                    [i for i in response.streaming_content]
                )
            mode = 'wb+'

        if not os.path.exists(self.content_path):
            with open(self.content_path, mode) as f:
                f.write(content)
            created[self.content_path] = content

        if not os.path.exists(self.metadata_path):
            with open(self.metadata_path, 'w+') as f:
                json.dump(metadata, f, indent=4, sort_keys=True)
            created[self.metadata_path] = json.dumps(metadata, indent=4)

        fh, dump_path = tempfile.mkstemp('_responsediff')
        with os.fdopen(fh, mode) as f:
            f.write(content)

        cmd, out = diff(self.content_path, dump_path)
        if out:
            diffs[cmd] = out

        metadata_fh, metadata_dump_path = tempfile.mkstemp('_responsediff')
        with os.fdopen(metadata_fh, 'w') as f:
            json.dump(metadata, f, indent=4, sort_keys=True)

        cmd, out = diff(self.metadata_path, metadata_dump_path)
        if out:
            diffs[cmd] = out

        return diffs, created

    def filesystem_path(self, suffix):
        """Return the filesystem path for fixture."""
        if self.path.endswith('/'):
            path = os.path.join(self.path, suffix)
        else:
            path = self.path + '.' + suffix
        return crossplatform_compatible(path)

    @property
    def metadata_path(self):
        """Return the path to the file for the response.metadata."""
        return self.filesystem_path('metadata')

    @property
    def content_path(self):
        """Return the path to the file for the response.content contents."""
        return self.filesystem_path('content')

    @classmethod
    def for_test(cls, case, url=None, *args, **kwargs):
        """Instanciate a Response with a path for the case and url if any."""
        name = '.'.join(case.id().split('.')[-2:])

        path = os.path.join(
            os.path.abspath(os.path.dirname(inspect.getfile(type(case)))),
            'response_fixtures',
            name
        )

        if url:
            path = os.path.join(
                path,
                *[p for p in url.split('/') if p]
            )

            if url.endswith('/'):
                path += '/'

        return cls(path, *args, **kwargs)
