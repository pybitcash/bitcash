.. _node:

Customize your node API endpoints
=================================

You can use your own or a compatible node (currently, `bch toolkit`_ is supported and works out of the box) by setting the following environment variables::

    BITCOINCOM_API_MAINNET
    BITCOINCOM_API_TESTNET
    BITCOINCOM_API_REGTEST

For example::

    export BITCOINCOM_API_MAINNET=https://rest.bitcoin.com/v2/

.. _bch toolkit: https://github.com/actorforth/bch-toolkit
