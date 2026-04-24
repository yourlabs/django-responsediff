.. image:: https://github.com/yourlabs/django-responsediff/actions/workflows/ci.yml/badge.svg
    :target: https://github.com/yourlabs/django-responsediff/actions/workflows/ci.yml
.. image:: https://codecov.io/github/yourlabs/django-responsediff/coverage.svg?branch=master
    :target: https://codecov.io/github/yourlabs/django-responsediff?branch=master
.. image:: https://badge.fury.io/py/django-responsediff.png
   :target: http://badge.fury.io/py/django-responsediff

django-responsediff
~~~~~~~~~~~~~~~~~~~

I'm pretty lazy when it comes to writing tests for existing code, however, I'm
even lazier when it comes to repetitive manual testing action.

This package aims at de-duplicating view tests inside the political-memory
itself and to make it reusable for other apps.

It's pretty much the same as django-dbdiff, except this is for HTTP response.

Response state assertion
========================

When my user tests, he browses the website and checks that everything is
rendered fine. This app allows to do high-level checks of HTML rendering.

See responsediff/response.py docstrings for example usage, or use the
conveniance mixin::

    from responsediff.test import ResponseDiffTestMixin

    class MixinTest(ResponseDiffTestMixin, test.TestCase):
        def test_admin(self):
            self.assertResponseDiffEmpty(test.Client().get('/admin/'))

The above will fail on the first time with ``DiffsFound`` to indicate that
it has written
``responsediff/tests/response_fixtures/MixinTest.test_admin/{content,metadata}``.
These files are meant to be added to version control. So next time this will
run, it will check that ``response.status_code`` and ``response.content`` are
the same, in future versions, or in other configurations.

Instead of deleting the fixtures manually before running the tests to
regenerate them, just run your tests with ``FIXTURE_REWRITE=1`` environment
variable. This will overwrite the fixtures and make the tests look like they
passed.

You can also use ``assertWebsiteSame`` to crawl your site automatically::

    class SiteTest(ResponseDiffTestMixin, test.TestCase):
        def test_site(self):
            self.assertWebsiteSame()

Requirements
============

Python 3.10 through 3.14 and Django 4.2 (LTS), 5.2 (LTS), and 6.0 are
supported. Install with pip::

    pip install django-responsediff

Related app
===========

A somewhat similar app which inspired django-responsediff is `django-test-utils
<https://github.com/ericholscher/django-test-utils>`_.
