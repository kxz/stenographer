"""Agent tests."""
# pylint: disable=missing-docstring,too-few-public-methods


import sys

from twisted.internet.defer import inlineCallbacks, returnValue
from twisted.python.failure import Failure
from twisted.trial.unittest import TestCase
from twisted.web.client import Headers, Response, ResponseDone, readBody
from twisted.web.test.test_agent import (AbortableStringTransport,
                                         FakeReactorAndConnectMixin)

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

    def test_content_length_known(self):
        agent = CassetteAgent(self.agent, '')
        finished = agent.request('GET', 'http://foo.test/')
        request, result = self.protocol.requests.pop()
        response = Response._construct(('HTTP', 1, 1), 200, 'OK', Headers(),
                                       AbortableStringTransport(), request)
        response.length = 9001
        response._bodyDataFinished()
        result.callback(response)
        finished.addCallback(readBody)
        def assert_correct_length(deferred_result):
            interaction = agent.cassette.as_dict()['http_interactions'][0]
            self.assertEqual(
                [response.length],
                interaction['response']['headers']['Content-Length'])
            return deferred_result
        finished.addCallback(assert_correct_length)
        return finished

    def test_content_length_unknown(self):
        agent = CassetteAgent(self.agent, '')
        finished = agent.request('GET', 'http://foo.test/')
        request, result = self.protocol.requests.pop()
        response = Response._construct(('HTTP', 1, 1), 200, 'OK', Headers(),
                                       AbortableStringTransport(), request)
        response._bodyDataFinished()
        result.callback(response)
        finished.addCallback(readBody)
        def assert_length_absent(deferred_result):
            interaction = agent.cassette.as_dict()['http_interactions'][0]
            self.assertFalse(
                interaction['response']['headers'].get('Content-Length'))
            return deferred_result
        finished.addCallback(assert_length_absent)
        return finished

    def test_header_isolation(self):
        agent = CassetteAgent(self.agent, '')
        finished = agent.request('GET', 'http://foo.test/')
        request, result = self.protocol.requests.pop()
        headers = Headers()
        headers.addRawHeader('Content-Encoding', 'gzip')
        response = Response._construct(('HTTP', 1, 1), 200, 'OK', headers,
                                       AbortableStringTransport(), request)
        response._bodyDataFinished()
        result.callback(response)
        @inlineCallbacks
        def assert_intact_headers(agent_response):
            yield readBody(agent_response)
            agent_response.headers.removeHeader('Content-Encoding')
            interaction = agent.cassette.as_dict()['http_interactions'][0]
            self.assertEqual(
                ['gzip'],
                interaction['response']['headers']['Content-Encoding'])
            returnValue(agent_response)
        finished.addCallback(assert_intact_headers)
        return finished
