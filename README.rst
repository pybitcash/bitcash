BitCash: BitcoinCash made easy.
=======================

NOTE about cashaddresses
========================

Breaking change in 0.5.0!

Bitcoin Cash has changed address formats (from 1........ to bitcoincash:qsomething). We now support the new format. As of 0.5.0, the new address format is used internally and the .address returned from PrivateKey has changed to the new format. This is unfortunate to make such a change, but the work would have been far greater to have legacy addresses returned. PrivateKey.send() supports both legacy and cashaddresses.

If you have not done so already, *please pin your bitcash version*. Like, bitcash==0.5.0 in your setup.py. This way breaking changes won't break your application.

Some point after, legacy address support may be removed entirely. So please convert addresses to the new format before sending them on to BitCash: https://github.com/oskyk/cashaddress/

.. image:: https://img.shields.io/pypi/v/bitcash.svg?style=flat-square
    :target: https://pypi.org/project/bitcash

.. image:: https://img.shields.io/travis/sporestack/bitcash.svg?branch=master&style=flat-square
    :target: https://travis-ci.org/sporestack/bitcash

.. image:: https://img.shields.io/codecov/c/github/sporestack/bitcash.svg?style=flat-square
    :target: https://codecov.io/gh/sporestack/bitcash

.. image:: https://img.shields.io/pypi/pyversions/bitcash.svg?style=flat-square
    :target: https://pypi.org/project/bitcash

.. image:: https://img.shields.io/badge/license-MIT-blue.svg?style=flat-square
    :target: https://en.wikipedia.org/wiki/MIT_License

-----

Forked from Ofek's awesome Bit library: https://github.com/ofek/bit

Despite what it looks like, this is mostly a working library for Bitcoin Cash! Try to ignore the out of date bits on the README which referred to Bitcoin and not Bitcoin Cash.

What needs fixing
----------------

- This README.
- Dynamic fees.
- The test cases...
- Rates (so 'usd', 'jpy', etc work as they do in bit)

**BitCash is so easy to use, in fact, you can do this:**

.. code-block:: python

    >>> from bitcash import Key
    >>>
    >>> my_key = Key(...)
    >>> my_key.get_balance('usd')
    '12.51'
    >>>
    >>> # Let's donate!
    >>> outputs = [
    >>>     # Wikileaks
    >>>     ('1HB5XMLmzFVj8ALj6mfBsbifRoD4miY36v', 0.0035, 'bch'),
    >>>     # Internet Archive
    >>>     ('1Archive1n2C579dMsAu3iC6tWzuQJz8dN', 190, 'jpy'),
    >>>     # The Pirate Bay
    >>>     ('129TQVAroeehD9fZpzK51NdZGQT4TqifbG', 3, 'eur'),
    >>>     # xkcd
    >>>     ('14Tr4HaKkKuC1Lmpr2YMAuYVZRWqAdRTcr', 2.5, 'cad')
    >>> ]
    >>>
    >>> my_key.send(outputs)
    '9f59f5c6757ec46fdc7440acbeb3920e614c8d1d247ac174eb6781b832710c1c'

Here is the transaction `<https://blockchain.info/tx/9f59f5c6757ec46fdc7440acbeb3920e614c8d1d247ac174eb6781b832710c1c>`_.

Features
--------

- Python's fastest available implementation (100x faster than closest library)
- Seamless integration with existing server setups
- Supports keys in cold storage
- Fully supports 25 different currencies
- First class support for storing data in the blockchain
- Deterministic signatures via RFC 6979
- Access to the blockchain (and testnet chain) through multiple APIs for redundancy
- Exchange rate API, with optional caching
- Optimal transaction fee API, with optional caching
- Compressed public keys by default
- Multiple representations of private keys; WIF, PEM, DER, etc.
- Standard P2PKH transactions

If you are intrigued, continue reading. If not, continue all the same!

Installation
------------

BitCash is distributed on `PyPI`_ as a universal wheel and is available on Linux/macOS
and Windows and supports Python 3.5+ and PyPy3.5-v5.7.1+. ``pip`` >= 8.1.2 is required.

.. code-block:: bash

    $ pip install bitcash  # pip3 if pip is Python 2 on your system.

Documentation
-------------

Docs are hosted by Github Pages and are automatically built and published
by Travis after every successful commit to BitCash's ``master`` branch.

Credits
-------

- `ofek`_ for the original bit codebase.
- `bjarnemagnussen`_ for his segwit code for the necessary BIP-143 support.

.. _ofek: https://github.com/ofek/bit
.. _bjarnemagnussen: https://github.com/bjarnemagnussen/bitcash/tree/segwit
