.. image:: https://travis-ci.org/yourlabs/django-responsediff.svg
    :target: https://travis-ci.org/yourlabs/django-responsediff
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

See responsediff/response.py docstrings for example usage.

Requirements
============

Python 2.7 and 3.4 are supported along with Django 1.7 to 1.10 - it's always
better to support django's master so that we can **upgrade easily when it is
released**, which is one of the selling points for having 100% coverage.

Install
=======

Install ``django-responsediff`` with pip.
