"""HTTP interaction cassettes and related classes."""
# -*- test-case-name: stenographer.test.test_cassette


from collections import Sequence
from base64 import b64encode, b64decode
from email.utils import formatdate
from urlparse import urlparse, urlunparse

from twisted.web.client import URI
from twisted.web.http_headers import Headers
from twisted.web.iweb import UNKNOWN_LENGTH
from twisted.web._newclient import Request, Response
from twisted.web.test.test_agent import AbortableStringTransport

from .proxy import SavedBodyProducer, SavedResponse
from .__version__ import __version__


def body_from_dict(dct):
    """Decode and return a body string from a VCR request or response
    dict."""
    body = dct['body']
    if 'base64_string' in body:
        return b64decode(body['base64_string'])
    return body['string'].encode(body['encoding'])


def body_as_dict(string, headers=None, preserve_exact_body_bytes=False):
    """Encode a body string into a VCR body dict and return it,
    according to the given HTTP headers."""
    body = {'encoding': 'utf-8'}
    gzip_encoded = (
        headers and 'gzip' in headers.getRawHeaders('Content-Encoding', []))
    if preserve_exact_body_bytes or gzip_encoded:
        body['base64_string'] = b64encode(string)
    else:
        body['string'] = string
    return body


def headers_as_dict(headers):
    """Encode a Twisted `Headers` object into a VCR header dict."""
    return {k: v for k, v in headers.getAllRawHeaders()}


class Cassette(Sequence):
    """A container for recorded HTTP interactions."""

    def __init__(self):
        #: A list of `RecordingResponse` objects resulting from
        #: recorded interactions.
        self.responses = []

    @classmethod
    def from_dict(cls, dct):
        """Create a new cassette from *dct*, as deserialized from JSON
        or YAML format."""
        cassette = cls()
        for interaction in dct['http_interactions']:
            rq = interaction['request']
            # Overwrite the scheme and netloc, leaving just the part of
            # the URI that would be sent in a real request.
            relative_uri = urlunparse(('', '') + urlparse(rq['uri'])[2:])
            request = Request._construct(
                rq['method'], relative_uri, Headers(rq['headers']),
                SavedBodyProducer(body_from_dict(rq)),
                False, URI.fromBytes(rq['uri'].encode('utf-8')))
            rp = interaction['response']
            response = Response._construct(
                ('HTTP', 1, 1), rp['status']['code'], rp['status']['message'],
                Headers(rp['headers']), AbortableStringTransport(), request)
            content_length = response.headers.getRawHeaders('Content-Length')
            if content_length:
                try:
                    response.length = int(content_length[0])
                except ValueError:
                    pass
            cassette.responses.append(
                SavedResponse(response, body_from_dict(rp)))
        return cassette

    def __getitem__(self, index):
        return self.responses[index]

    def __len__(self):
        return len(self.responses)

    def as_dict(self, preserve_exact_body_bytes=False):
        """Return a dictionary representation of this cassette, suitable
        for serializing in JSON or YAML format."""
        http_interactions = []
        for response in self.responses:
            # `Response._construct` wraps the original request in a
            # proxy for `IClientRequest`, so we have to fish it out.
            request = response.request.original
            if request.bodyProducer is None:
                request_body = {'encoding': 'utf-8', 'string': ''}
            else:
                request_body = body_as_dict(
                    request.bodyProducer.value(), request.headers,
                    preserve_exact_body_bytes)
            # Twisted also eats any "Content-Length" header provided to
            # us, so we have to reconstruct it if it's present.
            if response.length is not UNKNOWN_LENGTH:
                response.headers.setRawHeaders('Content-Length',
                                               [response.length])
            http_interactions.append({
                'request': {
                    'method': request.method,
                    'uri': request.absoluteURI,
                    'body': request_body,
                    'headers': headers_as_dict(request.headers)},
                'response': {
                    'http_version': '1.1',  # only one Twisted Web supports
                    'status': {'code': response.code,
                               'message': response.phrase},
                    'body': body_as_dict(response.value(), response.headers,
                                         preserve_exact_body_bytes),
                    'headers': headers_as_dict(response.headers)},
                'recorded_at': formatdate()})
        return {'http_interactions': http_interactions,
                'recorded_with': 'Stenographer {}'.format(__version__)}
