from django import test

from responsediff.test import ResponseDiffTestMixin


class MixinTest(ResponseDiffTestMixin, test.TestCase):
    def test_assertNoDiff(self):  # noqa
        self.assertResponseDiffEmpty(test.Client().get('/admin/'))
