.. _cashtokens:

CashTokens
==========

CashTokens enable `token primitives`_ for BCH. A token is an asset – distinct from 
the Bitcoin Cash currency – that can be created and transferred on the Bitcoin Cash
network. CashTokens come in two flavours:

   #. **Non-Fungible tokens (NFTs)** are a token type in which individual units 
         cannot be merged or divided – each NFT contains a ``commitment``, a short
         byte string attested to by the issuer of the NFT.
   #. **Fungible tokens** are a token type in which individual units are 
         undifferentiated – groups of fungible tokens can be freely divided and merged
         without tracking the identity of individual tokens (much like the Bitcoin
         Cash currency).

Moreover, an NFT token can have 3 ``capabilities``:
   #. **Minting tokens** (NFTs with the "minting" ``capability``) allow the spending
         transaction to create any number of new NFTs of the same ``category``, each
         with any ``commitment`` and (optionally) the *minting* or *mutable* ``capability``.
   #. **Mutable tokens** (NFTs with the "mutable" ``capability``) allow the spending
         transaction to create one NFT of the same ``category``, with any
         ``commitment`` and (optionally) the *mutable* ``capability``.
   #. **Immutable tokens** (NFTs with "none" ``capability``) cannot have their
         ``commitment`` modified when spent.

The cashtokens are attached to BCH :ref:`Unspents <unspent>`. A single unspent can
have tokens of a single ``category``, which can include one of or both of fungible
tokens and an NFT.

.. _token primitives: https://github.com/cashtokens/cashtokens/blob/master/readme.md

CashToken genesis
------------------

To create cashtokens, an :ref:`unspent <unspent>` is required with output index 0 that
acts as a genesis unspent. This genesis unspent can be spent to create the cashtoken
required. This cashtoken then gets the transaction id of the genesis output as its
``category``.

.. figure:: /_static/cashtoken-creation.svg

  Two new token ``categories`` are created by transaction ``c3a601...`` The first ``category`` (``■ b201a0...``) is created by spending the 0th output of transaction ``b201a0...``; for this ``category``, a supply of 150 fungible tokens are created across two outputs (100 and 50). The second ``category`` (``▲ a1efcd...``) is created by spending the 0th output of transaction ``a1efcd...``; for this ``category``, a supply of 100 fungible tokens are created across two outputs (20 and 80), and two NFTs are created (each with a ``commitment`` of ``0x010203``).

Using the :func:`~bitcash.PrivateKey.get_unspents` you can query the unspent set
belonging to your address:

.. code-block:: python

    >>> key = Key(...)
    >>> key.get_unspents()
    [Unspent(amount=900000, confirmations=1, script='76a914dd9c917762a9f585a40e5c3a54238684d8cc741e88ac', txid='afe979e6b52e37d29f6c4d7edd922bddb91b5e4d55ebfa8cd59a0f90bc03b802', txindex=0)]

In the above example, the unspent output has an output index 0, which implies it can be
a cashtoken genesis unspent. The cashtoken generated with this unspent will have a 
``category`` of ``afe979...``. To generate a cashtoken with an NFT of "minting" 
``capability``, and 10000 fungible tokens we can use an extended :ref:`output format <outputsparam>`
which is a tuple of size 7 in the form `(destination, amount, currency, category_id, 
nft_capability, nft_commitment, token_amount)`. This can be sent as:

.. code-block:: python

   >>> key.send([
   ...     (
   ...         "bitcoincash:zrweeythv25ltpdypewr54prs6zd3nr5rcjhrnhy2v",  # destination
   ...         1000,  # amount
   ...         "satoshi",  # currency
   ...         "afe979e6b52e37d29f6c4d7edd922bddb91b5e4d55ebfa8cd59a0f90bc03b802",  # category
   ...         "minting",  # NFT capability
   ...         None,  # NFT commitment, None
   ...         10000  # fungible token amount
   ...     )
   ... ])
   '311e30abebb9d6b35d3d02308bec3985988aa0ef997bffa7bca821fe6094f17f'
   >>> key.get_balance()  # to fetch present balance from the network
   '899737'
   >>> key.cashtoken_balance
   {'afe979e6b52e37d29f6c4d7edd922bddb91b5e4d55ebfa8cd59a0f90bc03b802': {'token_amount': 10000, 'nft': [{'capability': 'minting'}]}}

CashToken spending
------------------

Much like generating new cashtokens, cashtokens can be spent as well. For example, to 
send 6000 fungible tokens of ``category`` ``afe979...`` you can use:

.. code-block:: python

   >>> key.send([
   ...     (
   ...         "bitcoincash:zrweeythv25ltpdypewr54prs6zd3nr5rcjhrnhy2v",
   ...         1000,
   ...         "satoshi",
   ...         "afe979e6b52e37d29f6c4d7edd922bddb91b5e4d55ebfa8cd59a0f90bc03b802",
   ...         None,
   ...         None,
   ...         6000
   ...     )
   ... ])
   'fec7bff45086ac961e8f2289a9f280f7710144979a61b0a11121f674fed85b15'

BitCash automatically handles unspents to form the desired transaction outputs with 
the leftover BCH and cashtokens management.

We can further use the "minting" ``capability`` of NFT to mint a cashtoken of "mutable"
``capability`` with a ``commitment`` of ``b"bitcash"`` as:

.. code-block:: python

   >>> key.send(
   ...     [
   ...     (
   ...         "bitcoincash:zrweeythv25ltpdypewr54prs6zd3nr5rcjhrnhy2v",
   ...         1000,
   ...         "satoshi",
   ...         "afe979e6b52e37d29f6c4d7edd922bddb91b5e4d55ebfa8cd59a0f90bc03b802",
   ...         "mutable",
   ...         b"bitcash",
   ...         None
   ...     )
   ... ])
   '58292afb507d881e6564f4210e24d2008c7b7d9028e365811cdf7304080ecb08'
   >>> key.get_balance()
   '898388'
   >>> key.cashtoken_balance
   {'afe979e6b52e37d29f6c4d7edd922bddb91b5e4d55ebfa8cd59a0f90bc03b802': {'nft': [{'capability': 'mutable', 'commitment': b'bitcash'}, {'capability': 'minting'}], 'token_amount': 10000}}


CashToken spending order
^^^^^^^^^^^^^^^^^^^^^^^^

When spending unspents, BitCash follows a certain order:

   #. When choosing unspents to add BCH to fulfill BCH in outputs, BitCash 
         prioritises adding unspents with no cashtokens. It then chooses unspents
         with just fungible tokens, followed by unspents with NFT. The unspents
         with "none" ``capability`` are chosen first, then followed by "mutable"
         ``capability``, and finally "minting" ``capability``.
   #. When an NFT with "none" ``capability`` is to be sent, then a "none" ``capability``
         NFT with the same ``commitment`` is chosen. If none are found, then an NFT
         with "mutable" ``capability`` is chosen, whose ``commitment`` is mutated
         to match the ``commitment`` of the NFT and is made into the NFT with "none"
         ``capability``. If none are found, then an NFT with "minting" ``capability``
         is added to the transaction, to mint the required NFT. The "minting" 
         ``capability`` NFT is not consumed and is also present in a leftover output.
   #. When an NFT with "mutable" ``capability`` is to be sent, then a "mutable"
         ``capability`` NFT is chosen, whose ``commitment`` is mutated to match the
         ``commitment`` of the "mutable" ``capability`` NFT sent. If none are found,
         then an NFT with "minting" ``capability`` is added to the transaction, to
         mint the required NFT. The "minting" ``capability`` NFT is not consumed and
         is also present in a leftover output.
   #. When an NFT with "minting" ``capability`` is to be sent, then a "minting"
         ``capability`` NFT is chosen. The "minting" ``capability`` NFT is not consumed
         and is also present in a leftover output.

.. note::
   In all the cases where an NFT is to be sent, the NFT to be spent has to be of the same
   ``category``.

If the default behaviour is not suitable, then a curated unspent set can be specified,
which only includes cashtokens which need to be used.
   

CashToken signalling CashAddr
-----------------------------

To signal cashtoken support by wallets, new :ref:`cashaddr` versions are introduced. BitCash 
wallet can signal cashtoken support by sharing cashtoken address using 
:func:`~bitcash.PrivateKey.cashtoken_address`, and BitCash does not allow spending cashtokens to
non-cashtoken-signalling addresses:

.. code-block:: python

   >>> key.cashtoken_address
   'bitcoincash:zrweeythv25ltpdypewr54prs6zd3nr5rcjhrnhy2v'
