import logging
import json

import requests
import base64
from decimal import Decimal

from bitcash.network import currency_to_satoshi, NetworkAPI
from bitcash.network.meta import Unspent
from bitcash.network.transaction import Transaction, TxPart

DEFAULT_TIMEOUT = 30

BCH_TO_SAT_MULTIPLIER = 100000000


class SlpAPI:
    SLP_MAIN_ENDPOINT = "https://slpdb.fountainhead.cash/q/"
    SLP_TEST_ENDPOINT = "https://slpdb-testnet.fountainhead.cash/q/"
    SLP_REG_ENDPOINT = "http://localhost:12300/q/"

    @classmethod
    def query_to_url(cls, query, network):
        query_to_string = json.dumps(query)
        b64 = base64.b64encode(query_to_string.encode("utf-8"))
        path = str(b64)
        path = path[2:-1]

        if network == "mainnet":
            url = cls.SLP_MAIN_ENDPOINT + path
        elif network == "testnet":
            url = cls.SLP_TEST_ENDPOINT + path
        elif network == "regtest":
            url = cls.SLP_REG_ENDPOINT + path
        else:
            raise ValueError('"{}" is an invalid path')

        return url

    @classmethod
    def get_balance(cls, address, tokenId=None, network="mainnet", limit=100, skip=0):

        if tokenId:
            query = {
                "v": 3,
                "q": {
                    "db": ["g"],
                    "aggregate": [
                        {"$match": {"graphTxn.outputs.address": address}},
                        {"$unwind": "$graphTxn.outputs"},
                        {
                            "$match": {
                                "graphTxn.outputs.status": "UNSPENT",
                                "graphTxn.outputs.address": address,
                            }
                        },
                        {
                            "$group": {
                                "_id": "$tokenDetails.tokenIdHex",
                                "slpAmount": {"$sum": "$graphTxn.outputs.slpAmount"},
                            }
                        },
                        {"$sort": {"slpAmount": -1}},
                        {"$match": {"slpAmount": {"$gt": 0}}},
                        {
                            "$lookup": {
                                "from": "tokens",
                                "localField": "_id",
                                "foreignField": "tokenDetails.tokenIdHex",
                                "as": "token",
                            }
                        },
                        {"$match": {"_id": tokenId}},
                    ],
                    "sort": {"slpAmount": -1},
                    "skip": 0,
                    "limit": 10,
                },
            }

            path = cls.query_to_url(query, network)
            get_balance_response = requests.get(url=path, timeout=DEFAULT_TIMEOUT)

            # Check response json size to determine if empty response, prevents
            # throwing error if calling index of empty array.
            if len(get_balance_response.json()) > 0:
                get_balance_json = get_balance_response.json()["g"]
                return [
                    (token["token"][0]["tokenDetails"]["name"], token["slpAmount"])
                    for token in get_balance_json
                ]
            else:
                return []

        else:
            query = {
                "v": 3,
                "q": {
                    "db": ["g"],
                    "aggregate": [
                        {"$match": {"graphTxn.outputs.address": address}},
                        {"$unwind": "$graphTxn.outputs"},
                        {
                            "$match": {
                                "graphTxn.outputs.status": "UNSPENT",
                                "graphTxn.outputs.address": address,
                            }
                        },
                        {
                            "$group": {
                                "_id": "$tokenDetails.tokenIdHex",
                                "slpAmount": {"$sum": "$graphTxn.outputs.slpAmount"},
                            }
                        },
                        {"$sort": {"slpAmount": -1}},
                        {"$match": {"slpAmount": {"$gt": 0}}},
                        {
                            "$lookup": {
                                "from": "tokens",
                                "localField": "_id",
                                "foreignField": "tokenDetails.tokenIdHex",
                                "as": "token",
                            }
                        },
                    ],
                    "sort": {"slpAmount": -1},
                    "skip": skip,
                    "limit": limit,
                },
            }

        path = cls.query_to_url(query, network)
        get_balance_response = requests.get(url=path, timeout=DEFAULT_TIMEOUT)

        # Check response json size to determine if empty response, prevents
        # throwing error if calling index of empty array.
        if len(get_balance_response.json()) > 0:
            get_balance_json = get_balance_response.json()["g"]
            return [
                (token["token"][0]["tokenDetails"]["name"], token["slpAmount"])
                for token in get_balance_json
            ]
        else:
            return []

    @classmethod
    def get_token_by_id(cls, tokenid, network="mainnet"):
        query = {
            "v": 3,
            "q": {
                "db": ["t"],
                "find": {"$query": {"tokenDetails.tokenIdHex": tokenid}},
                "project": {"tokenDetails": 1, "tokenStats": 1, "_id": 0},
                "limit": 1000,
            },
        }

        path = cls.query_to_url(query, network)
        get_token_response = requests.get(url=path, timeout=DEFAULT_TIMEOUT)
        get_token_json = get_token_response.json()["t"]

        return [
            (
                token["tokenDetails"]["tokenIdHex"],
                token["tokenDetails"]["documentUri"],
                token["tokenDetails"]["documentSha256Hex"],
                token["tokenDetails"]["symbol"],
                token["tokenDetails"]["name"],
                token["tokenDetails"]["genesisOrMintQuantity"],
                token["tokenDetails"]["decimals"],
                token["tokenDetails"]["versionType"],
            )
            for token in get_token_json
        ]

    @classmethod
    def get_utxo_by_tokenId(cls, address, tokenId, network="mainnet", limit=100):

        query = {
            "v": 3,
            "q": {
                "db": ["g"],
                "aggregate": [
                    {
                        "$match": {
                            "graphTxn.outputs": {
                                "$elemMatch": {
                                    "status": "UNSPENT",
                                    "slpAmount": {"$gte": 0},
                                }
                            },
                            "tokenDetails.tokenIdHex": tokenId,
                        }
                    },
                    {"$unwind": "$graphTxn.outputs"},
                    {
                        "$match": {
                            "graphTxn.outputs.status": "UNSPENT",
                            "graphTxn.outputs.slpAmount": {"$gte": 0},
                            "tokenDetails.tokenIdHex": tokenId,
                        }
                    },
                    {
                        "$project": {
                            "token_balance": "$graphTxn.outputs.slpAmount",
                            "address": "$graphTxn.outputs.address",
                            "txid": "$graphTxn.txid",
                            "vout": "$graphTxn.outputs.vout",
                            "tokenId": "$tokenDetails.tokenIdHex",
                        }
                    },
                    {"$match": {"address": address}},
                    {"$sort": {"token_balance": -1}},
                ],
                "limit": limit,
            },
        }

        path = cls.query_to_url(query, network)
        get_utxo_response = requests.get(url=path, timeout=DEFAULT_TIMEOUT)
        get_utxo_json = get_utxo_response.json()["g"]

        return [
            (utxo["token_balance"], utxo["address"], utxo["txid"], utxo["vout"])
            for utxo in get_utxo_json
        ]

    @classmethod
    def get_all_slp_utxo_by_address(cls, address, network="mainnet", limit=100):

        query = {
            "v": 3,
            "q": {
                "db": ["g"],
                "aggregate": [
                    {
                        "$match": {
                            "graphTxn.outputs": {
                                "$elemMatch": {
                                    "status": "UNSPENT",
                                    "slpAmount": {"$gte": 0},
                                }
                            }
                        }
                    },
                    {"$unwind": "$graphTxn.outputs"},
                    {
                        "$match": {
                            "graphTxn.outputs.status": "UNSPENT",
                            "graphTxn.outputs.slpAmount": {"$gte": 0},
                        }
                    },
                    {
                        "$project": {
                            "token_balance": "$graphTxn.outputs.slpAmount",
                            "address": "$graphTxn.outputs.address",
                            "txid": "$graphTxn.txid",
                            "vout": "$graphTxn.outputs.vout",
                            "tokenId": "$tokenDetails.tokenIdHex",
                        }
                    },
                    {"$match": {"address": address}},
                    {"$sort": {"token_balance": -1}},
                ],
                "limit": limit,
            },
        }

        path = cls.query_to_url(query, network)
        slp_utxo_response = requests.get(url=path, timeout=DEFAULT_TIMEOUT)
        slp_utxo_json = slp_utxo_response.json()["g"]

        return [
            (utxo["token_balance"], utxo["address"], utxo["txid"], utxo["vout"])
            for utxo in slp_utxo_json
        ]

    @classmethod
    def get_mint_baton(cls, tokenId=None, address=None, network="mainnet", limit=10):

        if tokenId:
            query = {
                "v": 3,
                "q": {
                    "db": ["g"],
                    "aggregate": [
                        {
                            "$match": {
                                "graphTxn.outputs": {
                                    "$elemMatch": {"status": "BATON_UNSPENT"}
                                },
                                "tokenDetails.tokenIdHex": tokenId,
                            }
                        },
                        {"$unwind": "$graphTxn.outputs"},
                        {"$match": {"graphTxn.outputs.status": "BATON_UNSPENT"}},
                        {
                            "$project": {
                                "address": "$graphTxn.outputs.address",
                                "txid": "$graphTxn.txid",
                                "vout": "$graphTxn.outputs.vout",
                                "tokenId": "$tokenDetails.tokenIdHex",
                            }
                        },
                    ],
                    "limit": limit,
                },
            }

            path = cls.query_to_url(query, network)
            mint_baton_utxo_response = requests.get(url=path, timeout=DEFAULT_TIMEOUT)
            mint_baton_utxo_json = mint_baton_utxo_response.json()["g"]

            return [
                (tx["address"], tx["txid"], tx["vout"]) for tx in mint_baton_utxo_json
            ]

        elif address:
            query = {
                "v": 3,
                "q": {
                    "db": ["g"],
                    "aggregate": [
                        {
                            "$match": {
                                "graphTxn.outputs": {
                                    "$elemMatch": {"status": "BATON_UNSPENT"}
                                }
                            }
                        },
                        {"$unwind": "$graphTxn.outputs"},
                        {
                            "$match": {
                                "graphTxn.outputs.status": "BATON_UNSPENT",
                                "graphTxn.outputs.address": address,
                            }
                        },
                        {
                            "$project": {
                                "address": "$graphTxn.outputs.address",
                                "txid": "$graphTxn.txid",
                                "vout": "$graphTxn.outputs.vout",
                                "tokenId": "$tokenDetails.tokenIdHex",
                            }
                        },
                    ],
                    "limit": limit,
                },
            }

            path = cls.query_to_url(query, network)
            mint_baton_utxo_response = requests.get(url=path, timeout=DEFAULT_TIMEOUT)
            mint_baton_utxo_json = mint_baton_utxo_response.json()["g"]

            return [
                (tx["address"], tx["txid"], tx["vout"]) for tx in mint_baton_utxo_json
            ]
        else:
            raise ValueError("Must include either a tokenId or address")

    @classmethod
    def get_tx_by_opreturn(cls, op_return_segment, network="mainnet", limit=100):

        query = {
            "v": 3,
            "q": {
                "db": ["c"],
                "aggregate": [
                    {
                        "$match": {
                            "out": {
                                "$elemMatch": {"str": {"$regex": op_return_segment}}
                            }
                        }
                    },
                    {
                        "$project": {
                            "_id": "$_id",
                            "txid": "$tx.h",
                            "slp_name": "$slp.detail.name",
                            "slp_amount": "$slp.detail.outputs",
                            "opreturns": "$out.str",
                        }
                    },
                ],
                "limit": 10,
            },
        }

        path = cls.query_to_url(query, network)
        tx_containing_op_return_response = requests.get(
            url=path, timeout=DEFAULT_TIMEOUT
        )
        tx_containing_op_return_json = tx_containing_op_return_response.json()["c"]

        # return [
        #     (
        #     a['token_balance'],
        #     a['address'],
        #     a['txid'],
        #     a['vout']
        #     )

        #     for a in j
        # ]

        # Not sure on what information we want from this call, format this
        # Used for searching for secondary opreturn in a multi opreturn tx
        # TODO format this

        return tx_containing_op_return_json

    @classmethod
    def get_child_nft_by_parent_tokenId(
        cls, tokenId, network="mainnet", skip=0, limit=100
    ):

        query = {
            "v": 3,
            "q": {
                "db": ["t"],
                "aggregate": [
                    {
                        "$match": {
                            "nftParentId": tokenId,
                        },
                    },
                    {
                        "$sort": {
                            "tokenStats.block_created": -1,
                        },
                    },
                    {
                        "$skip": skip,
                    },
                    {
                        "$limit": limit,
                    },
                ],
            },
        }

        path = cls.query_to_url(query, network)
        child_nft_response = requests.get(url=path, timeout=DEFAULT_TIMEOUT)
        child_nft_json = child_nft_response.json()["t"]

        return [
            (
                token["tokenDetails"]["tokenIdHex"],
                token["tokenDetails"]["documentUri"],
                token["tokenDetails"]["documentSha256Hex"],
                token["tokenDetails"]["symbol"],
                token["tokenDetails"]["name"],
                token["tokenDetails"]["genesisOrMintQuantity"],
                token["tokenDetails"]["decimals"],
                token["tokenDetails"]["versionType"],
            )
            for token in child_nft_json
        ]

    @classmethod
    def filter_slp_txid(cls, address, slp_address, unspents, network="mainnet"):

        slp_utxos = SlpAPI.get_all_slp_utxo_by_address(slp_address, network=network)

        baton_info = SlpAPI.get_mint_baton(address=slp_address, network=network)
        baton_tx = []

        if len(baton_info) > 0:
            for baton in baton_info:
                baton_tx.append(("546", baton[0], baton[1], baton[2]))

        # Filters SLP out of unspent pool
        def _is_slp(unspent, slp_utxos):
            return (unspent.txid, unspent.txindex) in [
                (slp_utxo[2], slp_utxo[3]) for slp_utxo in slp_utxos
            ]

        # Grabs UTXOs with batons attached
        def _is_baton(unspent, baton_tx):
            return (unspent.txid, unspent.txindex) in [
                (baton[2], baton[3]) for baton in baton_tx
            ]

        # Filters baton out of unspent pool
        def _filter_baton_out(unspent, baton_utxo):
            return (unspent.txid, unspent.txindex) in [
                (batonutxo.txid, batonutxo.txindex) for batonutxo in baton_utxo
            ]

        difference = [
            unspent for unspent in unspents if not _is_slp(unspent, slp_utxos)
        ]

        baton = [unspent for unspent in unspents if _is_baton(unspent, baton_tx)]
        utxo_without_slp_or_baton = [
            i for i in difference if not _filter_baton_out(i, baton)
        ]

        slp_utxos = [unspent for unspent in unspents if _is_slp(unspent, slp_utxos)]

        # Temporary names, need to replace
        # TODO: Refactor names
        return {
            "slp_utxos": slp_utxos,
            "difference": utxo_without_slp_or_baton,
            "baton": baton,
        }
