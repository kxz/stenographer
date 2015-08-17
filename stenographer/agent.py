"""Custom Twisted Web Agents."""


import errno
import json

from twisted.internet.defer import succeed, inlineCallbacks, returnValue

from .cassette import Cassette
from .proxy import RecordingBodyProducer, RecordingResponse, IsolatingResponse


class CassetteAgent(object):
    """A Twisted Web `Agent` that reconstructs a `Response` object from
    a recorded HTTP response in JSON-serialized VCR cassette format, or
    records a new cassette if none exists."""

    def __init__(self, agent, cassette_path):
        self.agent = agent
        self.recording = True
        self.cassette_path = cassette_path
        self.index = 0
        try:
            with open(self.cassette_path) as cassette_file:
                self.cassette = Cassette.from_dict(json.load(cassette_file))
        except IOError as e:
            if e.errno != errno.ENOENT:
                raise
            self.cassette = Cassette()
        else:
            self.recording = False

    @inlineCallbacks
    def request(self, method, uri, headers=None, bodyProducer=None):
        """Replay a recorded HTTP request, or make and record an actual
        request if no recording exists."""
        if not self.recording:
            response = yield self.replay_request(
                method, uri, headers, bodyProducer)
            returnValue(response)
        if bodyProducer is not None:
            bodyProducer = RecordingBodyProducer(bodyProducer)
        real_response = yield self.agent.request(
            method, uri, headers, bodyProducer)
        response = RecordingResponse(real_response)
        self.cassette.responses.append(response)
        # We have to do this because ContentDecoderAgent mutates the
        # response headers.  I don't like it, but them's the breaks.
        returnValue(IsolatingResponse(response))

    def replay_request(self, method, uri, headers=None, bodyProducer=None):
        """Replay a recorded HTTP request.  Raise `IOError` if the
        recorded request does not match the one being made, like VCR's
        ``once`` record mode."""
        try:
            response = self.cassette[self.index]
        except IndexError:
            raise IOError('no more saved interactions for current {} '
                          'request for {}'.format(method, uri))
        self.index += 1
        if not (method == response.request.method and
                uri == response.request.absoluteURI):
            raise IOError(
                'current {} request for {} differs from saved {} '
                'request for {}'.format(method, uri,
                                        response.request.method,
                                        response.request.absoluteURI))
        return succeed(response)

    def save(self, deferred_result=None):
        """Record interactions in this agent's cassette path."""
        if self.recording:
            with open(self.cassette_path, 'w') as cassette_file:
                json.dump(self.cassette.as_dict(), cassette_file)
        return deferred_result
