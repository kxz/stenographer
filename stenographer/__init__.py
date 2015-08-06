"""Stenographer, an HTTP interaction recorder for Twisted Web."""


from base64 import b64encode, b64decode
import errno
from email.utils import formatdate
from io import BytesIO
import json
from urlparse import urlparse, urlunparse

from twisted.internet.defer import succeed, inlineCallbacks, returnValue
from twisted.web.client import FileBodyProducer, URI, readBody
from twisted.web.http_headers import Headers
from twisted.web.test.test_agent import AbortableStringTransport
from twisted.web._newclient import Request, Response


__version__ = '0.1-dev'


class CassetteAgent(object):
    """A Twisted Web `Agent` that reconstructs a `Response` object from
    a recorded HTTP response in JSON-serialized VCR cassette format, or
    records a new cassette if none exists."""

    version = 'Stenographer {}'.format(__version__)

    def __init__(self, agent, cassette_path):
        self.agent = agent
        self.interactions = []
        self.recording = True
        self.cassette_path = cassette_path
        try:
            with open(self.cassette_path) as cassette_file:
                cassette = json.load(cassette_file)
        except IOError as e:
            if e.errno != errno.ENOENT:
                raise
        else:
            self.interactions = cassette['http_interactions']
            self.recording = False
            self.request = self.replay_request

    @staticmethod
    def _body_of(message):
        """Return the decoded body of a recorded *message*."""
        body = message['body']
        if 'base64_string' in body:
            return b64decode(body['base64_string'])
        return body['string'].encode(body['encoding'])

    @staticmethod
    def _make_body(string, headers=None):
        """Return a VCR-style body dict from *body_string*."""
        body = {'encoding': 'utf-8'}
        if (headers and
                'gzip' in headers.getRawHeaders('content-encoding', [])):
            body['base64_string'] = b64encode(string)
        else:
            body['string'] = string
        return body

    @inlineCallbacks
    def request(self, method, uri, headers=None, bodyProducer=None):
        """Replay a recorded HTTP request, or make and record an actual
        request if no recording exists."""
        if not self.recording:
            response = yield self.replay_request(method, uri,
                                                 headers, bodyProducer)
            returnValue(response)
        if bodyProducer:
            body_length = body_producer.length
            transport = AbortableStringTransport()
            yield body_producer.startProducing(transport)
            body_string = transport.value()
            body = CassetteAgent._make_body(body_string, headers)
            # Create a new BodyProducer that looks like the old one.
            bodyProducer = FileBodyProducer(BytesIO(body_string))
            bodyProducer.length = body_length
        else:
            body = {'encoding': 'utf-8', 'string': ''}
        rq = {
            'method': method, 'uri': uri, 'body': body,
            'headers': {k: v for k, v in headers.getAllRawHeaders()}}
        response = yield self.agent.request(method, uri, headers, bodyProducer)
        body_string = yield readBody(response)
        rp = {
            'http_version': '1.1',  # only thing Twisted Web supports
            'status': {'code': response.code, 'message': response.phrase},
            'headers': {k: v for k, v in response.headers.getAllRawHeaders()},
            'body': CassetteAgent._make_body(body_string, response.headers)}
        self.interactions.append({'request': rq, 'response': rp,
                                  'recorded_at': formatdate()})
        # Make a new Response on which deliverBody can still be called,
        # and return that instead of the original Response.
        response = Response._construct(
            response.version, response.code, response.phrase,
            response.headers, AbortableStringTransport(), response.request)
        response._bodyDataReceived(body_string)
        response._bodyDataFinished()
        returnValue(response)

    def replay_request(self, method, uri, headers=None, bodyProducer=None):
        """Replay a recorded HTTP request.  Raise `IOError` if the
        recorded request does not match the one being made, like VCR's
        ``once`` record mode."""
        try:
            interaction = self.interactions.pop(0)
        except IndexError:
            raise IOError('no more saved interactions for current {} '
                          'request for {}'.format(method, uri))
        rq = interaction['request']
        # TODO:  Implement looser request matching.
        if not (method == rq['method'] and uri == rq['uri']):
            raise IOError('current {} request for {} differs from '
                          'saved {} request for {}'.format(
                method, uri, rq['method'], rq['uri']))
        # Overwrite the scheme and netloc, leaving just the part of the
        # URI that would be sent in a real request.
        relative_uri = urlunparse(('', '') + urlparse(rq['uri'])[2:])
        request = Request._construct(
            rq['method'], relative_uri, Headers(rq['headers']),
            FileBodyProducer(BytesIO(CassetteAgent._body_of(rq))),
            False, URI.fromBytes(rq['uri'].encode('utf-8')))
        rp = interaction['response']
        response = Response._construct(
            ('HTTP', 1, 1), rp['status']['code'], rp['status']['message'],
            Headers(rp['headers']), AbortableStringTransport(), request)
        response._bodyDataReceived(CassetteAgent._body_of(rp))
        response._bodyDataFinished()
        return succeed(response)

    def save(self, deferred_result=None):
        """Record interactions in this agent's cassette path."""
        if not self.recording:
            return deferred_result
        cassette = {'http_interactions': self.interactions,
                    'recorded_with': self.version}
        with open(self.cassette_path, 'w') as cassette_file:
            json.dump(cassette, cassette_file)
        return deferred_result

    def save_after(self, deferred):
        """Add `save` as a callback to the given `Deferred`."""
        deferred.addBoth(self.save)
