.. _api:

Developer Interface
===================

.. module:: bitcash

.. _keysapi:

Keys
----

.. autoclass:: bitcash.Key

.. autoclass:: bitcash.PrivateKey
    :members:
    :undoc-members:
    :inherited-members:

.. autoclass:: bitcash.PrivateKeyTestnet
    :members:
    :undoc-members:
    :inherited-members:

.. autoclass:: bitcash.wallet.BaseKey
    :members:
    :undoc-members:

Network
-------

.. autoclass:: bitcash.network.NetworkAPI
    :members:
    :undoc-members:

.. autoclass:: bitcash.network.services.BitpayAPI
    :members:
    :undoc-members:
    :inherited-members:

.. autoclass:: bitcash.network.services.BlockchainAPI
    :members:
    :undoc-members:

.. autoclass:: bitcash.network.services.SmartbitcashAPI
    :members:
    :undoc-members:

.. autoclass:: bitcash.network.meta.Unspent
    :members:
    :undoc-members:

Exchange Rates
--------------

.. autofunction:: bitcash.network.currency_to_satoshi
.. autofunction:: bitcash.network.currency_to_satoshi_cached
.. autofunction:: bitcash.network.satoshi_to_currency
.. autofunction:: bitcash.network.satoshi_to_currency_cached

.. autoclass:: bitcash.network.rates.RatesAPI
    :members:
    :undoc-members:

.. autoclass:: bitcash.network.rates.BitpayRates
    :members:
    :undoc-members:

.. autoclass:: bitcash.network.rates.BlockchainRates
    :members:
    :undoc-members:

Fees
----

.. autofunction:: bitcash.network.get_fee
.. autofunction:: bitcash.network.get_fee_cached

Utilities
---------

.. autofunction:: bitcash.verify_sig

Exceptions
----------

.. autoexception:: bitcash.exceptions.InsufficientFunds
