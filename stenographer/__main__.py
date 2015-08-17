"""Command line entry points."""


import argparse
from itertools import imap
import sys

from twisted.internet import reactor
from twisted.internet.defer import DeferredList, inlineCallbacks
from twisted.web.client import (Agent, ContentDecoderAgent,
                                RedirectAgent, GzipDecoder, readBody)

from .agent import CassetteAgent


@inlineCallbacks
def save_and_exit(responses, cassette_agent):
    """Save the cassette and stop the reactor."""
    for success, response in responses:
        if success:
            yield readBody(response)
    cassette_agent.save()
    reactor.stop()


def fail_and_exit(failure):
    """Print a failure message and stop the reactor."""
    failure.printTraceback()
    reactor.stop()


def main():
    """Main command line entry point."""
    parser = argparse.ArgumentParser(
        description='Make requests to one or more HTTP or HTTPS URIs, '
                    'and record the interactions in a cassette.',
        epilog='If no URIs are passed on the command line, they are '
               'read from standard input, one per line.')
    parser.add_argument(
        'uris', metavar='URI', nargs='*', help='URI to fetch')
    parser.add_argument(
        'cassette_path', metavar='CASSETTE',
        help='path to output cassette')
    args = parser.parse_args()
    uris = args.uris or imap(lambda x: x.strip(), sys.stdin)
    cassette_agent = CassetteAgent(Agent(reactor), args.cassette_path)
    agent = ContentDecoderAgent(
        RedirectAgent(cassette_agent), [('gzip', GzipDecoder)])
    finished = DeferredList([agent.request('GET', uri) for uri in uris])
    finished.addCallback(save_and_exit, cassette_agent)
    finished.addErrback(fail_and_exit)
    reactor.run()


if __name__ == '__main__':
    main()
