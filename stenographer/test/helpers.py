"""Test helpers."""


import os.path


def cassette_path(name):
    """Return the full path of a cassette file in our fixtures."""
    return os.path.join(os.path.dirname(__file__),
                        'fixtures', 'cassettes', name + '.json')
