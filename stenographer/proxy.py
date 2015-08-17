"""Proxy classes for Twisted components."""
# -*- test-case-name: stenographer.test.test_proxy


from io import BytesIO

from twisted.internet.interfaces import IConsumer, IProtocol
from twisted.python.components import proxyForInterface
from twisted.web.client import FileBodyProducer
from twisted.web.iweb import IBodyProducer, IResponse


class RecordingConsumer(proxyForInterface(IConsumer)):
    """An `IConsumer` implementation that wraps another, recording any
    consumed data."""

    def __init__(self, original):
        self.original = original
        self.io = BytesIO()

    def write(self, data):
        """See `IConsumer.write`."""
        self.io.write(data)
        self.original.write(data)


class RecordingBodyProducer(proxyForInterface(IBodyProducer)):
    """An `IBodyProducer` implementation that wraps another, recording
    any bytes produced to its consumer."""

    def __init__(self, original):
        self.original = original
        self.consumer = None

    def startProducing(self, consumer):
        """See `IBodyProducer.startProducing`."""
        self.consumer = RecordingConsumer(consumer)
        return self.original.startProducing(self.consumer)

    def value(self):
        """Return a byte string containing any bytes produced."""
        if self.consumer is None:
            raise ValueError('no consumer started yet')
        return self.consumer.io.getvalue()


class RecordingProtocol(proxyForInterface(IProtocol)):
    """An `IProtocol` implementation that wraps another, recording any
    received data."""

    def __init__(self, original):
        self.original = original
        self.io = BytesIO()

    def dataReceived(self, data):
        """See `IProtocol.dataReceived`."""
        self.io.write(data)
        self.original.dataReceived(data)


class RecordingResponse(proxyForInterface(IResponse)):
    """An `IResponse` implementation that records body bytes delivered
    to its protocol by wrapping it in `RecordingProtocol`."""

    def __init__(self, original):
        self.original = original
        self.protocol = None

    def deliverBody(self, protocol):
        """See `IResponse.deliverBody`."""
        self.protocol = RecordingProtocol(protocol)
        self.original.deliverBody(self.protocol)

    def value(self):
        """Return a byte string containing the delivered body bytes."""
        if self.protocol is None:
            raise ValueError('response body not yet delivered')
        return self.protocol.io.getvalue()


class IsolatingResponse(proxyForInterface(IResponse)):
    """An `IResponse` implementation that wraps another and presents
    copies of its mutable attributes, preserving the original values.
    """

    def __init__(self, original):
        self.original = original
        self._headers = original.headers.copy()

    @property
    def headers(self):
        return self._headers


class SavedBodyProducer(FileBodyProducer):
    """An `IBodyProducer` that returns a predetermined byte string."""

    def __init__(self, value):
        self._value = value
        FileBodyProducer.__init__(self, BytesIO(value))

    def value(self):
        """Return the byte string this producer was initialized with."""
        return self._value


class SavedResponse(proxyForInterface(IResponse)):
    """An `IResponse` that returns a predetermined byte string."""

    def __init__(self, original, value):
        self.original = original
        self._value = value
        self.original._bodyDataReceived(value)
        self.original._bodyDataFinished()

    def value(self):
        """Return the byte string this response was initialized with."""
        return self._value
