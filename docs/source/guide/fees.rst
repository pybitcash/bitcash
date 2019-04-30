.. _fees:

Fees
====

For now, bitcash provides a 2 satoshi/byte default fee.

Transactions will likely be confirmed in the next block.

.. code-block:: python

    >>> from bitcash.network import get_fee
    >>>
    >>> get_fee()
    2
