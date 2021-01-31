.. _fees:

Fees
====

BitCash provides a 1 satoshi/byte default fee.

Transactions will likely be confirmed in the next block.

If you want to set a custom fee, pass a `fee` parameter to `send()`:

.. code-block:: python

    >>> send(outputs, fee=2)
