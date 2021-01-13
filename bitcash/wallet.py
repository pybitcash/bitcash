import json
import time
import bitcash.slp_create as slp_create

from bitcash.crypto import ECPrivateKey
from bitcash.curve import Point
from bitcash.exceptions import InvalidNetwork
from bitcash.format import (
    bytes_to_wif,
    public_key_to_address,
    public_key_to_coords,
    wif_to_bytes,
    address_to_public_key_hash,
)
from bitcash.network import NetworkAPI, get_fee, satoshi_to_currency_cached
from bitcash.network.slp_services import SlpAPI
from bitcash.network.meta import Unspent
from bitcash.transaction import (
    calc_txid,
    create_p2pkh_transaction,
    sanitize_tx_data,
    sanitize_slp_tx_data,
    sanitize_slp_create_tx_data,
    OP_CHECKSIG,
    OP_DUP,
    OP_EQUALVERIFY,
    OP_HASH160,
    OP_PUSH_20,
)
from bitcash.tx import Transaction

NETWORKS = {"main": "mainnet", "test": "testnet", "regtest": "regtest"}
NFT_DELAY = 3


def wif_to_key(wif, regtest=False):
    private_key_bytes, compressed, version = wif_to_bytes(wif, regtest)

    if version == "main":
        if compressed:
            return PrivateKey.from_bytes(private_key_bytes)
        else:
            return PrivateKey(wif)
    elif version == "test":
        if compressed:
            return PrivateKeyTestnet.from_bytes(private_key_bytes)
        else:
            return PrivateKeyTestnet(wif)
    else:  # Regtest
        if compressed:
            return PrivateKeyRegtest.from_bytes(private_key_bytes)
        else:
            return PrivateKeyRegtest(wif)


class BaseKey:
    """This class represents a point on the elliptic curve secp256k1 and
    provides all necessary cryptographic functionality. You shouldn't use
    this class directly.

    :param wif: A private key serialized to the Wallet Import Format. If the
                argument is not supplied, a new private key will be created.
                The WIF compression flag will be adhered to, but the version
                byte is disregarded. Compression will be used by all new keys.
    :type wif: ``str``
    :raises TypeError: If ``wif`` is not a ``str``.
    """

    def __init__(self, wif=None, regtest=False):
        if wif:
            if isinstance(wif, str):
                private_key_bytes, compressed, version = wif_to_bytes(wif, regtest)
                self._pk = ECPrivateKey(private_key_bytes)
            elif isinstance(wif, ECPrivateKey):
                self._pk = wif
                compressed = True
            else:
                raise TypeError("Wallet Import Format must be a string.")
        else:
            self._pk = ECPrivateKey()
            compressed = True

        self._public_point = None
        self._public_key = self._pk.public_key.format(compressed=compressed)

    @property
    def public_key(self):
        """The public point serialized to bytes."""
        return self._public_key

    @property
    def public_point(self):
        """The public point (x, y)."""
        if self._public_point is None:
            self._public_point = Point(*public_key_to_coords(self._public_key))
        return self._public_point

    def sign(self, data):
        """Signs some data which can be verified later by others using
        the public key.

        :param data: The message to sign.
        :type data: ``bytes``
        :returns: A signature compliant with BIP-62.
        :rtype: ``bytes``
        """
        return self._pk.sign(data)

    def verify(self, signature, data):
        """Verifies some data was signed by this private key.

        :param signature: The signature to verify.
        :type signature: ``bytes``
        :param data: The data that was supposedly signed.
        :type data: ``bytes``
        :rtype: ``bool``
        """
        return self._pk.public_key.verify(signature, data)

    def to_hex(self):
        """:rtype: ``str``"""
        return self._pk.to_hex()

    def to_bytes(self):
        """:rtype: ``bytes``"""
        return self._pk.secret

    def to_der(self):
        """:rtype: ``bytes``"""
        return self._pk.to_der()

    def to_pem(self):
        """:rtype: ``bytes``"""
        return self._pk.to_pem()

    def to_int(self):
        """:rtype: ``int``"""
        return self._pk.to_int()

    def is_compressed(self):
        """Returns whether or not this private key corresponds to a compressed
        public key.

        :rtype: ``bool``
        """
        return True if len(self.public_key) == 33 else False

    def __eq__(self, other):
        return self.to_int() == other.to_int()


class PrivateKey(BaseKey):
    """This class represents a BitcoinCash private key. ``Key`` is an alias.

    :param wif: A private key serialized to the Wallet Import Format. If the
                argument is not supplied, a new private key will be created.
                The WIF compression flag will be adhered to, but the version
                byte is disregarded. Compression will be used by all new keys.
    :type wif: ``str``
    :raises TypeError: If ``wif`` is not a ``str``.
    """

    def __init__(self, wif=None, network="main"):
        super().__init__(wif=wif)

        self._address = None
        self._slp_address = None
        self._scriptcode = None
        if network in NETWORKS.keys():
            self._network = network
        else:
            raise InvalidNetwork
        self.balance = 0
        self.slp_balance = []
        self.unspents = []
        self.slp_unspents = []
        self.batons = []
        self.transactions = []

    def __assign_address(self):
        self._address = public_key_to_address(self._public_key, version=self._network)
        self._slp_address = public_key_to_address(
            self._public_key, version=f"{self._network}-slp"
        )

    @property
    def address(self):
        """The public address you share with others to receive funds."""
        if self._address is None:
            self.__assign_address()

        return self._address

    @property
    def slp_address(self):
        """The public address you share with others to receive funds."""
        if self._address is None:
            self.__assign_address()

        return self._slp_address

    @property
    def scriptcode(self):
        self._scriptcode = (
            OP_DUP
            + OP_HASH160
            + OP_PUSH_20
            + address_to_public_key_hash(self.address)
            + OP_EQUALVERIFY
            + OP_CHECKSIG
        )
        return self._scriptcode

    def to_wif(self):
        return bytes_to_wif(
            self._pk.secret, version=self._network, compressed=self.is_compressed()
        )

    def balance_as(self, currency):
        """Returns your balance as a formatted string in a particular currency.

        :param currency: One of the :ref:`supported currencies`.
        :type currency: ``str``
        :rtype: ``str``
        """
        return satoshi_to_currency_cached(self.balance, currency)

    def get_balance(self, currency="satoshi"):
        """Fetches the current balance by calling
        :func:`~bitcash.PrivateKey.get_balance` and returns it using
        :func:`~bitcash.PrivateKey.balance_as`.

        :param currency: One of the :ref:`supported currencies`.
        :type currency: ``str``
        :rtype: ``str``
        """
        self.unspents[:] = NetworkAPI.get_unspent(
            self.address, network=NETWORKS[self._network]
        )
        filtered_unspents = SlpAPI.filter_slp_txid(
            self.address,
            self.slp_address,
            self.unspents,
            network=NETWORKS[self._network],
        )
        self.unspents = filtered_unspents["difference"]
        self.slp_unspents = filtered_unspents["slp_utxos"]
        self.batons = filtered_unspents["baton"]
        self.balance = sum(unspent.amount for unspent in self.unspents)
        return self.balance_as(currency)

    def get_slp_balance(self, tokenId=None):
        """Fetches the current balance by calling
        :func:`~bitcash.PrivateKey.get_balance` and returns it using
        :func:`~bitcash.PrivateKey.balance_as`.
        :param currency: One of the :ref:`supported currencies`.
        :type currency: ``str``
        :rtype: ``str``
        """
        if tokenId:
            self.slp_balance = SlpAPI.get_balance(
                self.slp_address, tokenId=tokenId, network=NETWORKS[self._network]
            )
            return self.slp_balance

        self.slp_balance = SlpAPI.get_balance_address(
            self.slp_address, network=NETWORKS[self._network]
        )
        return self.slp_balance

    def get_unspents(self):
        """Fetches all available unspent transaction outputs.

        :rtype: ``list`` of :class:`~bitcash.network.meta.Unspent`
        """
        self.unspents[:] = NetworkAPI.get_unspent(
            self.address, network=NETWORKS[self._network]
        )

        # Remove SLP unspents

        self.balance = sum(unspent.amount for unspent in self.unspents)
        return self.unspents

    def get_transactions(self):
        """Fetches transaction history.

        :rtype: ``list`` of ``str`` transaction IDs
        """
        self.transactions[:] = NetworkAPI.get_transactions(
            self.address, network=NETWORKS[self._network]
        )
        return self.transactions

    def create_transaction(
        self,
        outputs,
        fee=None,
        leftover=None,
        combine=True,
        message=None,
        unspents=None,
        custom_pushdata=False,
    ):  # pragma: no cover
        """Creates a signed P2PKH transaction.

        :param outputs: A sequence of outputs you wish to send in the form
                        ``(destination, amount, currency)``. The amount can
                        be either an int, float, or string as long as it is
                        a valid input to ``decimal.Decimal``. The currency
                        must be :ref:`supported <supported currencies>`.
        :type outputs: ``list`` of ``tuple``
        :param fee: The number of satoshi per byte to pay to miners. By default
                    Bitcash will poll `<https://bitcoincashfees.earn.com>`_ and use a fee
                    that will allow your transaction to be confirmed as soon as
                    possible.
        :type fee: ``int``
        :param leftover: The destination that will receive any change from the
                         transaction. By default Bitcash will send any change to
                         the same address you sent from.
        :type leftover: ``str``
        :param combine: Whether or not Bitcash should use all available UTXOs to
                        make future transactions smaller and therefore reduce
                        fees. By default Bitcash will consolidate UTXOs.
        :type combine: ``bool``
        :param message: A message to include in the transaction. This will be
                        stored in the blockchain forever. Due to size limits,
                        each message will be stored in chunks of 220 bytes.
        :type message: ``str``
        :param unspents: The UTXOs to use as the inputs. By default Bitcash will
                         communicate with the blockchain itself.
        :type unspents: ``list`` of :class:`~bitcash.network.meta.Unspent`
        :returns: The signed transaction as hex.
        :rtype: ``str``
        """

        unspents, outputs = sanitize_tx_data(
            unspents or self.unspents,
            outputs,
            fee or get_fee(),
            leftover or self.address,
            combine=combine,
            message=message,
            compressed=self.is_compressed(),
            custom_pushdata=custom_pushdata,
        )

        return create_p2pkh_transaction(
            self, unspents, outputs, custom_pushdata=custom_pushdata
        )

    def create_slp_transaction(
        self,
        outputs,
        tokenId,
        fee=None,
        leftover=None,
        combine=True,
        combine_slp=True,
        message=None,
        unspents=None,
        slp_unspents=None,
        non_standard=False,
        custom_pushdata=False,
    ):  # pragma: no cover
        """Creates a signed P2PKH transaction.
        :param outputs: A sequence of outputs you wish to send in the form
                        ``(destination, amount, currency)``. The amount can
                        be either an int, float, or string as long as it is
                        a valid input to ``decimal.Decimal``. The currency
                        must be :ref:`supported <supported currencies>`.
        :type outputs: ``list`` of ``tuple``
        :param fee: The number of satoshi per byte to pay to miners. By default
                    Bitcash will poll `<https://bitcoincashfees.earn.com>`_ and use a fee
                    that will allow your transaction to be confirmed as soon as
                    possible.
        :type fee: ``int``
        :param leftover: The destination that will receive any change from the
                         transaction. By default Bitcash will send any change to
                         the same address you sent from.
        :type leftover: ``str``
        :param combine: Whether or not Bitcash should use all available UTXOs to
                        make future transactions smaller and therefore reduce
                        fees. By default Bitcash will consolidate UTXOs.
        :type combine: ``bool``
        :param message: A message to include in the transaction. This will be
                        stored in the blockchain forever. Due to size limits,
                        each message will be stored in chunks of 220 bytes.
        :type message: ``str``
        :param unspents: The UTXOs to use as the inputs. By default Bitcash will
                         communicate with the blockchain itself.
        :type unspents: ``list`` of :class:`~bitcash.network.meta.Unspent`
        :returns: The signed transaction as hex.
        :rtype: ``str``
        """

        unspents, outputs = sanitize_slp_tx_data(
            self.address,
            self.slp_address,
            unspents or self.unspents,
            slp_unspents or self.slp_unspents,
            outputs,
            tokenId,
            fee or get_fee(),
            leftover or self.address,
            network=NETWORKS[self._network],
            combine=combine,
            combine_slp=combine_slp,
            message=message,
            compressed=self.is_compressed(),
            custom_pushdata=custom_pushdata,
            non_standard=non_standard,
        )

        return create_p2pkh_transaction(self, unspents, outputs, custom_pushdata=custom_pushdata)

    def send(
        self,
        outputs,
        fee=None,
        leftover=None,
        combine=True,
        message=None,
        unspents=None,
    ):  # pragma: no cover
        """Creates a signed P2PKH transaction and attempts to broadcast it on
        the blockchain. This accepts the same arguments as
        :func:`~bitcash.PrivateKey.create_transaction`.

        :param outputs: A sequence of outputs you wish to send in the form
                        ``(destination, amount, currency)``. The amount can
                        be either an int, float, or string as long as it is
                        a valid input to ``decimal.Decimal``. The currency
                        must be :ref:`supported <supported currencies>`.
        :type outputs: ``list`` of ``tuple``
        :param fee: The number of satoshi per byte to pay to miners. By default
                    Bitcash will poll `<https://bitcoincashfees.earn.com>`_ and use a fee
                    that will allow your transaction to be confirmed as soon as
                    possible.
        :type fee: ``int``
        :param leftover: The destination that will receive any change from the
                         transaction. By default Bitcash will send any change to
                         the same address you sent from.
        :type leftover: ``str``
        :param combine: Whether or not Bitcash should use all available UTXOs to
                        make future transactions smaller and therefore reduce
                        fees. By default Bitcash will consolidate UTXOs.
        :type combine: ``bool``
        :param message: A message to include in the transaction. This will be
                        stored in the blockchain forever. Due to size limits,
                        each message will be stored in chunks of 220 bytes.
        :type message: ``str``
        :param unspents: The UTXOs to use as the inputs. By default Bitcash will
                         communicate with the blockchain itself.
        :type unspents: ``list`` of :class:`~bitcash.network.meta.Unspent`
        :returns: The transaction ID.
        :rtype: ``str``
        """

        # tx = Transaction.from_outputs(
        #     self.unspents,
        #     outputs,
        #     fees=fee,
        #     leftover=leftover,
        #     combine=combine,
        #     message=message,
        # )
        # tx_hex = tx.to_hex()

        tx_hex = self.create_transaction(
            outputs,
            fee=fee,
            leftover=leftover,
            combine=combine,
            message=message,
            unspents=unspents,
        )

        NetworkAPI.broadcast_tx(tx_hex, network=NETWORKS[self._network])

        return calc_txid(tx_hex)

    def send_slp(
        self,
        outputs,
        tokenId,
        fee=None,
        leftover=None,
        combine=True,
        combine_slp=True,
        message=None,
        unspents=None,
        slp_unspents=None,
        non_standard=False,
    ):  # pragma: no cover
        """Creates a signed P2PKH transaction and attempts to broadcast it on
        the blockchain. This accepts the same arguments as
        :func:`~bitcash.PrivateKey.create_transaction`.
        :param outputs: A sequence of outputs you wish to send in the form
                        ``(destination, amount, currency)``. The amount can
                        be either an int, float, or string as long as it is
                        a valid input to ``decimal.Decimal``. The currency
                        must be :ref:`supported <supported currencies>`.
        :type outputs: ``list`` of ``tuple``
        :param fee: The number of satoshi per byte to pay to miners. By default
                    Bitcash will poll `<https://bitcoincashfees.earn.com>`_ and use a fee
                    that will allow your transaction to be confirmed as soon as
                    possible.
        :type fee: ``int``
        :param leftover: The destination that will receive any change from the
                         transaction. By default Bitcash will send any change to
                         the same address you sent from.
        :type leftover: ``str``
        :param combine: Whether or not Bitcash should use all available UTXOs to
                        make future transactions smaller and therefore reduce
                        fees. By default Bitcash will consolidate UTXOs.
        :type combine: ``bool``
        :param message: A message to include in the transaction. This will be
                        stored in the blockchain forever. Due to size limits,
                        each message will be stored in chunks of 220 bytes.
        :type message: ``str``
        :param unspents: The UTXOs to use as the inputs. By default Bitcash will
                         communicate with the blockchain itself.
        :type unspents: ``list`` of :class:`~bitcash.network.meta.Unspent`
        :returns: The transaction ID.
        :rtype: ``str``
        """

        tx_hex = self.create_slp_transaction(
            outputs,
            tokenId,
            fee=fee,
            leftover=leftover,
            combine=combine,
            message=message,
            unspents=unspents,
            combine_slp=combine_slp,
            slp_unspents=slp_unspents,
            non_standard=non_standard,
            custom_pushdata=True,
        )

        NetworkAPI.broadcast_tx(tx_hex, network=NETWORKS[self._network])

        return calc_txid(tx_hex)

    def create_slp_token(
        self,
        ticker,
        token_name,
        document_url,
        document_hash,
        decimals,
        token_quantity,
        token_type=1,
        token_address=None,
        mint_baton_address=None,
        fee=None,
        leftover=None,
        combine=True,
        unspents=None,
        custom_pushdata=False,
    ):  # pragma: no cover
        """Creates a signed P2PKH transaction.
        :param outputs: A sequence of outputs you wish to send in the form
                        ``(destination, amount, currency)``. The amount can
                        be either an int, float, or string as long as it is
                        a valid input to ``decimal.Decimal``. The currency
                        must be :ref:`supported <supported currencies>`.
        :type outputs: ``list`` of ``tuple``
        :param fee: The number of satoshi per byte to pay to miners. By default
                    Bitcash will poll `<https://bitcoincashfees.earn.com>`_ and use a fee
                    that will allow your transaction to be confirmed as soon as
                    possible.
        :type fee: ``int``
        :param leftover: The destination that will receive any change from the
                         transaction. By default Bitcash will send any change to
                         the same address you sent from.
        :type leftover: ``str``
        :param combine: Whether or not Bitcash should use all available UTXOs to
                        make future transactions smaller and therefore reduce
                        fees. By default Bitcash will consolidate UTXOs.
        :type combine: ``bool``
        :param message: A message to include in the transaction. This will be
                        stored in the blockchain forever. Due to size limits,
                        each message will be stored in chunks of 220 bytes.
        :type message: ``str``
        :param unspents: The UTXOs to use as the inputs. By default Bitcash will
                         communicate with the blockchain itself.
        :type unspents: ``list`` of :class:`~bitcash.network.meta.Unspent`
        :returns: The signed transaction as hex.
        :rtype: ``str``
        """

        baton_vout = None

        if mint_baton_address:
            baton_vout = 2

        op_return = slp_create.buildGenesisOpReturn(
            ticker,
            token_name,
            document_url,
            document_hash,
            decimals,
            baton_vout,
            token_quantity,
            token_type,
        )

        # hacky but works, find a better way
        # TODO: Find a better way
        op_return = bytes.fromhex(op_return[2:])

        # This strips the "6a" (OP_RETURN) off the string,
        # and then converts it to bytes (needed for construct_output_block)

        # the minimum amount of BCH required for a tx
        min_satoshi = 546
        outputs = [(self.address, min_satoshi, "satoshi")]

        if mint_baton_address is not None:
            outputs.append((mint_baton_address, min_satoshi, "satoshi"))

        unspents, outputs = sanitize_slp_create_tx_data(
            self.address,
            unspents or self.unspents,
            outputs,
            fee or get_fee(),
            leftover or self.address,
            combine=combine,
            message=op_return,
            compressed=self.is_compressed(),
            custom_pushdata=custom_pushdata,
        )

        tx_hex = create_p2pkh_transaction(self, unspents, outputs, custom_pushdata=True)

        NetworkAPI.broadcast_tx(tx_hex, network=NETWORKS[self._network])

        return calc_txid(tx_hex)

    def create_child_nft(
        self,
        tokenId,
        amount,
        address=None,
        fee=None,
        leftover=None,
        combine=True,
        message=None,
        unspents=None,
        slp_unspents=None,
        custom_pushdata=True,
    ):  # pragma: no cover
        """Creates a signed P2PKH transaction and attempts to broadcast it on
        the blockchain. This accepts the same arguments as
        :func:`~bitcash.PrivateKey.create_transaction`.
        :param outputs: A sequence of outputs you wish to send in the form
                        ``(destination, amount, currency)``. The amount can
                        be either an int, float, or string as long as it is
                        a valid input to ``decimal.Decimal``. The currency
                        must be :ref:`supported <supported currencies>`.
        :type outputs: ``list`` of ``tuple``
        :param fee: The number of satoshi per byte to pay to miners. By default
                    Bitcash will poll `<https://bitcoincashfees.earn.com>`_ and use a fee
                    that will allow your transaction to be confirmed as soon as
                    possible.
        :type fee: ``int``
        :param leftover: The destination that will receive any change from the
                         transaction. By default Bitcash will send any change to
                         the same address you sent from.
        :type leftover: ``str``
        :param combine: Whether or not Bitcash should use all available UTXOs to
                        make future transactions smaller and therefore reduce
                        fees. By default Bitcash will consolidate UTXOs.
        :type combine: ``bool``
        :param message: A message to include in the transaction. This will be
                        stored in the blockchain forever. Due to size limits,
                        each message will be stored in chunks of 220 bytes.
        :type message: ``str``
        :param unspents: The UTXOs to use as the inputs. By default Bitcash will
                         communicate with the blockchain itself.
        :type unspents: ``list`` of :class:`~bitcash.network.meta.Unspent`
        :returns: The transaction ID.
        :rtype: ``str``
        """
        
        # Grab utxos for specified token
        token_slp_utxos = SlpAPI.get_utxo_by_tokenId(
            address=self.slp_address, tokenId=tokenId, network=NETWORKS[self._network])

        fanned_token_slp_utxos = []

        for utxo in token_slp_utxos:
            if utxo[0] == '1':
                fanned_token_slp_utxos.append(utxo)

        if len(fanned_token_slp_utxos) == 0:
            raise(Exception("There are not any fanned group utxos."))

        if len(fanned_token_slp_utxos) < amount:
            raise(Exception("Not enough fanned group utxos."))

        # cut out unconfirmed to work around slpdb not handling the spent group tokens
        unconfirmed = SlpAPI.get_unconfirmed_spent_utxo_genesis_65(
            tokenId, self.slp_address, network=NETWORKS[self._network])

        def _is_unconfirmed(unspent, unconfirmed):
            return (unspent[2], unspent[3]) in [
                (unconfirm[2], unconfirm[3]) for unconfirm in unconfirmed
            ]

        confirmed_token_slp_utxos = [unspent for unspent in fanned_token_slp_utxos if not _is_unconfirmed(
            unspent, unconfirmed)]

        # slice the desired amount
        specified_amount_fanned_token_slp_utxos = confirmed_token_slp_utxos[:amount]

        # map against unspent objects
        def _is_slp(unspent, specified_amount_fanned_token_slp_utxos):
            return (unspent.txid, unspent.txindex) in [
                (slp_utxo[2], slp_utxo[3]) for slp_utxo in specified_amount_fanned_token_slp_utxos
            ]

        slp_utxos = [unspent for unspent in self.slp_unspents if _is_slp(
            unspent, specified_amount_fanned_token_slp_utxos)]
        
        # Pulls Group NFT token details to populate ticker and name
        tokenDetails = SlpAPI.get_token_by_id(tokenId, network=NETWORKS[self._network])[
            0
        ]
        
        slp_unspents = self.slp_unspents.copy()

        # Change this for different child tickers/names
        # TODO change this
        op_return = slp_create.buildGenesisOpReturn(
            tokenDetails[3], tokenDetails[4] + " child", "", "", 0, None, 1, 65
        )

        # Slice the 6a off the opreturn
        op_return = bytes.fromhex(op_return[2:])

        txids = []
        index = 0   

        while index < amount:
            
            # Clears previous slp_unspents to only include the desired utxo
            slp_unspents = []
            slp_unspents.append(slp_utxos[index])

            min_satoshi = 546

            if address:
                outputs = [(address, min_satoshi, "satoshi")]
            else:
                outputs = [(self.address, min_satoshi, "satoshi")]

            unspents, outputs = sanitize_slp_create_tx_data(
                address or self.address,
                self.unspents,
                outputs,
                fee or get_fee(),
                leftover or self.address,
                combine=combine,
                message=op_return,
                compressed=self.is_compressed(),
                custom_pushdata=custom_pushdata,
                slp_unspents=slp_unspents,
            )

            tx_hex = create_p2pkh_transaction(self, unspents, outputs, custom_pushdata=True)

            NetworkAPI.broadcast_tx(tx_hex, network=NETWORKS[self._network])
            calced_tx_hex = calc_txid(tx_hex)
            txids.append(calced_tx_hex) 

            time.sleep(5)

            self.get_balance()
            
            index+=1
            
            # Spent group utxo isnt flagged as slp or SPENT when getting unspents, need to filter it out
            # for these purposes. Might be a better implementation "soon"
            # For now will filter out dust

            filtered_unspents = []
            for utxo in self.unspents:
                if utxo.amount > 546:
                    filtered_unspents.append(utxo)

            self.unspents = filtered_unspents
            unspents = filtered_unspents

        return txids

    def fan_group_token(
        self,
        tokenId,
        amount,
        address=None,
        fee=None,
        leftover=None,
        combine=True,
        message=None,
        unspents=None,
        slp_unspents=None,
        custom_pushdata=False,
    ):

        i = 0
        outputs = []

        while i < amount:

            outputs.append((self.slp_address, 1))
            i+=1
        
        tx_hex = self.create_slp_transaction(
            outputs,
            tokenId,
            fee=fee,
            leftover=leftover,
            combine=combine,
            combine_slp=False,
            unspents=unspents,
            slp_unspents=slp_unspents,
            custom_pushdata=True,
        )

        NetworkAPI.broadcast_tx(tx_hex, network=NETWORKS[self._network])

        return calc_txid(tx_hex)

    def mint_slp(
        self,
        tokenId,
        amount,
        keepBaton=True,
        fee=None,
        leftover=None,
        combine=True,
        message=None,
        unspents=None,
        custom_pushdata=False,
    ):
        """Creates a signed P2PKH transaction.
        :param outputs: A sequence of outputs you wish to send in the form
                        ``(destination, amount, currency)``. The amount can
                        be either an int, float, or string as long as it is
                        a valid input to ``decimal.Decimal``. The currency
                        must be :ref:`supported <supported currencies>`.
        :type outputs: ``list`` of ``tuple``
        :param fee: The number of satoshi per byte to pay to miners. By default
                    Bitcash will poll `<https://bitcoincashfees.earn.com>`_ and use a fee
                    that will allow your transaction to be confirmed as soon as
                    possible.
        :type fee: ``int``
        :param leftover: The destination that will receive any change from the
                         transaction. By default Bitcash will send any change to
                         the same address you sent from.
        :type leftover: ``str``
        :param combine: Whether or not Bitcash should use all available UTXOs to
                        make future transactions smaller and therefore reduce
                        fees. By default Bitcash will consolidate UTXOs.
        :type combine: ``bool``
        :param message: A message to include in the transaction. This will be
                        stored in the blockchain forever. Due to size limits,
                        each message will be stored in chunks of 220 bytes.
        :type message: ``str``
        :param unspents: The UTXOs to use as the inputs. By default Bitcash will
                         communicate with the blockchain itself.
        :type unspents: ``list`` of :class:`~bitcash.network.meta.Unspent`
        :returns: The signed transaction as hex.
        :rtype: ``str``
        """

        baton_vout = None

        if keepBaton:
            baton_vout = 2

        tokenDetails = SlpAPI.get_token_by_id(tokenId, network=NETWORKS[self._network])[
            0
        ]
        tokenType = tokenDetails[7]

        op_return = slp_create.buildMintOpReturn(
            tokenId, baton_vout, amount, token_type=tokenType
        )

        # Check that self.address contains mint baton
        mint_baton_utxo = SlpAPI.get_mint_baton(
            tokenId, network=NETWORKS[self._network]
        )

        if mint_baton_utxo:
            address_with_baton = mint_baton_utxo[0][0]

        else:
            address_with_baton = None

        if self.slp_address != address_with_baton:
            raise ValueError("The baton is not on your address")

        # Grab baton utxo from baton pool
        def _baton_match(batons, baton_utxo):
            return (batons.txid, batons.txindex) in [
                (baton[1], baton[2]) for baton in baton_utxo
            ]

        batons = self.batons
        baton_match = [i for i in batons if _baton_match(i, mint_baton_utxo)]

        if unspents == None:
            unspents = self.unspents

        unspents.extend(baton_match)

        # hacky but works, find a better way
        # TODO: Find a better way
        op_return = bytes.fromhex(op_return[2:])
        # This strips the "6a" (OP_RETURN) off the string,
        # and then converts it to bytes (needed for construct_output_block)

        # the minimum amount of BCH required for a tx
        min_satoshi = 546
        outputs = [(self.address, min_satoshi, "satoshi")]

        if keepBaton:
            outputs.append((self.address, min_satoshi, "satoshi"))

        unspents, outputs = sanitize_slp_create_tx_data(
            self.address,
            unspents,
            outputs,
            fee or get_fee(),
            leftover or self.address,
            combine=combine,
            message=op_return,
            compressed=self.is_compressed(),
            custom_pushdata=custom_pushdata,
        )

        tx_hex = create_p2pkh_transaction(self, unspents, outputs, custom_pushdata=True)

        NetworkAPI.broadcast_tx(tx_hex, network=NETWORKS[self._network])

        return calc_txid(tx_hex)

    @classmethod
    def prepare_transaction(
        cls,
        address,
        outputs,
        compressed=True,
        fee=None,
        leftover=None,
        combine=True,
        message=None,
        unspents=None,
    ):  # pragma: no cover
        """Prepares a P2PKH transaction for offline signing.

        :param address: The address the funds will be sent from.
        :type address: ``str``
        :param outputs: A sequence of outputs you wish to send in the form
                        ``(destination, amount, currency)``. The amount can
                        be either an int, float, or string as long as it is
                        a valid input to ``decimal.Decimal``. The currency
                        must be :ref:`supported <supported currencies>`.
        :type outputs: ``list`` of ``tuple``
        :param compressed: Whether or not the ``address`` corresponds to a
                           compressed public key. This influences the fee.
        :type compressed: ``bool``
        :param fee: The number of satoshi per byte to pay to miners. By default
                    Bitcash will poll `<https://bitcoincashfees.earn.com>`_ and use a fee
                    that will allow your transaction to be confirmed as soon as
                    possible.
        :type fee: ``int``
        :param leftover: The destination that will receive any change from the
                         transaction. By default Bitcash will send any change to
                         the same address you sent from.
        :type leftover: ``str``
        :param combine: Whether or not Bitcash should use all available UTXOs to
                        make future transactions smaller and therefore reduce
                        fees. By default Bitcash will consolidate UTXOs.
        :type combine: ``bool``
        :param message: A message to include in the transaction. This will be
                        stored in the blockchain forever. Due to size limits,
                        each message will be stored in chunks of 220 bytes.
        :type message: ``str``
        :param unspents: The UTXOs to use as the inputs. By default Bitcash will
                         communicate with the blockchain itself.
        :type unspents: ``list`` of :class:`~bitcash.network.meta.Unspent`
        :returns: JSON storing data required to create an offline transaction.
        :rtype: ``str``
        """
        unspents, outputs = sanitize_tx_data(
            unspents or NetworkAPI.get_unspent(address),
            outputs,
            fee or get_fee(),
            leftover or address,
            combine=combine,
            message=message,
            compressed=compressed,
        )

        data = {
            "unspents": [unspent.to_dict() for unspent in unspents],
            "outputs": outputs,
        }

        return json.dumps(data, separators=(",", ":"))

    def sign_transaction(self, tx_data):  # pragma: no cover
        """Creates a signed P2PKH transaction using previously prepared
        transaction data.

        :param tx_data: Output of :func:`~bitcash.PrivateKey.prepare_transaction`.
        :type tx_data: ``str``
        :returns: The signed transaction as hex.
        :rtype: ``str``
        """
        data = json.loads(tx_data)

        unspents = [Unspent.from_dict(unspent) for unspent in data["unspents"]]
        outputs = data["outputs"]

        return create_p2pkh_transaction(self, unspents, outputs)

    @classmethod
    def from_hex(cls, hexed):
        """
        :param hexed: A private key previously encoded as hex.
        :type hexed: ``str``
        :rtype: :class:`~bitcash.PrivateKey`
        """
        return PrivateKey(ECPrivateKey.from_hex(hexed))

    @classmethod
    def from_bytes(cls, bytestr):
        """
        :param bytestr: A private key previously encoded as hex.
        :type bytestr: ``bytes``
        :rtype: :class:`~bitcash.PrivateKey`
        """
        return PrivateKey(ECPrivateKey(bytestr))

    @classmethod
    def from_der(cls, der):
        """
        :param der: A private key previously encoded as DER.
        :type der: ``bytes``
        :rtype: :class:`~bitcash.PrivateKey`
        """
        return PrivateKey(ECPrivateKey.from_der(der))

    @classmethod
    def from_pem(cls, pem):
        """
        :param pem: A private key previously encoded as PEM.
        :type pem: ``bytes``
        :rtype: :class:`~bitcash.PrivateKey`
        """
        return PrivateKey(ECPrivateKey.from_pem(pem))

    @classmethod
    def from_int(cls, num):
        """
        :param num: A private key in raw integer form.
        :type num: ``int``
        :rtype: :class:`~bitcash.PrivateKey`
        """
        return PrivateKey(ECPrivateKey.from_int(num))

    def __repr__(self):
        return f"<PrivateKey: {self.address}>"


class PrivateKeyTestnet(PrivateKey):
    """This class represents a testnet BitcoinCash private key. **Note:** coins
    on the test network have no monetary value!

    :param wif: A private key serialized to the Wallet Import Format. If the
                argument is not supplied, a new private key will be created.
                The WIF compression flag will be adhered to, but the version
                byte is disregarded. Compression will be used by all new keys.
    :type wif: ``str``
    :raises TypeError: If ``wif`` is not a ``str``.
    """

    def __init__(self, wif=None, network="test"):
        super().__init__(wif=wif, network=network)

    @classmethod
    def from_hex(cls, hexed):
        """
        :param hexed: A private key previously encoded as hex.
        :type hexed: ``str``
        :rtype: :class:`~bitcash.PrivateKeyTestnet`
        """
        return PrivateKeyTestnet(ECPrivateKey.from_hex(hexed))

    @classmethod
    def from_bytes(cls, bytestr):
        """
        :param bytestr: A private key previously encoded as hex.
        :type bytestr: ``bytes``
        :rtype: :class:`~bitcash.PrivateKeyTestnet`
        """
        return PrivateKeyTestnet(ECPrivateKey(bytestr))

    @classmethod
    def from_der(cls, der):
        """
        :param der: A private key previously encoded as DER.
        :type der: ``bytes``
        :rtype: :class:`~bitcash.PrivateKeyTestnet`
        """
        return PrivateKeyTestnet(ECPrivateKey.from_der(der))

    @classmethod
    def from_pem(cls, pem):
        """
        :param pem: A private key previously encoded as PEM.
        :type pem: ``bytes``
        :rtype: :class:`~bitcash.PrivateKeyTestnet`
        """
        return PrivateKeyTestnet(ECPrivateKey.from_pem(pem))

    @classmethod
    def from_int(cls, num):
        """
        :param num: A private key in raw integer form.
        :type num: ``int``
        :rtype: :class:`~bitcash.PrivateKeyTestnet`
        """
        return PrivateKeyTestnet(ECPrivateKey.from_int(num))

    def __repr__(self):
        return f"<PrivateKeyTestnet: {self.address}>"


class PrivateKeyRegtest(PrivateKey):
    """This class represents a regtest BitcoinCash private key. **Note:** coins
    on the regtest network have no monetary value!

    :param wif: A private key serialized to the Wallet Import Format. If the
                argument is not supplied, a new private key will be created.
                The WIF compression flag will be adhered to, but the version
                byte is disregarded. Compression will be used by all new keys.
    :type wif: ``str``
    :raises TypeError: If ``wif`` is not a ``str``.
    """

    def __init__(self, wif=None, network="regtest"):
        super().__init__(wif, network)

    @classmethod
    def from_hex(cls, hexed):
        """
        :param hexed: A private key previously encoded as hex.
        :type hexed: ``str``
        :rtype: :class:`~bitcash.PrivateKeyRegtest`
        """
        return PrivateKeyRegtest(ECPrivateKey.from_hex(hexed))

    @classmethod
    def from_bytes(cls, bytestr):
        """
        :param bytestr: A private key previously encoded as hex.
        :type bytestr: ``bytes``
        :rtype: :class:`~bitcash.PrivateKeyRegtest`
        """
        return PrivateKeyRegtest(ECPrivateKey(bytestr))

    @classmethod
    def from_der(cls, der):
        """
        :param der: A private key previously encoded as DER.
        :type der: ``bytes``
        :rtype: :class:`~bitcash.PrivateKeyRegtest`
        """
        return PrivateKeyRegtest(ECPrivateKey.from_der(der))

    @classmethod
    def from_pem(cls, pem):
        """
        :param pem: A private key previously encoded as PEM.
        :type pem: ``bytes``
        :rtype: :class:`~bitcash.PrivateKeyRegtest`
        """
        return PrivateKeyRegtest(ECPrivateKey.from_pem(pem))

    @classmethod
    def from_int(cls, num):
        """
        :param num: A private key in raw integer form.
        :type num: ``int``
        :rtype: :class:`~bitcash.PrivateKeyRegtest`
        """
        return PrivateKeyRegtest(ECPrivateKey.from_int(num))

    def __repr__(self):
        return f"<PrivateKeyRegtest: {self.address}>"


Key = PrivateKey
