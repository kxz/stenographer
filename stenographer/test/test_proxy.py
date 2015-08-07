"""Twisted component proxy tests."""
# pylint: disable=missing-docstring,too-few-public-methods


from io import BytesIO
from textwrap import dedent

from twisted.internet.defer import inlineCallbacks
from twisted.trial.unittest import TestCase
from twisted.web.client import FileBodyProducer, Response, readBody
from twisted.web.http_headers import Headers
from twisted.web.test.test_agent import AbortableStringTransport

from ..proxy import RecordingBodyProducer, RecordingResponse


LOREM_IPSUM = dedent("""\
    Iliquiscipis laortie issendiam.  Aciliqu eniscip nostra nostie
    etueratem primis dolor pellentesque nulla; consed nostie nullut
    modionsed adio numsandre.  Curae mattis nullute nostra laortieisse
    maecenas utateismodi niscidu dionse.  Quis erit corero rhoncus
    luptatum. Adio utat core suscin dis sum volor tionsenis augue.
    Incipis rcilis auguero dolorpe veriusto eum ut.  Utat incipis vent
    faciliquis odolorperos placerat etiam inceptos acipit interdum
    suscil.""")


class RecordingBodyProducerTestCase(TestCase):
    @inlineCallbacks
    def test_proxy_filebodyproducer(self):
        original = FileBodyProducer(BytesIO(LOREM_IPSUM))
        proxy = RecordingBodyProducer(original)
        self.assertEqual(original.length, proxy.length)
        transport = AbortableStringTransport()
        yield proxy.startProducing(transport)
        self.assertEqual(transport.value(), LOREM_IPSUM)
        self.assertEqual(proxy.value(), LOREM_IPSUM)


class RecordingReadBodyProtocolTestCase(TestCase):
    @inlineCallbacks
    def test_proxy_readbodyprotocol(self):
        original = Response(('HTTP', 1, 1), 200, 'OK', Headers(),
                            AbortableStringTransport())
        original._bodyDataReceived(LOREM_IPSUM)
        original._bodyDataFinished()
        proxy = RecordingResponse(original)
        body = yield readBody(proxy)
        self.assertEqual(body, LOREM_IPSUM)
        self.assertEqual(proxy.value(), LOREM_IPSUM)
