.. _cli:

Command-Line Interface
======================

BitCash ships with a command-line interface for common operations.
Install the optional CLI dependencies to enable it:

.. code-block:: bash

    pip install 'bitcash[cli]'

All commands are available under the ``bitcash`` entry point:

.. code-block:: bash

    bitcash --help

----

Stateless Commands
------------------

These commands require no stored wallet and make no writes to disk.

new
^^^

Generate a fresh private key and print its WIF and address.

.. code-block:: bash

    bitcash new [--network main|test|regtest]

Example:

.. code-block:: bash

    $ bitcash new
    WIF:     L4vB5fomsK8L95wQ7GFzvErYGht8aN9KV5CLDnXBFwGLCbcBHEFJ
    Address: bitcoincash:qp0hamw9rpyllkmvd8047w9em3yt9fytsunyhutucx

gen
^^^

Generate a vanity address whose address starts with the given prefix.

.. code-block:: bash

    bitcash gen <prefix> [--cores N|all]

Example:

.. code-block:: bash

    $ bitcash gen q1
    ...

cashtoken-address
^^^^^^^^^^^^^^^^^

Convert any address to its CashToken-signalling form (``bitcoincash:zz...``).

.. code-block:: bash

    bitcash cashtoken-address <address>

Example:

.. code-block:: bash

    $ bitcash cashtoken-address bitcoincash:qp0hamw9rpyllkmvd8047w9em3yt9fytsunyhutucx
    bitcoincash:zp0hamw9rpyllkmvd8047w9em3yt9fytsuu5wac7aq

balance
^^^^^^^

Fetch the current balance of any address. Pass ``--cashtoken`` to also show
CashToken holdings (fungible amounts and NFTs) alongside the BCH balance.

.. code-block:: bash

    bitcash balance <address> [--currency satoshi] [--cashtoken] [--network main|test|regtest]

Example:

.. code-block:: bash

    $ bitcash balance bitcoincash:qp0hamw9rpyllkmvd8047w9em3yt9fytsunyhutucx
    493200 satoshi

    $ bitcash balance bitcoincash:qp0hamw9rpyllkmvd8047w9em3yt9fytsunyhutucx --currency usd
    2 USD

    $ bitcash balance bitcoincash:qp0hamw9rpyllkmvd8047w9em3yt9fytsunyhutucx --cashtoken
    493200 satoshi
    Category: aabbcc0011223344556677889900aabbcc0011223344556677889900aabbcc00
      Fungible amount: 1000
      NFTs (1):
        capability=minting  commitment(hex)=666f6f626172

transactions
^^^^^^^^^^^^

List all transaction IDs for an address.

.. code-block:: bash

    bitcash transactions <address> [--network main|test|regtest]

Example:

.. code-block:: bash

    $ bitcash transactions bitcoincash:qp0hamw9rpyllkmvd8047w9em3yt9fytsunyhutucx
    6aea7b1c687d976644a430a87e34c93a8a7fd52d77c30e9cc247fc8228b749ff
    fcb45fbe67ae685ac03a1d4ab25b644d57ddaca2e5f4e65ca500c8c4ccea9070
    ...

unspents
^^^^^^^^

List all unspent transaction outputs (UTXOs) for an address.

.. code-block:: bash

    bitcash unspents <address> [--network main|test|regtest]

Example:

.. code-block:: bash

    $ bitcash unspents bitcoincash:qp0hamw9rpyllkmvd8047w9em3yt9fytsunyhutucx
    Unspent(amount=172294, confirmations=2244, ...)

send
^^^^

Broadcast a transaction using a raw WIF key (no wallet store required).
CashToken options are optional — omit them for a plain BCH transfer.

.. code-block:: bash

    bitcash send --wif <WIF> <to> <amount> <currency> \
        [--fee N] [--message TEXT] \
        [--category-id HEX] [--nft-capability none|mutable|minting] \
        [--nft-commitment HEX] [--token-amount N] \
        [--network main|test|regtest]

Examples:

.. code-block:: bash

    # Plain BCH transfer
    $ bitcash send --wif L4vB5fomsK8L... \
        bitcoincash:qz69e5y8yrtujhsyht7q9xq5zhu4mrklmv0ap7tq5f 1000 satoshi
    Transaction ID: 6aea7b1c687d976644a430a87e34c93a8a7fd52d77c30e9cc247fc8228b749ff

    # Send fungible tokens
    $ bitcash send --wif L4vB5fomsK8L... \
        bitcoincash:zz69e5y8yrtujhsyht7q9xq5zhu4mrklmvxxxxxxx 1000 satoshi \
        --category-id aabbcc00... --token-amount 50
    Transaction ID: 6aea7b1c...

    # Send an NFT with commitment
    $ bitcash send --wif L4vB5fomsK8L... \
        bitcoincash:zz69e5y8yrtujhsyht7q9xq5zhu4mrklmvxxxxxxx 1000 satoshi \
        --category-id aabbcc00... --nft-capability none --nft-commitment 666f6f626172
    Transaction ID: 6aea7b1c...

subscribe
^^^^^^^^^

Watch an address for real-time transaction activity. Blocks until
``Ctrl+C`` or the server sends an ``unsubscribed`` event.

Requires the ``subscriptions`` extra: ``pip install 'bitcash[subscriptions]'``.

.. code-block:: bash

    bitcash subscribe <address> [--show-balance] [--network main|test|regtest]

Example:

.. code-block:: bash

    $ bitcash subscribe bitcoincash:qp0hamw9rpyllkmvd8047w9em3yt9fytsunyhutucx --show-balance
    Subscribing to bitcoincash:qp0h... on main. Press Ctrl+C to stop.
    [10:23:45] bitcoincash:qp0h...  status=abc123def456…  balance=493200 sat

----

Wallet Commands
---------------

The ``wallet`` subgroup manages a local, password-protected wallet store
(backed by `TinyDB`_). Wallets are stored in the platform user-data directory
(e.g. ``~/.local/share/bitcash/wallets.json`` on Linux).

Requires the ``cli`` extra: ``pip install 'bitcash[cli]'``.

Passwords
^^^^^^^^^

Commands that need to decrypt the stored WIF accept the password in three ways,
in order of precedence:

1. ``--password <value>`` flag
2. ``BITCASH_WALLET_PASSWORD`` environment variable
3. Interactive prompt (fallback for human use)

The environment variable approach is recommended for scripting and AI agents:

.. code-block:: bash

    export BITCASH_WALLET_PASSWORD=mysecret
    bitcash wallet send mykey bitcoincash:qq... 1000 satoshi

wallet new
^^^^^^^^^^

Create a new wallet (generates a fresh key) or import an existing WIF.

.. code-block:: bash

    bitcash wallet new <name> [--wif WIF] [--network main|test|regtest] [--password PASSWORD]

Examples:

.. code-block:: bash

    # Generate a new key
    $ bitcash wallet new mykey
    Password: ••••••••
    Repeat for confirmation: ••••••••
    Wallet 'mykey' created.
    Address: bitcoincash:qq...

    # Import an existing WIF
    $ bitcash wallet new mykey --wif L4vB5fomsK8L...
    Password: ••••••••
    Wallet 'mykey' created.
    Address: bitcoincash:qp0hamw9rpyllkmvd8047w9em3yt9fytsunyhutucx

wallet list
^^^^^^^^^^^

List all stored wallets (no password required).

.. code-block:: bash

    bitcash wallet list

Example:

.. code-block:: bash

    $ bitcash wallet list
    mykey                 main      bitcoincash:qp0hamw9rpyllkmvd8047w9em3yt9fytsunyhutucx

wallet balance
^^^^^^^^^^^^^^

Fetch the balance of a stored wallet. No password required — the address
is public information. Pass ``--cashtoken`` to also show CashToken holdings.

.. code-block:: bash

    bitcash wallet balance <name> [--currency satoshi] [--cashtoken]

Example:

.. code-block:: bash

    $ bitcash wallet balance mykey
    493200 satoshi

    $ bitcash wallet balance mykey --cashtoken
    493200 satoshi
    Category: aabbcc0011223344556677889900aabbcc0011223344556677889900aabbcc00
      Fungible amount: 1000
      NFTs (1):
        capability=minting  commitment(hex)=666f6f626172

wallet subscribe
^^^^^^^^^^^^^^^^

Watch a stored wallet's address for real-time activity.

.. code-block:: bash

    bitcash wallet subscribe <name> [--show-balance]

wallet send
^^^^^^^^^^^

Send BCH (and optionally CashTokens) from a stored wallet.

.. code-block:: bash

    bitcash wallet send <name> <to> <amount> <currency> \
        [--fee N] [--message TEXT] \
        [--category-id HEX] [--nft-capability none|mutable|minting] \
        [--nft-commitment HEX] [--token-amount N] \
        [--password PASSWORD]

Example:

.. code-block:: bash

    $ bitcash wallet send mykey bitcoincash:qz69e5y8yrtujhsyht7q9xq5zhu4mrklmv0ap7tq5f 1000 satoshi --password mysecret
    Transaction ID: 6aea7b1c687d976644a430a87e34c93a8a7fd52d77c30e9cc247fc8228b749ff

    $ bitcash wallet send mykey bitcoincash:zz69e5y8yrtujhsyht7q9xq5zhu4mrklmvxxxxxxx 1000 satoshi \
        --category-id aabbcc00... --token-amount 50 --password mysecret
    Transaction ID: 6aea7b1c...

wallet export
^^^^^^^^^^^^^

Decrypt and print the WIF of a stored wallet.

.. code-block:: bash

    bitcash wallet export <name> [--password PASSWORD]

Example:

.. code-block:: bash

    $ bitcash wallet export mykey --password mysecret
    WIF: L4vB5fomsK8L95wQ7GFzvErYGht8aN9KV5CLDnXBFwGLCbcBHEFJ

wallet delete
^^^^^^^^^^^^^

Delete a stored wallet (asks for confirmation unless ``--yes`` is passed).

.. code-block:: bash

    bitcash wallet delete <name> [--yes]

Example:

.. code-block:: bash

    $ bitcash wallet delete mykey
    Are you sure you want to delete this wallet? [y/N]: y
    Wallet 'mykey' deleted.

.. _TinyDB: https://tinydb.readthedocs.io/
