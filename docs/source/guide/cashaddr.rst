.. _cashaddr:

CashAddr
========

CashAddr is a new Bitcoin Cash `address format`_. It is an encoding of the
address in base32 format using `BCH codes`_ as checksum, that can be used
directly in links or QR codes.

BitCash uses CashAddr encoded addresses throughout the library for sending,
receiving :ref:`transactions <outputsparam>`. A CashAddr is handled through
:class:`~bitcash.cashaddress.Address`:

.. code-block:: python

   >>> from bitcash.cashaddress import Address
   >>> cashaddr = Address.from_string("bitcoincash:qqrxvhnn88gmpczyxry254vcsnl6canmkqgt98lpn5")
   >>> cashaddr
   Address('bitcoincash:qqrxvhnn88gmpczyxry254vcsnl6canmkqgt98lpn5')
   >>> cashaddr_test = Address.from_string("bchtest:qqrxvhnn88gmpczyxry254vcsnl6canmkqvepqak5g")
   >>> cashaddr_test
   Address('bchtest:qqrxvhnn88gmpczyxry254vcsnl6canmkqvepqak5g')
   >>> cashaddr.payload == cashaddr_test.payload
   True
   >>> cashaddr = Address.from_string("bitcoincash:qqrxvhnn88gmpczyxry254vcsnl6canmkqgt98lpn6")
   InvalidAddress: Bad cash address checksum for address bitcoincash:qqrxvhnn88gmpczyxry254vcsnl6canmkqgt98lpn6

The CashAddr can distinguish between networks of BCH of the same address, and 
perform checksum tests for bad addresses.


URI Scheme
----------

CashAddr follows `URI format`_ as described in `BIP0021`_. The query parameters 
of the URI can be used to pass additional information to the wallet, like BCH amount,
message, etc::

    bitcoincash:<address>[?amount=<amount>][?label=<label>][?message=<message>]


The parsing and generating of CashAddr URI is handled by :func:`~bitcash.cashaddress.parse_cashaddress`
and :func:`~bitcash.cashaddress.generate_cashaddress`:

.. code-block:: python

   >> from bitcash.cashaddress import generate_cashaddress, parse_cashaddress
   >> cashaddr_uri = generate_cashaddress(
          'bitcoincash:qqrxvhnn88gmpczyxry254vcsnl6canmkqgt98lpn5',
          {"amount": 0.1, "message": "Satoshi Nakamoto"}
      )
   >> cashaddr_uri
   'bitcoincash:qqrxvhnn88gmpczyxry254vcsnl6canmkqgt98lpn5?amount=0.1&message=Satoshi+Nakamoto'
   >> parse_cashaddress(cashaddr_uri)
   (Address('bitcoincash:qqrxvhnn88gmpczyxry254vcsnl6canmkqgt98lpn5'),
    {'amount': '0.1', 'message': 'Satoshi Nakamoto'})

As described in the `spec <BIP0021>`_, the amount is considered in BCH. Further
variables can be added to query. The ones which are prefixed with a req- are
considered required. If a client does not implement any variables which are
prefixed with req-, it must consider the entire URI invalid. Any other
variables which are not implemented, but which are not prefixed with a req-,
can be safely ignored.


.. _address format: https://github.com/bitcoincashorg/bitcoincash.org/blob/master/spec/cashaddr.md
.. _BCH codes: https://en.wikipedia.org/wiki/BCH_code
.. _URI format: https://en.wikipedia.org/wiki/Uniform_Resource_Identifier
.. _BIP0021: https://en.bitcoin.it/wiki/BIP_0021
