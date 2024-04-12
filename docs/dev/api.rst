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

CashAddress
-----------

.. autoclass:: bitcash.cashaddress.Address
   :members:

.. autofunction:: bitcash.cashaddress.generate_cashaddress
.. autofunction:: bitcash.cashaddress.parse_cashaddress

CashTokens
-----------

.. autofunction:: bitcash.cashtoken.verify_cashtoken_output_data
.. autofunction:: bitcash.cashtoken.parse_cashtoken_prefix
.. autofunction:: bitcash.cashtoken.generate_cashtoken_prefix
.. autofunction:: bitcash.format.cashtokenaddress_to_address

Network
-------

.. autoclass:: bitcash.network.NetworkAPI
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

Utilities
---------

.. autofunction:: bitcash.verify_sig

Exceptions
----------

.. autoexception:: bitcash.exceptions.InsufficientFunds
