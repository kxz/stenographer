"""Agent tests."""
# pylint: disable=missing-docstring,too-few-public-methods


from twisted.trial.unittest import TestCase
from twisted.web.test.test_agent import FakeReactorAndConnectMixin

from ..agent import CassetteAgent
from .helpers import cassette_path


class CassetteAgentTestCase(FakeReactorAndConnectMixin, TestCase):
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
        finished = agent.request('GET', 'http://foo.test/')
        return self.assertFailure(finished, IOError)
