import pytest
import unittest
from unittest import mock
import json

import bitcash
from bitcash.network.services import (
    BitcoinDotComAPI,
    BitcoreAPI,
    NetworkAPI,
    set_service_timeout,
)
from bitcash.network.slp_services import SlpAPI

from tests.utils import (
    catch_errors_raise_warnings,
    decorate_methods,
    raise_connection_error,
)
from bitcash.network.meta import Unspent
from bitcash.wallet import (
    BaseKey,
    Key,
    PrivateKey,
    PrivateKeyTestnet,
    PrivateKeyRegtest,
    wif_to_key,
)
from tests.samples import WALLET_FORMAT_TEST_SLP

NETWORKS = {"main": "mainnet", "test": "testnet", "regtest": "regtest"}

MAIN_SLP_ADDRESS_USED = "simpleledger:qz9y7ujr9ucavpdsywnykrxnlvds5nwxz5vejsm5nf"
TEST_SLP_ADDRESS_USED = ""
REG_SLP_ADDRESS_USED = ""

MAIN_TEST_COIN_NAME = "Test Coins"
MAIN_TEST_COIN_TOKENID = (
    "ac7bdca0161752c80c2c7de6fb5cd149054a078e6cd4b6381acc2016b8ff0e8d"
)

TESTNET_TEST_COIN_TOKENID = (
    "15cd6253c8ac838a4b9f9918fc84b0484a45b661a78ccc597a7653a0fc175d1f"
)


# Replace later with controlled token
MAIN_TEMPORARY_GROUP_NFT_TEST_COIN_TOKENID = (
    "b641a4c7efc4f81739f84be7eda8e0c89f3e0338f107fdfe647236819fd62ed2"
)
MAIN_TEMP_CHILD_TOKENID = (
    "5745f6d0c91efbb49eb427255093171af36c498b2011eefb0071c0a6fe9d9844"
)

MAIN_BATON_UTXO = (
    "simpleledger:qq72px9d5he0ah87rrl8vg9y7gdl5kqguvrwa5w7jv",
    "ac7bdca0161752c80c2c7de6fb5cd149054a078e6cd4b6381acc2016b8ff0e8d",
    2,
)
TESTNET_BATON_UTXO = (
    "slptest:qz9y7ujr9ucavpdsywnykrxnlvds5nwxz5ly6hk5ck",
    "15cd6253c8ac838a4b9f9918fc84b0484a45b661a78ccc597a7653a0fc175d1f",
    2,
)
TESTNET_BATON_ADDRESS = "slptest:qz9y7ujr9ucavpdsywnykrxnlvds5nwxz5ly6hk5ck"

MAIN_OP_RETURN = "OP_RETURN 534c5000 01 47454e45534953 544343 5465737420436f696e73 6d696e742e626974636f696e2e636f6d 00 02 00000000000f4240"
MAIN_OP_RETURN_TEST_TXID = (
    "ac7bdca0161752c80c2c7de6fb5cd149054a078e6cd4b6381acc2016b8ff0e8d"
)

MAIN = "mainnet"
TEST = "testnet"
REG = "regtest"

MAIN_GET_BALANCE_URL = "https://slpdb.fountainhead.cash/q/eyJ2IjogMywgInEiOiB7ImRiIjogWyJnIl0sICJhZ2dyZWdhdGUiOiBbeyIkbWF0Y2giOiB7ImdyYXBoVHhuLm91dHB1dHMuYWRkcmVzcyI6ICJzaW1wbGVsZWRnZXI6cXo5eTd1anI5dWNhdnBkc3l3bnlrcnhubHZkczVud3h6NXZlanNtNW5mIn19LCB7IiR1bndpbmQiOiAiJGdyYXBoVHhuLm91dHB1dHMifSwgeyIkbWF0Y2giOiB7ImdyYXBoVHhuLm91dHB1dHMuc3RhdHVzIjogIlVOU1BFTlQiLCAiZ3JhcGhUeG4ub3V0cHV0cy5hZGRyZXNzIjogInNpbXBsZWxlZGdlcjpxejl5N3Vqcjl1Y2F2cGRzeXdueWtyeG5sdmRzNW53eHo1dmVqc201bmYifX0sIHsiJGdyb3VwIjogeyJfaWQiOiAiJHRva2VuRGV0YWlscy50b2tlbklkSGV4IiwgInNscEFtb3VudCI6IHsiJHN1bSI6ICIkZ3JhcGhUeG4ub3V0cHV0cy5zbHBBbW91bnQifX19LCB7IiRzb3J0IjogeyJzbHBBbW91bnQiOiAtMX19LCB7IiRtYXRjaCI6IHsic2xwQW1vdW50IjogeyIkZ3QiOiAwfX19LCB7IiRsb29rdXAiOiB7ImZyb20iOiAidG9rZW5zIiwgImxvY2FsRmllbGQiOiAiX2lkIiwgImZvcmVpZ25GaWVsZCI6ICJ0b2tlbkRldGFpbHMudG9rZW5JZEhleCIsICJhcyI6ICJ0b2tlbiJ9fSwgeyIkbWF0Y2giOiB7Il9pZCI6ICJhYzdiZGNhMDE2MTc1MmM4MGMyYzdkZTZmYjVjZDE0OTA1NGEwNzhlNmNkNGI2MzgxYWNjMjAxNmI4ZmYwZThkIn19XSwgInNvcnQiOiB7InNscEFtb3VudCI6IC0xfSwgInNraXAiOiAwLCAibGltaXQiOiAxMH19"
MAIN_GET_BALANCE_RESPONSE = """
{"g":[{"_id":"ac7bdca0161752c80c2c7de6fb5cd149054a078e6cd4b6381acc2016b8ff0e8d","slpAmount":"50000","token":[{"_id":"5fd8be0384e07624f24c1f2d","schema_version":79,"lastUpdatedBlock":666017,"tokenDetails":{"decimals":0,"tokenIdHex":"ac7bdca0161752c80c2c7de6fb5cd149054a078e6cd4b6381acc2016b8ff0e8d","timestamp":"2020-12-15 14:04:44","timestamp_unix":1608041084,"transactionType":"GENESIS","versionType":1,"documentUri":"mint.bitcoin.com","documentSha256Hex":null,"symbol":"TCC","name":"Test Coins","batonVout":2,"containsBaton":true,"genesisOrMintQuantity":"1000000","sendOutputs":null},"mintBatonUtxo":"ac7bdca0161752c80c2c7de6fb5cd149054a078e6cd4b6381acc2016b8ff0e8d:2","mintBatonStatus":"ALIVE","tokenStats":{"block_created":666018,"approx_txns_since_genesis":1},"_pruningState":{"pruneHeight":0,"sendCount":0,"mintCount":0}}]}]}
"""
MAIN_GET_BALANCE_JSON = json.loads(MAIN_GET_BALANCE_RESPONSE)
MAIN_GET_BALANCE = [("ac7bdca0161752c80c2c7de6fb5cd149054a078e6cd4b6381acc2016b8ff0e8d", "Test Coins", "50000")]


MAIN_GET_TOKEN_BY_ID_URL = "https://slpdb.fountainhead.cash/q/eyJ2IjogMywgInEiOiB7ImRiIjogWyJ0Il0sICJmaW5kIjogeyIkcXVlcnkiOiB7InRva2VuRGV0YWlscy50b2tlbklkSGV4IjogImFjN2JkY2EwMTYxNzUyYzgwYzJjN2RlNmZiNWNkMTQ5MDU0YTA3OGU2Y2Q0YjYzODFhY2MyMDE2YjhmZjBlOGQifX0sICJwcm9qZWN0IjogeyJ0b2tlbkRldGFpbHMiOiAxLCAidG9rZW5TdGF0cyI6IDEsICJfaWQiOiAwfSwgImxpbWl0IjogMTAwMH19"
MAIN_GET_TOKEN_BY_ID_RESPONSE = """
{"t":[{"tokenDetails":{"decimals":0,"tokenIdHex":"ac7bdca0161752c80c2c7de6fb5cd149054a078e6cd4b6381acc2016b8ff0e8d","timestamp":"2020-12-15 14:04:44","timestamp_unix":1608041084,"transactionType":"GENESIS","versionType":1,"documentUri":"mint.bitcoin.com","documentSha256Hex":null,"symbol":"TCC","name":"Test Coins","batonVout":2,"containsBaton":true,"genesisOrMintQuantity":"1000000","sendOutputs":null},"tokenStats":{"block_created":666018,"approx_txns_since_genesis":1}}]}
"""
MAIN_GET_TOKEN_BY_ID_JSON = json.loads(MAIN_GET_TOKEN_BY_ID_RESPONSE)
MAIN__GET_TOKEN_BY_ID_RESULT = [
    (
        "ac7bdca0161752c80c2c7de6fb5cd149054a078e6cd4b6381acc2016b8ff0e8d",
        "mint.bitcoin.com",
        None,
        "TCC",
        "Test Coins",
        "1000000",
        0,
        1,
    )
]

MAIN_GET_MINT_BATON_URL = "https://slpdb.fountainhead.cash/q/eyJ2IjogMywgInEiOiB7ImRiIjogWyJnIl0sICJhZ2dyZWdhdGUiOiBbeyIkbWF0Y2giOiB7ImdyYXBoVHhuLm91dHB1dHMiOiB7IiRlbGVtTWF0Y2giOiB7InN0YXR1cyI6ICJCQVRPTl9VTlNQRU5UIn19LCAidG9rZW5EZXRhaWxzLnRva2VuSWRIZXgiOiAiYWM3YmRjYTAxNjE3NTJjODBjMmM3ZGU2ZmI1Y2QxNDkwNTRhMDc4ZTZjZDRiNjM4MWFjYzIwMTZiOGZmMGU4ZCJ9fSwgeyIkdW53aW5kIjogIiRncmFwaFR4bi5vdXRwdXRzIn0sIHsiJG1hdGNoIjogeyJncmFwaFR4bi5vdXRwdXRzLnN0YXR1cyI6ICJCQVRPTl9VTlNQRU5UIn19LCB7IiRwcm9qZWN0IjogeyJhZGRyZXNzIjogIiRncmFwaFR4bi5vdXRwdXRzLmFkZHJlc3MiLCAidHhpZCI6ICIkZ3JhcGhUeG4udHhpZCIsICJ2b3V0IjogIiRncmFwaFR4bi5vdXRwdXRzLnZvdXQiLCAidG9rZW5JZCI6ICIkdG9rZW5EZXRhaWxzLnRva2VuSWRIZXgifX1dLCAibGltaXQiOiAxMH19"
MAIN_GET_MINT_BATON_RESPONSE = """
    {"g": [{"_id": "5fd8be0384e07624f24c1f2b", "address": "simpleledger:qq72px9d5he0ah87rrl8vg9y7gdl5kqguvrwa5w7jv", "txid": "ac7bdca0161752c80c2c7de6fb5cd149054a078e6cd4b6381acc2016b8ff0e8d", "vout": 2, "tokenId": "ac7bdca0161752c80c2c7de6fb5cd149054a078e6cd4b6381acc2016b8ff0e8d"}]}
    """
MAIN_GET_MINT_BATON_JSON = json.loads(MAIN_GET_MINT_BATON_RESPONSE)
MAIN_GET_MINT_BATON_RESULT = [
    (
        "simpleledger:qq72px9d5he0ah87rrl8vg9y7gdl5kqguvrwa5w7jv",
        "ac7bdca0161752c80c2c7de6fb5cd149054a078e6cd4b6381acc2016b8ff0e8d",
        2,
    )
]

TEST_GET_MINT_BATON_URL = "https://slpdb-testnet.fountainhead.cash/q/eyJ2IjogMywgInEiOiB7ImRiIjogWyJnIl0sICJhZ2dyZWdhdGUiOiBbeyIkbWF0Y2giOiB7ImdyYXBoVHhuLm91dHB1dHMiOiB7IiRlbGVtTWF0Y2giOiB7InN0YXR1cyI6ICJCQVRPTl9VTlNQRU5UIn19LCAidG9rZW5EZXRhaWxzLnRva2VuSWRIZXgiOiAiMTVjZDYyNTNjOGFjODM4YTRiOWY5OTE4ZmM4NGIwNDg0YTQ1YjY2MWE3OGNjYzU5N2E3NjUzYTBmYzE3NWQxZiJ9fSwgeyIkdW53aW5kIjogIiRncmFwaFR4bi5vdXRwdXRzIn0sIHsiJG1hdGNoIjogeyJncmFwaFR4bi5vdXRwdXRzLnN0YXR1cyI6ICJCQVRPTl9VTlNQRU5UIn19LCB7IiRwcm9qZWN0IjogeyJhZGRyZXNzIjogIiRncmFwaFR4bi5vdXRwdXRzLmFkZHJlc3MiLCAidHhpZCI6ICIkZ3JhcGhUeG4udHhpZCIsICJ2b3V0IjogIiRncmFwaFR4bi5vdXRwdXRzLnZvdXQiLCAidG9rZW5JZCI6ICIkdG9rZW5EZXRhaWxzLnRva2VuSWRIZXgifX1dLCAibGltaXQiOiAxMH19"
TEST_GET_MINT_BATON_RESPONSE = """
    {"g": [{"_id": "5fd9761f863a80b74964c51f", "address": "slptest:qz9y7ujr9ucavpdsywnykrxnlvds5nwxz5ly6hk5ck", "txid": "15cd6253c8ac838a4b9f9918fc84b0484a45b661a78ccc597a7653a0fc175d1f", "vout": 2, "tokenId": "15cd6253c8ac838a4b9f9918fc84b0484a45b661a78ccc597a7653a0fc175d1f"}]}
    """
TEST_GET_MINT_BATON_JSON = json.loads(TEST_GET_MINT_BATON_RESPONSE)
TEST_GET_MINT_BATON_RESULT = [
    (
        "slptest:qz9y7ujr9ucavpdsywnykrxnlvds5nwxz5ly6hk5ck",
        "15cd6253c8ac838a4b9f9918fc84b0484a45b661a78ccc597a7653a0fc175d1f",
        2,
    )
]

TEST_GET_MINT_BATON_BY_ADDRESS_URL = "https://slpdb-testnet.fountainhead.cash/q/eyJ2IjogMywgInEiOiB7ImRiIjogWyJnIl0sICJhZ2dyZWdhdGUiOiBbeyIkbWF0Y2giOiB7ImdyYXBoVHhuLm91dHB1dHMiOiB7IiRlbGVtTWF0Y2giOiB7InN0YXR1cyI6ICJCQVRPTl9VTlNQRU5UIn19fX0sIHsiJHVud2luZCI6ICIkZ3JhcGhUeG4ub3V0cHV0cyJ9LCB7IiRtYXRjaCI6IHsiZ3JhcGhUeG4ub3V0cHV0cy5zdGF0dXMiOiAiQkFUT05fVU5TUEVOVCIsICJncmFwaFR4bi5vdXRwdXRzLmFkZHJlc3MiOiAic2xwdGVzdDpxejl5N3Vqcjl1Y2F2cGRzeXdueWtyeG5sdmRzNW53eHo1bHk2aGs1Y2sifX0sIHsiJHByb2plY3QiOiB7ImFkZHJlc3MiOiAiJGdyYXBoVHhuLm91dHB1dHMuYWRkcmVzcyIsICJ0eGlkIjogIiRncmFwaFR4bi50eGlkIiwgInZvdXQiOiAiJGdyYXBoVHhuLm91dHB1dHMudm91dCIsICJ0b2tlbklkIjogIiR0b2tlbkRldGFpbHMudG9rZW5JZEhleCJ9fV0sICJsaW1pdCI6IDEwfX0="
TEST_GET_MINT_BATON_BY_ADDRESS_RESPONSE = """{"g":[{"_id":"5fd9749a863a80b74964c1cb","address":"slptest:qz9y7ujr9ucavpdsywnykrxnlvds5nwxz5ly6hk5ck","txid":"89ef48fb7d0d39be9ad748827f191d6197eba342c044185dad58295f75f8b8eb","vout":2,"tokenId":"89ef48fb7d0d39be9ad748827f191d6197eba342c044185dad58295f75f8b8eb"},{"_id":"5fd9761f863a80b74964c51f","address":"slptest:qz9y7ujr9ucavpdsywnykrxnlvds5nwxz5ly6hk5ck","txid":"15cd6253c8ac838a4b9f9918fc84b0484a45b661a78ccc597a7653a0fc175d1f","vout":2,"tokenId":"15cd6253c8ac838a4b9f9918fc84b0484a45b661a78ccc597a7653a0fc175d1f"}]}"""
TEST_GET_MINT_BATON_BY_ADDRESS_JSON = json.loads(
    TEST_GET_MINT_BATON_BY_ADDRESS_RESPONSE
)
TEST_GET_MINT_BATON_BY_ADDRESS_RESULT = [
    (
        "slptest:qz9y7ujr9ucavpdsywnykrxnlvds5nwxz5ly6hk5ck",
        "89ef48fb7d0d39be9ad748827f191d6197eba342c044185dad58295f75f8b8eb",
        2,
    ),
    (
        "slptest:qz9y7ujr9ucavpdsywnykrxnlvds5nwxz5ly6hk5ck",
        "15cd6253c8ac838a4b9f9918fc84b0484a45b661a78ccc597a7653a0fc175d1f",
        2,
    ),
]


MAIN_GET_TX_BY_OPRETURN_URL = "https://slpdb.fountainhead.cash/q/eyJ2IjogMywgInEiOiB7ImRiIjogWyJjIl0sICJhZ2dyZWdhdGUiOiBbeyIkbWF0Y2giOiB7Im91dCI6IHsiJGVsZW1NYXRjaCI6IHsic3RyIjogeyIkcmVnZXgiOiAiT1BfUkVUVVJOIDUzNGM1MDAwIDAxIDQ3NDU0ZTQ1NTM0OTUzIDU0NDM0MyA1NDY1NzM3NDIwNDM2ZjY5NmU3MyA2ZDY5NmU3NDJlNjI2OTc0NjM2ZjY5NmUyZTYzNmY2ZCAwMCAwMiAwMDAwMDAwMDAwMGY0MjQwIn19fX19LCB7IiRwcm9qZWN0IjogeyJfaWQiOiAiJF9pZCIsICJ0eGlkIjogIiR0eC5oIiwgInNscF9uYW1lIjogIiRzbHAuZGV0YWlsLm5hbWUiLCAic2xwX2Ftb3VudCI6ICIkc2xwLmRldGFpbC5vdXRwdXRzIiwgIm9wcmV0dXJucyI6ICIkb3V0LnN0ciJ9fV0sICJsaW1pdCI6IDEwfX0="
MAIN_GET_TX_BY_OPRETURN_RESPONSE = """
{"c": [{"_id": "5fd8c29d84e07624f24c4486", "txid": "ac7bdca0161752c80c2c7de6fb5cd149054a078e6cd4b6381acc2016b8ff0e8d", "slp_name": "Test Coins", "slp_amount": [{"address": "simpleledger:qq72px9d5he0ah87rrl8vg9y7gdl5kqguvrwa5w7jv", "amount": "1000000"}], "opreturns": ["OP_RETURN 534c5000 01 47454e45534953 544343 5465737420436f696e73 6d696e742e626974636f696e2e636f6d 00 02 00000000000f4240", "OP_DUP OP_HASH160 3ca098ada5f2fedcfe18fe7620a4f21bfa5808e3 OP_EQUALVERIFY OP_CHECKSIG", "OP_DUP OP_HASH160 3ca098ada5f2fedcfe18fe7620a4f21bfa5808e3 OP_EQUALVERIFY OP_CHECKSIG", "OP_DUP OP_HASH160 81bb5584c37bc85ba6f4e588ec2bb9a453bf70b4 OP_EQUALVERIFY OP_CHECKSIG"]}]}
"""
MAIN_GET_TX_BY_OPRETURN_JSON = json.loads(MAIN_GET_TX_BY_OPRETURN_RESPONSE)
MAIN_GET_TX_BY_OPRETURN_RESULT = [
    {
        "_id": "5fd8c29d84e07624f24c4486",
        "txid": "ac7bdca0161752c80c2c7de6fb5cd149054a078e6cd4b6381acc2016b8ff0e8d",
        "slp_name": "Test Coins",
        "slp_amount": [
            {
                "address": "simpleledger:qq72px9d5he0ah87rrl8vg9y7gdl5kqguvrwa5w7jv",
                "amount": "1000000",
            }
        ],
        "opreturns": [
            "OP_RETURN 534c5000 01 47454e45534953 544343 5465737420436f696e73 6d696e742e626974636f696e2e636f6d 00 02 00000000000f4240",
            "OP_DUP OP_HASH160 3ca098ada5f2fedcfe18fe7620a4f21bfa5808e3 OP_EQUALVERIFY OP_CHECKSIG",
            "OP_DUP OP_HASH160 3ca098ada5f2fedcfe18fe7620a4f21bfa5808e3 OP_EQUALVERIFY OP_CHECKSIG",
            "OP_DUP OP_HASH160 81bb5584c37bc85ba6f4e588ec2bb9a453bf70b4 OP_EQUALVERIFY OP_CHECKSIG",
        ],
    }
]

# TEST_GET_BATON_UTXO_URL = 'https://slpdb-testnet.fountainhead.cash/q/eyJ2IjogMywgInEiOiB7ImRiIjogWyJnIl0sICJhZ2dyZWdhdGUiOiBbeyIkbWF0Y2giOiB7ImdyYXBoVHhuLm91dHB1dHMiOiB7IiRlbGVtTWF0Y2giOiB7InN0YXR1cyI6ICJCQVRPTl9VTlNQRU5UIn19LCAidG9rZW5EZXRhaWxzLnRva2VuSWRIZXgiOiAiMTVjZDYyNTNjOGFjODM4YTRiOWY5OTE4ZmM4NGIwNDg0YTQ1YjY2MWE3OGNjYzU5N2E3NjUzYTBmYzE3NWQxZiJ9fSwgeyIkdW53aW5kIjogIiRncmFwaFR4bi5vdXRwdXRzIn0sIHsiJG1hdGNoIjogeyJncmFwaFR4bi5vdXRwdXRzLnN0YXR1cyI6ICJCQVRPTl9VTlNQRU5UIn19LCB7IiRwcm9qZWN0IjogeyJhZGRyZXNzIjogIiRncmFwaFR4bi5vdXRwdXRzLmFkZHJlc3MiLCAidHhpZCI6ICIkZ3JhcGhUeG4udHhpZCIsICJ2b3V0IjogIiRncmFwaFR4bi5vdXRwdXRzLnZvdXQiLCAidG9rZW5JZCI6ICIkdG9rZW5EZXRhaWxzLnRva2VuSWRIZXgifX1dLCAibGltaXQiOiAxMH19'
# TEST_GET_BATON_UTXO_RESPONSE = '''{"g":[{"_id":"5fd9761f863a80b74964c51f","address":"slptest:qz9y7ujr9ucavpdsywnykrxnlvds5nwxz5ly6hk5ck","txid":"15cd6253c8ac838a4b9f9918fc84b0484a45b661a78ccc597a7653a0fc175d1f","vout":2,"tokenId":"15cd6253c8ac838a4b9f9918fc84b0484a45b661a78ccc597a7653a0fc175d1f"}]}'''
# TEST_GET_BATON_UTXO_JSON = json.loads(TEST_GET_BATON_UTXO_RESPONSE)
# TEST_GET_BATON_UTXO_RESULT = [('slptest:qz9y7ujr9ucavpdsywnykrxnlvds5nwxz5ly6hk5ck',
#                             '15cd6253c8ac838a4b9f9918fc84b0484a45b661a78ccc597a7653a0fc175d1f',
#                             2)]

MAIN_GET_ALL_SLP_UTXOS_BY_ADDRESS_URL = "https://slpdb.fountainhead.cash/q/eyJ2IjogMywgInEiOiB7ImRiIjogWyJnIl0sICJhZ2dyZWdhdGUiOiBbeyIkbWF0Y2giOiB7ImdyYXBoVHhuLm91dHB1dHMiOiB7IiRlbGVtTWF0Y2giOiB7InN0YXR1cyI6ICJVTlNQRU5UIiwgInNscEFtb3VudCI6IHsiJGd0ZSI6IDB9fX19fSwgeyIkdW53aW5kIjogIiRncmFwaFR4bi5vdXRwdXRzIn0sIHsiJG1hdGNoIjogeyJncmFwaFR4bi5vdXRwdXRzLnN0YXR1cyI6ICJVTlNQRU5UIiwgImdyYXBoVHhuLm91dHB1dHMuc2xwQW1vdW50IjogeyIkZ3RlIjogMH19fSwgeyIkcHJvamVjdCI6IHsidG9rZW5fYmFsYW5jZSI6ICIkZ3JhcGhUeG4ub3V0cHV0cy5zbHBBbW91bnQiLCAiYWRkcmVzcyI6ICIkZ3JhcGhUeG4ub3V0cHV0cy5hZGRyZXNzIiwgInR4aWQiOiAiJGdyYXBoVHhuLnR4aWQiLCAidm91dCI6ICIkZ3JhcGhUeG4ub3V0cHV0cy52b3V0IiwgInRva2VuSWQiOiAiJHRva2VuRGV0YWlscy50b2tlbklkSGV4In19LCB7IiRtYXRjaCI6IHsiYWRkcmVzcyI6ICJzaW1wbGVsZWRnZXI6cXo5eTd1anI5dWNhdnBkc3l3bnlrcnhubHZkczVud3h6NXZlanNtNW5mIn19LCB7IiRzb3J0IjogeyJ0b2tlbl9iYWxhbmNlIjogLTF9fV0sICJsaW1pdCI6IDEwMH19"
MAIN_GET_ALL_SLP_UTXOS_BY_ADDRESS_RESPONSE = """{"g":[{"_id":"5fd8be2684e07624f24c20db","token_balance":"50000","address":"simpleledger:qz9y7ujr9ucavpdsywnykrxnlvds5nwxz5vejsm5nf","txid":"8a99eba84ca4a2af8b106252e845d69bb6b577a16895234878982a5b70a65a68","vout":1,"tokenId":"ac7bdca0161752c80c2c7de6fb5cd149054a078e6cd4b6381acc2016b8ff0e8d"}]}"""
MAIN_GET_ALL_SLP_UTXOS_BY_ADDRESS_JSON = json.loads(
    MAIN_GET_ALL_SLP_UTXOS_BY_ADDRESS_RESPONSE
)
MAIN_GET_ALL_SLP_UTXOS_BY_ADDRESS_RESULT = [
    (
        "50000",
        "simpleledger:qz9y7ujr9ucavpdsywnykrxnlvds5nwxz5vejsm5nf",
        "8a99eba84ca4a2af8b106252e845d69bb6b577a16895234878982a5b70a65a68",
        1,
    )
]

MAIN_GET_UTXO_BY_TOKENID_URL = "https://slpdb.fountainhead.cash/q/eyJ2IjogMywgInEiOiB7ImRiIjogWyJnIl0sICJhZ2dyZWdhdGUiOiBbeyIkbWF0Y2giOiB7ImdyYXBoVHhuLm91dHB1dHMiOiB7IiRlbGVtTWF0Y2giOiB7InN0YXR1cyI6ICJVTlNQRU5UIiwgInNscEFtb3VudCI6IHsiJGd0ZSI6IDB9fX0sICJ0b2tlbkRldGFpbHMudG9rZW5JZEhleCI6ICJhYzdiZGNhMDE2MTc1MmM4MGMyYzdkZTZmYjVjZDE0OTA1NGEwNzhlNmNkNGI2MzgxYWNjMjAxNmI4ZmYwZThkIn19LCB7IiR1bndpbmQiOiAiJGdyYXBoVHhuLm91dHB1dHMifSwgeyIkbWF0Y2giOiB7ImdyYXBoVHhuLm91dHB1dHMuc3RhdHVzIjogIlVOU1BFTlQiLCAiZ3JhcGhUeG4ub3V0cHV0cy5zbHBBbW91bnQiOiB7IiRndGUiOiAwfSwgInRva2VuRGV0YWlscy50b2tlbklkSGV4IjogImFjN2JkY2EwMTYxNzUyYzgwYzJjN2RlNmZiNWNkMTQ5MDU0YTA3OGU2Y2Q0YjYzODFhY2MyMDE2YjhmZjBlOGQifX0sIHsiJHByb2plY3QiOiB7InRva2VuX2JhbGFuY2UiOiAiJGdyYXBoVHhuLm91dHB1dHMuc2xwQW1vdW50IiwgImFkZHJlc3MiOiAiJGdyYXBoVHhuLm91dHB1dHMuYWRkcmVzcyIsICJ0eGlkIjogIiRncmFwaFR4bi50eGlkIiwgInZvdXQiOiAiJGdyYXBoVHhuLm91dHB1dHMudm91dCIsICJ0b2tlbklkIjogIiR0b2tlbkRldGFpbHMudG9rZW5JZEhleCJ9fSwgeyIkbWF0Y2giOiB7ImFkZHJlc3MiOiAic2ltcGxlbGVkZ2VyOnF6OXk3dWpyOXVjYXZwZHN5d255a3J4bmx2ZHM1bnd4ejV2ZWpzbTVuZiJ9fSwgeyIkc29ydCI6IHsidG9rZW5fYmFsYW5jZSI6IC0xfX1dLCAibGltaXQiOiAxMDB9fQ=="
MAIN_GET_UTXO_BY_TOKENID_RESPONSE = """{"g":[{"_id":"5fd8be2684e07624f24c20db","token_balance":"50000","address":"simpleledger:qz9y7ujr9ucavpdsywnykrxnlvds5nwxz5vejsm5nf","txid":"8a99eba84ca4a2af8b106252e845d69bb6b577a16895234878982a5b70a65a68","vout":1,"tokenId":"ac7bdca0161752c80c2c7de6fb5cd149054a078e6cd4b6381acc2016b8ff0e8d"}]}"""
MAIN_GET_UTXO_BY_TOKENID_JSON = json.loads(MAIN_GET_UTXO_BY_TOKENID_RESPONSE)
MAIN_GET_UTXO_BY_TOKENID_RESULT = [
    (
        "50000",
        "simpleledger:qz9y7ujr9ucavpdsywnykrxnlvds5nwxz5vejsm5nf",
        "8a99eba84ca4a2af8b106252e845d69bb6b577a16895234878982a5b70a65a68",
        1,
    )
]

MAIN_GET_CHILD_NFT_BY_PARENT_TOKENID_URL = "https://slpdb.fountainhead.cash/q/eyJ2IjogMywgInEiOiB7ImRiIjogWyJ0Il0sICJhZ2dyZWdhdGUiOiBbeyIkbWF0Y2giOiB7Im5mdFBhcmVudElkIjogImI2NDFhNGM3ZWZjNGY4MTczOWY4NGJlN2VkYThlMGM4OWYzZTAzMzhmMTA3ZmRmZTY0NzIzNjgxOWZkNjJlZDIifX0sIHsiJHNvcnQiOiB7InRva2VuU3RhdHMuYmxvY2tfY3JlYXRlZCI6IC0xfX0sIHsiJHNraXAiOiAwfSwgeyIkbGltaXQiOiAxfV19fQ=="
MAIN_GET_CHILD_NFT_BY_PARENT_TOKENID_RESPONSE = """{"t":[{"_id":"5fd144d3c7ab823fae924c78","schema_version":79,"lastUpdatedBlock":665034,"tokenDetails":{"decimals":0,"tokenIdHex":"5745f6d0c91efbb49eb427255093171af36c498b2011eefb0071c0a6fe9d9844","timestamp":"2020-12-08 18:33:48","timestamp_unix":1607452428,"transactionType":"GENESIS","versionType":65,"documentUri":"https://collectible.staging.sweet.io/series/306/18867","documentSha256Hex":"5e48db67860185b107372e4322bfb5e6afe152e4b21796b6f7ba58abfa2b3140","symbol":"SWEDC","name":"Autumn Nights Tour V2 No. 18867","batonVout":null,"containsBaton":false,"genesisOrMintQuantity":"1","sendOutputs":null},"mintBatonUtxo":"","mintBatonStatus":"DEAD_ENDED","tokenStats":{"block_created":665034,"approx_txns_since_genesis":0},"_pruningState":{"pruneHeight":0,"sendCount":0,"mintCount":0},"nftParentId":"b641a4c7efc4f81739f84be7eda8e0c89f3e0338f107fdfe647236819fd62ed2"}]}"""
MAIN_GET_CHILD_NFT_BY_PARENT_TOKENID_JSON = json.loads(
    MAIN_GET_CHILD_NFT_BY_PARENT_TOKENID_RESPONSE
)
MAIN_GET_CHILD_NFT_BY_PARENT_TOKENID_RESULT = [
    (
        "5745f6d0c91efbb49eb427255093171af36c498b2011eefb0071c0a6fe9d9844",
        "https://collectible.staging.sweet.io/series/306/18867",
        "5e48db67860185b107372e4322bfb5e6afe152e4b21796b6f7ba58abfa2b3140",
        "SWEDC",
        "Autumn Nights Tour V2 No. 18867",
        "1",
        0,
        65,
    )
]

FILTER_SLP_UTXOS_URL = "https://slpdb-testnet.fountainhead.cash/q/eyJ2IjogMywgInEiOiB7ImRiIjogWyJnIl0sICJhZ2dyZWdhdGUiOiBbeyIkbWF0Y2giOiB7ImdyYXBoVHhuLm91dHB1dHMiOiB7IiRlbGVtTWF0Y2giOiB7InN0YXR1cyI6ICJVTlNQRU5UIiwgInNscEFtb3VudCI6IHsiJGd0ZSI6IDB9fX19fSwgeyIkdW53aW5kIjogIiRncmFwaFR4bi5vdXRwdXRzIn0sIHsiJG1hdGNoIjogeyJncmFwaFR4bi5vdXRwdXRzLnN0YXR1cyI6ICJVTlNQRU5UIiwgImdyYXBoVHhuLm91dHB1dHMuc2xwQW1vdW50IjogeyIkZ3RlIjogMH19fSwgeyIkcHJvamVjdCI6IHsidG9rZW5fYmFsYW5jZSI6ICIkZ3JhcGhUeG4ub3V0cHV0cy5zbHBBbW91bnQiLCAiYWRkcmVzcyI6ICIkZ3JhcGhUeG4ub3V0cHV0cy5hZGRyZXNzIiwgInR4aWQiOiAiJGdyYXBoVHhuLnR4aWQiLCAidm91dCI6ICIkZ3JhcGhUeG4ub3V0cHV0cy52b3V0IiwgInRva2VuSWQiOiAiJHRva2VuRGV0YWlscy50b2tlbklkSGV4In19LCB7IiRtYXRjaCI6IHsiYWRkcmVzcyI6ICJzbHB0ZXN0OnF6OXk3dWpyOXVjYXZwZHN5d255a3J4bmx2ZHM1bnd4ejVseTZoazVjayJ9fSwgeyIkc29ydCI6IHsidG9rZW5fYmFsYW5jZSI6IC0xfX1dLCAibGltaXQiOiAxMDB9fQ=="
FILTER_SLP_UTXOS_RESPONSE = """{"g":[{"_id":"5fdad4d7863a80b74967c349","token_balance":"999998","address":"slptest:qz9y7ujr9ucavpdsywnykrxnlvds5nwxz5ly6hk5ck","txid":"ebe4d53b26bdef8ddea7a55609c99cda5aaaa2c2909baefaa2bd295479c740ef","vout":2,"tokenId":"15cd6253c8ac838a4b9f9918fc84b0484a45b661a78ccc597a7653a0fc175d1f"},{"_id":"5fdf5bfe863a80b749713cbc","token_balance":"1000","address":"slptest:qz9y7ujr9ucavpdsywnykrxnlvds5nwxz5ly6hk5ck","txid":"c1613a5224fb3dc489817b81ef8c0179e8fcf9d016d00799fc60591ec305001f","vout":1,"tokenId":"c1613a5224fb3dc489817b81ef8c0179e8fcf9d016d00799fc60591ec305001f"},{"_id":"5fe06819863a80b7497372cf","token_balance":"1","address":"slptest:qz9y7ujr9ucavpdsywnykrxnlvds5nwxz5ly6hk5ck","txid":"ff7febe4abaf15771c9e5f402fdb3508810084d951f896d2470f42f57def07b4","vout":1,"tokenId":"89ef48fb7d0d39be9ad748827f191d6197eba342c044185dad58295f75f8b8eb"},{"_id":"5fe06819863a80b7497372cf","token_balance":"99","address":"slptest:qz9y7ujr9ucavpdsywnykrxnlvds5nwxz5ly6hk5ck","txid":"ff7febe4abaf15771c9e5f402fdb3508810084d951f896d2470f42f57def07b4","vout":2,"tokenId":"89ef48fb7d0d39be9ad748827f191d6197eba342c044185dad58295f75f8b8eb"}]}"""
FILTER_SLP_UTXOS_JSON = json.loads(FILTER_SLP_UTXOS_RESPONSE)

FILTER_BATON_URL = "https://slpdb-testnet.fountainhead.cash/q/eyJ2IjogMywgInEiOiB7ImRiIjogWyJnIl0sICJhZ2dyZWdhdGUiOiBbeyIkbWF0Y2giOiB7ImdyYXBoVHhuLm91dHB1dHMiOiB7IiRlbGVtTWF0Y2giOiB7InN0YXR1cyI6ICJCQVRPTl9VTlNQRU5UIn19fX0sIHsiJHVud2luZCI6ICIkZ3JhcGhUeG4ub3V0cHV0cyJ9LCB7IiRtYXRjaCI6IHsiZ3JhcGhUeG4ub3V0cHV0cy5zdGF0dXMiOiAiQkFUT05fVU5TUEVOVCIsICJncmFwaFR4bi5vdXRwdXRzLmFkZHJlc3MiOiAic2xwdGVzdDpxejl5N3Vqcjl1Y2F2cGRzeXdueWtyeG5sdmRzNW53eHo1bHk2aGs1Y2sifX0sIHsiJHByb2plY3QiOiB7ImFkZHJlc3MiOiAiJGdyYXBoVHhuLm91dHB1dHMuYWRkcmVzcyIsICJ0eGlkIjogIiRncmFwaFR4bi50eGlkIiwgInZvdXQiOiAiJGdyYXBoVHhuLm91dHB1dHMudm91dCIsICJ0b2tlbklkIjogIiR0b2tlbkRldGFpbHMudG9rZW5JZEhleCJ9fV0sICJsaW1pdCI6IDEwfX0="
FILTER_BATON_RESPONSE = """{"g":[{"_id":"5fd9749a863a80b74964c1cb","address":"slptest:qz9y7ujr9ucavpdsywnykrxnlvds5nwxz5ly6hk5ck","txid":"89ef48fb7d0d39be9ad748827f191d6197eba342c044185dad58295f75f8b8eb","vout":2,"tokenId":"89ef48fb7d0d39be9ad748827f191d6197eba342c044185dad58295f75f8b8eb"}]}"""
FILTER_BATON_JSON = json.loads(FILTER_BATON_RESPONSE)

FILTER_UNSPENTS = [
    Unspent(
        amount=546,
        confirmations=-1,
        script="76a9148a4f72432f31d605b023a64b0cd3fb1b0a4dc61588ac",
        txid="ff7febe4abaf15771c9e5f402fdb3508810084d951f896d2470f42f57def07b4",
        txindex=1,
    ),
    Unspent(
        amount=546,
        confirmations=-1,
        script="76a9148a4f72432f31d605b023a64b0cd3fb1b0a4dc61588ac",
        txid="ff7febe4abaf15771c9e5f402fdb3508810084d951f896d2470f42f57def07b4",
        txindex=2,
    ),
    Unspent(
        amount=992018,
        confirmations=-1,
        script="76a9148a4f72432f31d605b023a64b0cd3fb1b0a4dc61588ac",
        txid="ff7febe4abaf15771c9e5f402fdb3508810084d951f896d2470f42f57def07b4",
        txindex=3,
    ),
    Unspent(
        amount=546,
        confirmations=-1,
        script="76a9148a4f72432f31d605b023a64b0cd3fb1b0a4dc61588ac",
        txid="c1613a5224fb3dc489817b81ef8c0179e8fcf9d016d00799fc60591ec305001f",
        txindex=1,
    ),
    Unspent(
        amount=546,
        confirmations=-1,
        script="76a9148a4f72432f31d605b023a64b0cd3fb1b0a4dc61588ac",
        txid="ebe4d53b26bdef8ddea7a55609c99cda5aaaa2c2909baefaa2bd295479c740ef",
        txindex=2,
    ),
    Unspent(
        amount=546,
        confirmations=-1,
        script="76a9148a4f72432f31d605b023a64b0cd3fb1b0a4dc61588ac",
        txid="89ef48fb7d0d39be9ad748827f191d6197eba342c044185dad58295f75f8b8eb",
        txindex=2,
    ),
]
FILTER_RESULT_SLP_UTXOS = [
    Unspent(
        amount=546,
        confirmations=-1,
        script="76a9148a4f72432f31d605b023a64b0cd3fb1b0a4dc61588ac",
        txid="ff7febe4abaf15771c9e5f402fdb3508810084d951f896d2470f42f57def07b4",
        txindex=1,
    ),
    Unspent(
        amount=546,
        confirmations=-1,
        script="76a9148a4f72432f31d605b023a64b0cd3fb1b0a4dc61588ac",
        txid="ff7febe4abaf15771c9e5f402fdb3508810084d951f896d2470f42f57def07b4",
        txindex=2,
    ),
    Unspent(
        amount=546,
        confirmations=-1,
        script="76a9148a4f72432f31d605b023a64b0cd3fb1b0a4dc61588ac",
        txid="c1613a5224fb3dc489817b81ef8c0179e8fcf9d016d00799fc60591ec305001f",
        txindex=1,
    ),
    Unspent(
        amount=546,
        confirmations=-1,
        script="76a9148a4f72432f31d605b023a64b0cd3fb1b0a4dc61588ac",
        txid="ebe4d53b26bdef8ddea7a55609c99cda5aaaa2c2909baefaa2bd295479c740ef",
        txindex=2,
    ),
]
FILTER_RESULT_UNSPENT = [
    Unspent(
        amount=992018,
        confirmations=-1,
        script="76a9148a4f72432f31d605b023a64b0cd3fb1b0a4dc61588ac",
        txid="ff7febe4abaf15771c9e5f402fdb3508810084d951f896d2470f42f57def07b4",
        txindex=3,
    )
]
FILTER_RESULT_BATON = [
    Unspent(
        amount=546,
        confirmations=-1,
        script="76a9148a4f72432f31d605b023a64b0cd3fb1b0a4dc61588ac",
        txid="89ef48fb7d0d39be9ad748827f191d6197eba342c044185dad58295f75f8b8eb",
        txindex=2,
    )
]


# class MockBackend(SlpAPI):
#     # TODO add error codes
#     # IGNORED_ERRORS = NetworkAPI.IGNORED_ERRORS
#     SLP_MAIN_ENDPOINT = "raise_connection_error"
#     SLP_TEST_ENDPOINT = "raise_connection_error"
#     SLP_REG_ENDPOINT = "raise_connection_error"


def mocked_requests_get(*args, **kwargs):
    class MockResponse:
        def __init__(self, json_data, status_code):
            self.json_data = json_data
            self.status_code = status_code

        def json(self):
            return self.json_data

    if kwargs["url"] == MAIN_GET_BALANCE_URL:
        return MockResponse(MAIN_GET_BALANCE_JSON, 200)
    elif kwargs["url"] == MAIN_GET_TOKEN_BY_ID_URL:
        return MockResponse(MAIN_GET_TOKEN_BY_ID_JSON, 200)
    elif kwargs["url"] == MAIN_GET_MINT_BATON_URL:
        return MockResponse(MAIN_GET_MINT_BATON_JSON, 200)
    elif kwargs["url"] == TEST_GET_MINT_BATON_URL:
        return MockResponse(TEST_GET_MINT_BATON_JSON, 200)
    elif kwargs["url"] == MAIN_GET_TX_BY_OPRETURN_URL:
        return MockResponse(MAIN_GET_TX_BY_OPRETURN_JSON, 200)
    elif kwargs["url"] == MAIN_GET_ALL_SLP_UTXOS_BY_ADDRESS_URL:
        return MockResponse(MAIN_GET_ALL_SLP_UTXOS_BY_ADDRESS_JSON, 200)
    elif kwargs["url"] == MAIN_GET_UTXO_BY_TOKENID_URL:
        return MockResponse(MAIN_GET_UTXO_BY_TOKENID_JSON, 200)
    elif kwargs["url"] == MAIN_GET_CHILD_NFT_BY_PARENT_TOKENID_URL:
        return MockResponse(MAIN_GET_CHILD_NFT_BY_PARENT_TOKENID_JSON, 200)
    elif kwargs["url"] == TEST_GET_MINT_BATON_BY_ADDRESS_URL:
        return MockResponse(TEST_GET_MINT_BATON_BY_ADDRESS_JSON, 200)
    elif kwargs["url"] == FILTER_SLP_UTXOS_URL:
        return MockResponse(FILTER_SLP_UTXOS_JSON, 200)
    elif kwargs["url"] == FILTER_BATON_URL:
        return MockResponse(FILTER_BATON_URL, 200)

    return MockResponse(None, 404)


def mocked_connection_error(url, timeout):
    raise ConnectionError


class TestSlpAPI(unittest.TestCase):

    # def test_get_slp_balance_test_equal(self):
    #     results = SlpAPI.get_balance(TEST_SLP_ADDRESS_USED, network=TEST)
    #     assert results[0][0] == TESTNET_COIN_NAME
    #     assert int(results[0][1]) >= 50000

    # def test_get_slp_balance_test_failure(self):
    #     with pytest.raises(ConnectionError):
    #         MockBackend.get_balance(TEST_SLP_ADDRESS_USED, network=TEST)

    @mock.patch("requests.get", side_effect=mocked_requests_get)
    def test_get_balance_main_token_equal(self, mock_get):
        results = SlpAPI.get_balance(
            MAIN_SLP_ADDRESS_USED, tokenId=MAIN_TEST_COIN_TOKENID, network=MAIN
        )
        assert results == MAIN_GET_BALANCE

    @mock.patch("requests.get", side_effect=mocked_connection_error)
    def test_get_balance_main_token_failure(self, mock_get):
        with pytest.raises(ConnectionError):
            SlpAPI.get_balance(
                MAIN_SLP_ADDRESS_USED, tokenId=MAIN_TEST_COIN_TOKENID, network=MAIN
            )

    @mock.patch("requests.get", side_effect=mocked_requests_get)
    def test_get_token_by_id(self, mock_get):
        results = SlpAPI.get_token_by_id(MAIN_TEST_COIN_TOKENID, network=MAIN)
        assert results == MAIN__GET_TOKEN_BY_ID_RESULT

    @mock.patch("requests.get", side_effect=mocked_connection_error)
    def test_get_token_by_id_failure(self, mock_get):
        with pytest.raises(ConnectionError):
            SlpAPI.get_token_by_id(MAIN_TEST_COIN_TOKENID, network=MAIN)

    @mock.patch("requests.get", side_effect=mocked_requests_get)
    def test_get_mint_baton_utxo(self, mock_get):
        results = SlpAPI.get_mint_baton(tokenId=MAIN_TEST_COIN_TOKENID, network=MAIN)
        assert results == MAIN_GET_MINT_BATON_RESULT

    @mock.patch("requests.get", side_effect=mocked_connection_error)
    def test_get_mint_baton_utxo_failure(self, mock_get):
        with pytest.raises(ConnectionError):
            SlpAPI.get_mint_baton(tokenId=MAIN_TEST_COIN_TOKENID, network=MAIN)

    @mock.patch("requests.get", side_effect=mocked_requests_get)
    def test_get_mint_baton_utxo_testnet(self, mock_get):
        results = SlpAPI.get_mint_baton(tokenId=TESTNET_TEST_COIN_TOKENID, network=TEST)
        assert results == TEST_GET_MINT_BATON_RESULT

    @mock.patch("requests.get", side_effect=mocked_connection_error)
    def test_get_mint_baton_utxo_testnet_failure(self, mock_get):
        with pytest.raises(ConnectionError):
            SlpAPI.get_mint_baton(tokenId=TESTNET_TEST_COIN_TOKENID, network=TEST)

    @mock.patch("requests.get", side_effect=mocked_requests_get)
    def test_get_tx_by_op_return(self, mock_get):
        results = SlpAPI.get_tx_by_opreturn(
            op_return_segment=MAIN_OP_RETURN, network=MAIN
        )
        assert results == MAIN_GET_TX_BY_OPRETURN_RESULT

    @mock.patch("requests.get", side_effect=mocked_connection_error)
    def test_get_tx_by_op_return_failure(self, mock_get):
        with pytest.raises(ConnectionError):
            SlpAPI.get_tx_by_opreturn(MAIN_OP_RETURN)

    @mock.patch("requests.get", side_effect=mocked_requests_get)
    def test_get_all_slp_utxos_by_address_equal(self, mock_get):
        results = SlpAPI.get_all_slp_utxo_by_address(
            MAIN_SLP_ADDRESS_USED, network=MAIN
        )
        assert results == MAIN_GET_ALL_SLP_UTXOS_BY_ADDRESS_RESULT

    @mock.patch("requests.get", side_effect=mocked_connection_error)
    def test_get_all_slp_utxos_by_address_failure(self, mock_get):
        with pytest.raises(ConnectionError):
            SlpAPI.get_all_slp_utxo_by_address(MAIN_SLP_ADDRESS_USED, network=MAIN)

    @mock.patch("requests.get", side_effect=mocked_requests_get)
    def test_get_utxo_by_tokenId(self, mock_get):
        results = SlpAPI.get_utxo_by_tokenId(
            address=MAIN_SLP_ADDRESS_USED, tokenId=MAIN_TEST_COIN_TOKENID, network=MAIN
        )
        assert results == MAIN_GET_UTXO_BY_TOKENID_RESULT

    @mock.patch("requests.get", side_effect=mocked_connection_error)
    def test_get_utxo_by_tokenId_failure(self, mock_get):
        with pytest.raises(ConnectionError):
            SlpAPI.get_utxo_by_tokenId(
                MAIN_SLP_ADDRESS_USED, MAIN_TEST_COIN_TOKENID, network=MAIN
            )

    @mock.patch("requests.get", side_effect=mocked_requests_get)
    def test_get_child_nft_by_parent_tokenid(self, mock_get):
        results = SlpAPI.get_child_nft_by_parent_tokenId(
            tokenId=MAIN_TEMPORARY_GROUP_NFT_TEST_COIN_TOKENID, network=MAIN, limit=1
        )
        assert results == MAIN_GET_CHILD_NFT_BY_PARENT_TOKENID_RESULT

    @mock.patch("requests.get", side_effect=mocked_connection_error)
    def test_get_child_nft_by_parent_tokenid_failure(self, mock_get):
        with pytest.raises(ConnectionError):
            SlpAPI.get_child_nft_by_parent_tokenId(
                tokenId=MAIN_TEMPORARY_GROUP_NFT_TEST_COIN_TOKENID,
                network=MAIN,
                limit=1,
            )

    @mock.patch("requests.get", side_effect=mocked_requests_get)
    def test_get_mint_baton_by_address(self, mock_get):
        results = SlpAPI.get_mint_baton(address=TESTNET_BATON_ADDRESS, network=TEST)
        assert results == TEST_GET_MINT_BATON_BY_ADDRESS_RESULT

    @mock.patch("requests.get", side_effect=mocked_connection_error)
    def test_get_mint_baton_by_address_failure(self, mock_get):
        with pytest.raises(ConnectionError):
            SlpAPI.get_mint_baton(address=TESTNET_BATON_ADDRESS, network=TEST)

    @mock.patch("requests.get", side_effect=mocked_requests_get)
    def test_filter(self, mock_get):
        private_key = PrivateKeyTestnet(WALLET_FORMAT_TEST_SLP)
        private_key.unspents[:] = FILTER_UNSPENTS

        results = SlpAPI.filter_slp_txid(
            private_key.address,
            private_key.slp_address,
            private_key.unspents,
            network=NETWORKS[private_key._network]
        )
        assert results["difference"] == FILTER_RESULT_UNSPENT
        assert results["slp_utxos"] == FILTER_RESULT_SLP_UTXOS
        assert results["baton"] == FILTER_RESULT_BATON

    @mock.patch("requests.get", side_effect=mocked_connection_error)
    def test_filter_failure(self, mock_get):
        private_key = PrivateKeyTestnet(WALLET_FORMAT_TEST_SLP)
        with pytest.raises(ConnectionError):
            SlpAPI.filter_slp_txid(
                private_key.address,
                private_key.slp_address,
                private_key.unspents,
                network=NETWORKS[private_key._network]
            )
