"""Cassette tests."""
# pylint: disable=missing-docstring,too-few-public-methods


import json

from twisted.trial.unittest import TestCase

from ..cassette import Cassette
from .helpers import cassette_path


class CassetteLoadTestCase(TestCase):
    def test_room208(self):
        with open(cassette_path('room208')) as cassette_file:
            cassette = Cassette.from_dict(json.load(cassette_file))
        self.assertEqual(len(cassette), 2)
        self.assertEqual(cassette[0].request.method, 'GET')
        self.assertEqual(cassette[0].request.absoluteURI,
                         'http://room208.org/')
        self.assertEqual(cassette[0].code, 301)
        self.assertEqual(cassette[0].phrase, 'Moved Permanently')
        self.assertEqual(cassette[1].request.method, 'GET')
        self.assertEqual(cassette[1].request.absoluteURI,
                         'https://room208.org/')
        self.assertEqual(cassette[1].code, 200)
        self.assertEqual(cassette[1].phrase, 'OK')
