<h3 align="center">BitCash</h3>
<h4 align="center">Bitcoin Cash made easy</h4>

<p align="center">
  <a href="https://pypi.org/project/bitcash" target="_blank">
    <img src="https://img.shields.io/pypi/v/bitcash.svg?style=flat-square" alt="BitCash PyPi version">
  </a>
  <img src="https://img.shields.io/travis/pybitcash/bitcash.svg?branch=master&style=flat-square" alt="Build status">
  <img src="https://codecov.io/gh/pybitcash/bitcash/branch/master/graph/badge.svg" alt="Code Coverage">
  <img src="https://img.shields.io/pypi/pyversions/bitcash.svg?style=flat-square" alt="Python Versions">
  <img src="https://img.shields.io/badge/license-MIT-blue.svg?style=flat-square" alt="MIT license">
</p>

Forked from [Ofek's awesome Bit library](https://github.com/ofek/bit).

**BitCash is so easy to use, in fact, you can do this:**


```python
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
```

Done. Here is the transaction:
https://explorer.bitcoin.com/bch/tx/6aea7b1c687d976644a430a87e34c93a8a7fd52d77c30e9cc247fc8228b749ff

## Features

- Python's fastest available implementation (100x faster than closest library)
- Seamless integration with existing server setups
- Supports keys in cold storage
- Fully supports 29 different currencies
- First class support for storing data in the blockchain
- Deterministic signatures via RFC 6979
- Access to the blockchain (and testnet chain) through multiple APIs for redundancy
- Exchange rate API, with optional caching
- Compressed public keys by default
- Multiple representations of private keys; WIF, PEM, DER, etc.
- Standard P2PKH transactions

If you are intrigued, continue reading. If not, continue all the same!

## Installation

BitCash is distributed on `PyPI` as a universal wheel and is available on Linux/macOS
and Windows and supports Python 3.5+ and PyPy3.5-v5.7.1+. `pip` >= 8.1.2 is required.


```shell
$ pip install bitcash  # pip3 if pip is Python 2 on your system.
```

## Documentation

Docs are hosted by Github Pages and are automatically built and published
by Travis after every successful commit to BitCash's ``master`` branch.

[Read the documentation](https://pybitcash.github.io/bitcash/)

## Credits

- [ofek](https://github.com/ofek/bit) for the original bit codebase.
- [Additional](AUTHORS.rst)
