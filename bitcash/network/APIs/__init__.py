from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Callable, Optional

from bitcash.network.meta import Unspent
from bitcash.network.transaction import Transaction
from bitcash.types import NFTCapability, NetworkStr


class BaseAPI(ABC):
    """
    Abstract class for API classes

    :param network_endpoint: Network endpoint to send requests
    """

    def __init__(self, network_endpoint: str):
        self.network_endpoint = network_endpoint

    @classmethod
    @abstractmethod
    def get_default_endpoints(cls, network: NetworkStr) -> list[str]:
        """
        Return default endpoints for a network

        :param network: The BCH network.
        :returns: List of default endpoints
        """

    @abstractmethod
    def get_blockheight(self, *args, **kwargs) -> int:
        """
        Returns the current block height

        :returns: Current block height
        """

    @abstractmethod
    def get_balance(self, address: str, *args, **kwargs) -> int:
        """
        Returns balance of an address

        :param address: Cashaddress of the locking script
        :returns: BCH amount in satoshis
        """

    @abstractmethod
    def get_transactions(self, address: str, *args, **kwargs) -> list[str]:
        """Gets the ID of all transactions related to an address.

        :param address: The address in question.
        :returns: A list of transaction IDs.
        """

    @abstractmethod
    def get_tx_amount(self, txid: str, txindex: int, *args, **kwargs) -> int:
        """Gets the amount of a given transaction output.

        :param txid: The transaction id in question.
        :param txindex: The transaction index in question.
        :returns: The amount in satoshis.
        """

    @abstractmethod
    def get_transaction(self, txid: str, *args, **kwargs) -> Transaction:
        """
        Returns transaction data of a transaction

        :param txid: Transaction id hex
        :returns: Instance of class Transaction
        """

    @abstractmethod
    def get_unspent(self, address: str, *args, **kwargs) -> list[Unspent]:
        """
        Returns list of unspent outputs associated with an address

        :param address: Cashaddress of the locking script
        :returns: List of unspents
        """

    @abstractmethod
    def get_raw_transaction(self, txid: str, *args, **kwargs) -> dict[str, Any]:
        """Gets the raw, unparsed transaction details.

        :param txid: The transaction id in question.
        :returns: The raw transaction details as a dictionary.
        """

    @abstractmethod
    def broadcast_tx(self, tx_hex: str, *args, **kwargs) -> bool:
        """
        Broadcast a raw transaction

        :param tx_hex: The hex representaion of the transaction to be
                       broadcasted.
        :return: Boolean indicating if the tx is broadcasted
        """

    @abstractmethod
    def subscribe_address(
        self, address: str, callback: Callable[[str, str | None], None], *args, **kwargs
    ) -> SubscriptionHandle:
        """
        Subscribe to an address and receive real-time notifications.
        :param address: Address to subscribe to.
        :param callback: Function to call with (address, status_hash) on update.
            status_hash is None if the address has no history.
        :return: A SubscriptionHandle object for managing the subscription.
        """

    @abstractmethod
    def get_cashtoken_addresses(
        self,
        category_id: str,
        nft_capability: Optional[NFTCapability] = None,
        nft_commitment: Optional[bytes] = None,
        has_token: bool = False,
        *args,
        **kwargs,
    ) -> set[str]:
        """Gets all addresses holding unspent outputs of a given cashtoken category.

        :param category_id: The token category ID (hex string).
        :param nft_capability: If set, only return addresses holding an NFT with this capability
            (one of ``"none"``, ``"mutable"``, ``"minting"``).
        :param nft_commitment: If set, only return addresses holding an NFT with this commitment.
        :param has_token: If True, only return addresses holding fungible tokens of this category.
        :returns: A set of addresses holding the cashtoken.
        :raises NotImplementedError: If the API does not support this query.
        """


class SubscriptionHandle:
    """
    Handle for managing a subscription
    """

    def __init__(self, stop_callback: Callable[[], None]) -> None:
        self._stop_callback = stop_callback

    def unsubscribe(self) -> None:
        """
        Unsubscribe from the subscription
        """
        self._stop_callback()
