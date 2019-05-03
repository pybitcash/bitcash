bitcash: Bitcoin Cash for Python
================================

Version |version|.

.. image:: https://img.shields.io/pypi/v/bitcash.svg?style=flat-square
    :target: https://pypi.org/project/bitcash

.. image:: https://img.shields.io/pypi/pyversions/bitcash.svg?style=flat-square
    :target: https://pypi.org/project/bitcash

.. image:: https://travis-ci.org/sporestack/bitcash.svg?branch=master
    :target: https://travis-ci.org/sporestack/bitcash

.. image:: https://img.shields.io/codecov/c/github/sporestack/bitcash.svg?style=flat-square

.. image:: https://img.shields.io/badge/license-MIT-blue.svg?style=flat-square
    :target: https://en.wikipedia.org/wiki/MIT_License

-----

BitCash is Python's `fastest <guide/intro.html#why-bitcash>`_
Bitcoin Cash library and was designed from the beginning to feel intuitive, be
effortless to use, and have readable source code. It is heavily inspired by
`Requests <https://github.com/kennethreitz/requests>`_ and
`Keras <https://github.com/fchollet/keras>`_.

**bitcash is so easy to use, in fact, you can do this:**

.. code-block:: python

    >>> from bitcash import Key
    >>>
    >>> k = Key()
    >>> k.address
    'bitcoincash:qp0hamw9rpyllkmvd8047w9em3yt9fytsunyhutucx'
    >>>
    >>> k.get_balance('usd')
    '2'
    >>>
    >>> # Let's donate a dollar to CoinSpice.io
    >>> outputs = [
    >>>     ('bitcoincash:qz69e5y8yrtujhsyht7q9xq5zhu4mrklmv0ap7tq5f', 1, 'usd'),
    >>>     # you can add more recipients here
    >>> ]
    >>>
    >>> k.send(outputs)
    '6aea7b1c687d976644a430a87e34c93a8a7fd52d77c30e9cc247fc8228b749ff'

Here is the transaction `<https://explorer.bitcoin.com/bch/tx/6aea7b1c687d976644a430a87e34c93a8a7fd52d77c30e9cc247fc8228b749ff>`_.

Features
--------

- Python's fastest available implementation (100x faster than closest library)
- Seamless integration with existing server setups
- Supports keys in cold storage
- Fully supports 25 different currencies
- First class support for storing data in the blockchain
- Deterministic signatures via RFC 6979
- Access to the blockchain through multiple APIs for redundancy
- Exchange rate API, with optional caching
- Compressed public keys by default
- Multiple representations of private keys; WIF, PEM, DER, etc.
- Standard P2PKH transactions

If you are intrigued, continue reading. If not, continue all the same!

User Guide
----------

This section will tell you a little about the project, show how to install it,
and will then walk you through how to use bitcash with many examples and explanations
of best practices.

.. toctree::
    :maxdepth: 2

    guide/intro
    guide/install
    guide/keys
    guide/network
    guide/transactions
    guide/rates
    guide/fees
    guide/advanced

Community
---------

Here you will find everything you need to know about the development of bitcash
and the community surrounding it.

.. toctree::
    :maxdepth: 1

    community/faq
    community/support
    community/development
    community/contributing
    community/vulnerabilities
    community/updates
    community/authors

Dev Guide
---------

Up ahead is bitcash's API and a few notes about design decisions. Beware the
pedantry, or lack thereof.

.. toctree::
    :maxdepth: 2

    dev/api
