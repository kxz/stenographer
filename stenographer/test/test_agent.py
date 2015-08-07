"""Agent tests."""
# pylint: disable=missing-docstring,too-few-public-methods


import json

from twisted.trial.unittest import TestCase
from twisted.web.test.test_agent import (AgentTestsMixin,
                                         FakeReactorAndConnectMixin)

from ..agent import CassetteAgent
from ..cassette import Cassette
from .helpers import cassette_path


class CassetteAgentTestCase(TestCase, FakeReactorAndConnectMixin):
    def setUp(self):
        self.reactor = self.Reactor()
        self.agent = self.buildAgentForWrapperTest(self.reactor)
        self.connect(None)

    def test_saved(self):
        agent = CassetteAgent(self.agent, cassette_path('room208'))
        agent.request('GET', 'http://room208.org/')
        agent.request('GET', 'https://room208.org/')
        self.assertEqual(len(self.protocol.requests), 0)

    def test_no_saved(self):
        agent = CassetteAgent(self.agent, '')
        agent.request('GET', 'http://room208.org/')
        request, _ = self.protocol.requests.pop()
        self.assertEqual(request.method, 'GET')
        self.assertEqual(request.absoluteURI, 'http://room208.org/')

    def test_saved_mismatch(self):
        agent = CassetteAgent(self.agent, cassette_path('room208'))
        self.assertRaises(IOError, agent.request, 'GET', 'http://foo.test/')
