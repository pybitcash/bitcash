from __future__ import annotations

from enum import Enum
from typing import Literal, NamedTuple, Optional, Union
from dataclasses import dataclass
import typing

from bitcash.exceptions import InvalidCashToken

COMMITMENT_LENGTH = 128
MAX_TOKEN_AMOUNT = 9223372036854775807


class Network(Enum):
    """
    Enum for different Bitcoin Cash networks.
    The names are the versions used in bitcash, and the values are the network names
    in Bitcoin Cash.
    """

    main = "mainnet"
    test = "testnet"
    regtest = "regtest"


NetworkStr = Union[Literal["mainnet"], Literal["testnet"], Literal["regtest"]]


class NFTCapability(Enum):
    """
    Enum for NFT capabilities. The values are the int values in nft capability bit in
    the cashtoken format.
    """

    none = 0
    mutable = 1
    minting = 2


class CashAddressVersion(NamedTuple):
    prefix: str
    version_bit: int
    network: Network


class CashTokens(NamedTuple):
    """
    The cash tokens in an output of a transaction.
    :param category_id: Category hex of the cashtoken.
    :param nft_capability: Capability of the non-fungible token.
    :param nft_commitment: Commitment bytes of the non-fungible token.
    :param token_amount: Fungible token amount of the cashtoken.
    """

    category_id: Optional[str]
    nft_capability: Optional[NFTCapability]
    nft_commitment: Optional[bytes]
    token_amount: Optional[int]

    def verify(self):
        if self.category_id is None:
            if self.nft_capability is not None or self.token_amount is not None:
                raise InvalidCashToken("category_id missing")
        else:
            if self.token_amount is None and self.nft_capability is None:
                raise InvalidCashToken(
                    "CashToken must have atleast an amount or a capability"
                )

        if self.nft_capability is not None:
            if not isinstance(self.nft_capability, NFTCapability):
                raise InvalidCashToken("expected nft_capability as NFTCapability enum")

        if self.nft_commitment is not None:
            if self.nft_capability is None:
                raise InvalidCashToken("nft commitment found without nft capability")
            if not isinstance(self.nft_commitment, bytes):
                raise ValueError("expected nft_commitment as bytes")
            if (
                len(self.nft_commitment) > COMMITMENT_LENGTH
                or len(self.nft_commitment) == 0
            ):
                raise InvalidCashToken(
                    f"0 < valid nft commitment length"
                    f" <= {COMMITMENT_LENGTH}, received"
                    f" length: {len(self.nft_commitment)}"
                )
        if self.token_amount is not None and (
            self.token_amount > MAX_TOKEN_AMOUNT or self.token_amount < 1
        ):
            raise InvalidCashToken(f"1 <= valid token amount <= {MAX_TOKEN_AMOUNT}")


SerializedOutput = tuple[
    str, int, Optional[str], Optional[str], Optional[str], Optional[int]
]


class PreparedOutput(NamedTuple):
    """
    The prepared output of a transaction.
    :param sciptcode: The scriptcode of the output with token prefix.
    :param amount: The amount of the output in satoshis.
    :param cashtokens: The cashtokens of the output.
    """

    scriptcode: bytes
    amount: int
    cashtokens: CashTokens

    def to_serializable(self) -> SerializedOutput:
        return (
            self.scriptcode.hex(),
            self.amount,
            self.cashtokens.category_id,
            (
                self.cashtokens.nft_capability.name
                if self.cashtokens.nft_capability
                else None
            ),
            (
                self.cashtokens.nft_commitment.hex()
                if self.cashtokens.nft_commitment
                else None
            ),
            self.cashtokens.token_amount,
        )

    @classmethod
    def from_serializable(cls, serializable: SerializedOutput) -> PreparedOutput:
        return cls(
            bytes.fromhex(serializable[0]),
            serializable[1],
            CashTokens(
                serializable[2],
                NFTCapability[serializable[3]] if serializable[3] else None,
                bytes.fromhex(serializable[4]) if serializable[4] else None,
                serializable[5],
            ),
        )


@dataclass
class TokenData:
    """
    Data class for holding token information for a cashtoken category.

    :param token_amount: Fungible token amount of the cashtoken.
    :param nft: List of NFTData associated with the token.
    """

    token_amount: Optional[int]
    nft: Optional[list[NFTData]]

    @classmethod
    def get_empty(cls) -> TokenData:
        return cls(
            token_amount=None,
            nft=None,
        )

    def is_empty(self) -> bool:
        return self.token_amount is None and (self.nft is None or len(self.nft) == 0)

    def to_dict(self) -> dict[str, Union[str, int, list[dict[str, Union[str, bytes]]]]]:
        dict_: dict[str, Union[str, int, list[dict[str, Union[str, bytes]]]]] = {}
        if self.token_amount is not None:
            dict_["token_amount"] = self.token_amount
        if self.nft is not None:
            dict_["nft"] = [nft_data.to_dict() for nft_data in self.nft]
        return dict_

    @classmethod
    def from_dict(
        cls, dict_: dict[str, Union[str, int, list[dict[str, Union[str, bytes]]]]]
    ) -> TokenData:
        token_amount = typing.cast(Optional[int], dict_.get("token_amount"))
        nft_list_dict = typing.cast(
            Optional[list[dict[str, Union[str, bytes]]]], dict_.get("nft")
        )
        nft_list = (
            [NFTData.from_dict(nft_dict) for nft_dict in nft_list_dict]
            if nft_list_dict
            else None
        )
        return cls(
            token_amount=token_amount,
            nft=nft_list,
        )


@dataclass
class NFTData:
    """
    Data class for holding NFT information.

    :param capability: Capability of the non-fungible token.
    :param commitment: Commitment bytes of the non-fungible token.
    """

    capability: NFTCapability
    commitment: Optional[bytes]

    def to_dict(self) -> dict[str, Union[str, bytes]]:
        dict_: dict[str, Union[str, bytes]] = {"capability": self.capability.name}
        if self.commitment:
            dict_["commitment"] = self.commitment
        return dict_

    @classmethod
    def from_dict(cls, dict_: dict[str, Union[str, bytes]]) -> NFTData:
        nft_capability = typing.cast(str, dict_["capability"])
        nft_commitment = typing.cast(Optional[bytes], dict_.get("commitment"))
        return cls(
            capability=NFTCapability[nft_capability],
            commitment=nft_commitment,
        )


# The output tuple a user send.
# Output tuple of format: (destination address, amount, currency) or
# (destination address, amount, currency, category_id, nft_capability,
# nft_commitment, token_amount)
SimpleUserOutput = tuple[str, int, str]
CashTokenUserOutput = tuple[
    str, int, str, Optional[str], Optional[str], Optional[bytes], Optional[int]
]
UserOutput = Union[SimpleUserOutput, CashTokenUserOutput]
