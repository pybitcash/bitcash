.. _node:

Customize your node API endpoints
=================================

You can use your own or a compatible node (currently, `bch toolkit`_, `FulcrumProtocol`_, and `ChainGraph`_ are supported and work out of the box) by setting the following environment variables::

    BITCOINCOM_API_MAINNET
    BITCOINCOM_API_TESTNET
    BITCOINCOM_API_REGTEST
    FULCRUM_API_MAINNET
    FULCRUM_API_TESTNET
    FULCRUM_API_REGTEST
    CHAINGRAPH_API
    CHAINGRAPH_API_MAINNET
    CHAINGRAPH_API_TESTNET
    CHAINGRAPH_API_REGTEST

For example, for BitcoinDotComAPI::

    export BITCOINCOM_API_MAINNET=https://rest.bitcoin.com/v2/

For Fulcrum Protocol API::

    export FULCRUM_API_MAINNET=electron.jochen-hoenicke.de:51002

The port is a necessary component for a Fulcrum Protocol uri. The Fulcrum protocol is connected directly via tcp, hence, avoid "http://" or "https://" prefix.

And for ChainGraph API::

    export CHAINGRAPH_API=https://demo.chaingraph.cash/v1/graphql
    export CHAINGRAPH_API_MAINNET=%mainnet
    export CHAINGRAPH_API_TESTNET=%testnet

This is so implemented because a ChainGraph instance can be connected to multiple BCH nodes, even on different networks of mainnet, testnet, or regtest. These nodes can be differently queried by their node names with the node-like pattern given in the relevant environment variable. If the node-like pattern environment variable is missing, then the "%" pattern is used as default.

You can also specify multiple endpoints for redundancy by setting the following environment variables::

    BITCOINCOM_API_MAINNET_1
    BITCOINCOM_API_MAINNET_2
    BITCOINCOM_API_MAINNET_3
    and so on...
    or
    FULCRUM_API_MAINNET_1
    FULCRUM_API_MAINNET_2
    FULCRUM_API_MAINNET_3
    and so on...
    or
    CHAINGRAPH_API_1
    CHAINGRAPH_API_2
    CHAINGRAPH_API_MAINNET_1
    CHAINGRAPH_API_MAINNET_2
    CHAINGRAPH_API_TESTNET_2
    and so on...

This works with any supported network (mainnet, testnet and regtest).

.. note::
   If, for example, `BITCOINCOM_API_MAINNET` is set, `BITCOINCOM_API_MAINNET_1` and so on will not be taken into account.

.. _bch toolkit: https://github.com/actorforth/bch-toolkit
.. _ChainGraph: https://chaingraph.cash/
.. _FulcrumProtocol: https://electrum-cash-protocol.readthedocs.io/en/latest/index.html
