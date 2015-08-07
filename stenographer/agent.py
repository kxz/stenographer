"""Custom Twisted Web Agents."""


import errno
import json

from twisted.internet.defer import succeed, inlineCallbacks, returnValue

from .cassette import Cassette
from .proxy import RecordingBodyProducer, RecordingResponse


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

    def request(self, *args, **kwargs):
        """Replay a recorded HTTP request, or make and record an actual
        request if no recording exists."""
        if not self.recording:
            return self.replay_request(*args, **kwargs)
        finished = self.agent.request(*args, **kwargs)
        finished.addCallback(RecordingResponse)  # wrap the response
        finished.addCallback(self.cassette.responses.append)
        return finished

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
                json.dump(self.cassette, cassette_file)
        return deferred_result
