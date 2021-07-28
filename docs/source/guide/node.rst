.. _node:

Customize your node API endpoints
=================================

You can use your own or a compatible node (currently, `bch toolkit`_ is supported and works out of the box) by setting the following environment variables::

    BITCOINCOM_API_MAINNET
    BITCOINCOM_API_TESTNET
    BITCOINCOM_API_REGTEST

For example::

    export BITCOINCOM_API_MAINNET=https://rest.bitcoin.com/v2/

You can also specify multiple endpoints for redundancy by setting the following environment variables::

    BITCOINCOM_API_MAINNET_1
    BITCOINCOM_API_MAINNET_2
    BITCOINCOM_API_MAINNET_3
    and so on...

This works with any supported network (mainnet, testnet and regtest).

Note that if, for example, `BITCOINCOM_API_MAINNET` is set, `BITCOINCOM_API_MAINNET_1` and so on will not be taken into account.

.. _bch toolkit: https://github.com/actorforth/bch-toolkit
