Stenographer
============

An HTTP interaction recorder for Twisted Web.
It aims to be compatible with the cassette format used by the `VCR`__
library for Ruby and ports like `Betamax`__ for Python, but with an API
based on Twisted Web Agents.

__ https://relishapp.com/vcr/vcr
__ https://betamax.readthedocs.org/

**Stenographer is not production-ready software.**
It's currently composed mostly of bits hacked out of `Omnipresence`__'s
test helpers, is nowhere near feature parity with VCR, and ironically
doesn't have a comprehensive test suite.
Improvements are welcome.

__ https://github.com/kxz/omnipresence

Basic usage, in case the warning above wasn't scary enough::

    from stenographer import CassetteAgent
    from twisted.internet import reactor
    from twisted.web.client import Agent, RedirectAgent

    # Use CassetteAgent to wrap the innermost agent object.  In most
    # cases, this will be the basic Agent in twisted.web.client.
    cassette_agent = CassetteAgent(Agent(reactor), 'cassette_path.json')
    agent = RedirectAgent(cassette_agent)
    deferred = agent.request('GET', 'http://www.example.com/')
    # Don't forget to add a save callback to the response Deferred.
    deferred.addCallback(cassette_agent.save)
