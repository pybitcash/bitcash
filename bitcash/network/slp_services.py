import logging
import json
import os

import requests
import base64
from decimal import Decimal

from bitcash.network import currency_to_satoshi, NetworkAPI
from bitcash.network.meta import Unspent
from bitcash.network.transaction import Transaction, TxPart
from bitcash.exceptions import InvalidNetwork

DEFAULT_TIMEOUT = 30

BCH_TO_SAT_MULTIPLIER = 100000000

NETWORKS = {"mainnet", "testnet", "regtest"}


class SlpAPI:

    NETWORK_ENDPOINTS = {
        "mainnet": os.getenv("SLP_MAIN_ENDPOINT", "https://slpdb.bch.actorforth.org/q/"),
        "testnet": os.getenv(
            "SLP_TEST_ENDPOINT", "https://slpdb-testnet.fountainhead.cash/q/"
        ),
        "regtest": os.getenv("SLP_REG_ENDPOINT", "http://localhost:12300/q/"),
    }

    @classmethod
    def network_endpoint(cls, network):
        if network not in NETWORKS:
            raise InvalidNetwork(f"No endpoints found for network {network}")
        return cls.NETWORK_ENDPOINTS[network]

    @classmethod
    def query_to_url(cls, query, network):
        query_to_string = json.dumps(query)
        query_b64 = base64.b64encode(query_to_string.encode("utf-8"))
        b64_to_str = str(query_b64)
        query_path = b64_to_str[2:-1]

        url = cls.network_endpoint(network) + query_path

        return url

    @classmethod
    def get_balance(cls, address, tokenId, network="mainnet"):

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
                },
            }

            path = cls.query_to_url(query, network)
            get_balance_response = requests.get(url=path, timeout=DEFAULT_TIMEOUT)

            # Check response json size to determine if empty response, prevents
            # throwing error if calling index of empty array.
            if len(get_balance_response.json()) > 0:
                get_balance_json = get_balance_response.json()["g"]
                return [
                    (
                        token["token"][0]["tokenDetails"]["tokenIdHex"],
                        token["token"][0]["tokenDetails"]["name"],
                        token["slpAmount"],
                    )
                    for token in get_balance_json
                ]
            else:
                return []

    @classmethod
    def get_balance_address(cls, address, network="mainnet"):
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
            },
        }

        path = cls.query_to_url(query, network)
        get_balance_response = requests.get(url=path, timeout=DEFAULT_TIMEOUT)

        # Check response json size to determine if empty response, prevents
        # throwing error if calling index of empty array.
        if len(get_balance_response.json()) > 0:
            get_balance_json = get_balance_response.json()["g"]
            return [
                (
                    token["token"][0]["tokenDetails"]["tokenIdHex"],
                    token["token"][0]["tokenDetails"]["name"],
                    token["slpAmount"],
                )
                for token in get_balance_json
            ]
        else:
            return []


    @classmethod
    def get_token_fan_out_count(cls, token_id, network="mainnet", limit=1000):
        # c2c8f750774094bfa90eab73b689f8ab5fc6ba9f85880091818890869fda6167
        query={    
            "v": 3, #version
            "q": {  #query
                "db": ["g"],    #table
                "aggregate": [
                {   # filter token
                    "$match": {
                        "tokenDetails.tokenIdHex": token_id
                    }
                }, {    # split outputs into separate documents
                    "$unwind": {
                        "path": "$graphTxn.outputs"
                    }
                }, {    # filter only unspents at quantity of 1
                    "$match": {
                        "graphTxn.outputs.status": "UNSPENT", 
                        "graphTxn.outputs.slpAmount": 1
                    }
                }, {
                    "$count": "amount"
                }
            ],
            "limit":limit
            }
        }

        path = cls.query_to_url(query, network)
        get_token_fan_count_response = requests.get(url=path, timeout=DEFAULT_TIMEOUT)
        get_token_fan_count_json = get_token_fan_count_response.json()["g"]

        if len(get_token_fan_count_json) > 0:
            return {"amount": get_token_fan_count_json[0]["amount"]}
        else:

            return get_token_fan_count_json
   

    @classmethod
    def get_balance_address_and_tokentype(
        cls, address, token_type, network="mainnet", limit=1000
    ):
        # Check whether the token is group or child NFT, as the meta data is different.
        # In group we are projecting the denomination and seats while child is projecting
        # tokenId and name
        if token_type == 129:
            query = {
                "v": 3,
                "q": {
                    "db": ["c", "u"],
                    "aggregate": [
                        {
                            "$match": {
                                "slp.detail.outputs.address": address,
                                "slp.detail.versionType": token_type,
                                "slp.detail.transactionType": "GENESIS",
                            }
                        },
                        {
                            "$project": {
                                "tokenId": "$tx.h",
                                "denomination": {"$arrayElemAt": ["$out", 3]},
                                "seats": {"$arrayElemAt": ["$out", 4]},
                            }
                        },
                        {
                            "$project": {
                                "tokenId": "$tokenId",
                                "denomination": "$denomination.s1",
                                "seats": "$seats.s1",
                            }
                        },
                    ],
                    "limit": limit,
                },
            }
        else:
            query = {
                "v": 3,
                "q": {
                    "db": ["c", "u"],
                    "aggregate": [
                        {
                            "$match": {
                                "slp.detail.outputs.address": address,
                                "slp.detail.versionType": token_type,
                            }
                        },
                        {
                            "$project": {
                                "tokenId": "$slp.detail.tokenIdHex",
                                "name": "$slp.detail.name",
                            }
                        },
                    ],
                    "limit": limit,
                },
            }

        path = cls.query_to_url(query, network)
        get_group_token_response = requests.get(url=path, timeout=DEFAULT_TIMEOUT)
        json = get_group_token_response.json()

        confirmed = []
        confirmed.extend(json["c"])
        unconfirmed = []
        unconfirmed.extend(json["u"])

        transactions = []
        transactions.extend(confirmed)
        transactions.extend(unconfirmed)
        return transactions

    @classmethod
    def get_meta_details_of_child_nft(cls, tokenId, network="mainnet"):
        query = {
            "v": 3,
            "q": {
                "db": ["c", "u"],
                "aggregate": [
                    {
                        "$lookup": {
                            "from": "tokens",
                            "localField": "slp.detail.tokenIdHex",
                            "foreignField": "tokenDetails.tokenIdHex",
                            "as": "tokenDetails",
                        }
                    },
                    {
                        "$match": {
                            "tx.h": tokenId,
                            "slp.detail.versionType": 65,
                            "slp.detail.transactionType": "GENESIS",
                        }
                    },
                    {
                        "$project": {
                            "nft txid": "$tx.h",
                            "return address": {"$arrayElemAt": ["$out", 3]},
                            "message": {"$arrayElemAt": ["$tokenDetails", 0]},
                        }
                    },
                    {
                        "$project": {
                            "nft txid": "$nft txid",
                            "return address": "$return address.s1",
                            "parentId": "$message.nftParentId",
                        }
                    },
                ],
            },
        }
        path = cls.query_to_url(query, network)
        response = requests.get(url=path, timeout=DEFAULT_TIMEOUT)
        json = response.json()
        confirmed = []
        confirmed.extend(json["c"])
        unconfirmed = []
        unconfirmed.extend(json["u"])

        transactions = []
        transactions.extend(confirmed)
        transactions.extend(unconfirmed)

        return transactions

    @classmethod
    def get_token_by_id(cls, tokenid, network="mainnet"):
        query = {
            "v": 3,
            "q": {
                "db": ["t"],
                "find": {"$query": {"tokenDetails.tokenIdHex": tokenid}},
                "project": {"tokenDetails": 1, "tokenStats": 1, "_id": 0},
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
    def get_utxo_by_tokenId(cls, tokenId, address=None, network="mainnet"):

        if address:
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
                },
            }
        else:
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
                    ],
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
    def get_all_slp_utxo_by_address(cls, address, network="mainnet"):

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
                "limit": 9999999,
            },
        }

        path = cls.query_to_url(query, network)
        slp_utxo_response = requests.get(url=path, timeout=DEFAULT_TIMEOUT)
        slp_utxo_json = slp_utxo_response.json()
        if len(slp_utxo_json) > 0:
            json = slp_utxo_json["g"]

            return [
                (utxo["token_balance"], utxo["address"], utxo["txid"], utxo["vout"])
                for utxo in json
            ]
        else:
            return []

    @classmethod
    def get_mint_baton(cls, tokenId=None, address=None, network="mainnet"):

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
    def get_tx_by_opreturn(cls, op_return_segment, network="mainnet"):

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
            },
        }

        path = cls.query_to_url(query, network)
        tx_containing_op_return_response = requests.get(
            url=path, timeout=DEFAULT_TIMEOUT
        )
        tx_containing_op_return_json = tx_containing_op_return_response.json()["c"]

        # return [
        #     (
        #     a["token_balance"],
        #     a["address"],
        #     a["txid"],
        #     a["vout"]
        #     )

        #     for a in j
        # ]

        # Not sure on what information we want from this call, format this
        # Used for searching for secondary opreturn in a multi opreturn tx
        # TODO format this

        return tx_containing_op_return_json

    @classmethod
    def get_child_nft_by_parent_tokenId(cls, tokenId, network="mainnet"):

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
    def get_unconfirmed_spent_utxo_genesis_65(cls, tokenId, address, network="mainnet"):
        # Grabs inputs of unconfirmed type 65 genesis tx
        # Work around for type 129 inputs on type 65 genesis
        # not registering as spent

        query = {
            "v": 3,
            "q": {
                "db": ["u"],
                "aggregate": [
                    {
                        "$match": {
                            "slp.detail.versionType": 65,
                            "slp.detail.transactionType": "GENESIS",
                        }
                    },
                    {"$unwind": "$in"},
                ],
                "project": {
                    "txid": "$tx.h",
                    "vin index": "$in.i",
                    "vin txid": "$in.e.h",
                    "utxo index": "$in.e.i",
                },
            },
        }

        path = cls.query_to_url(query, network)
        get_utxo_response = requests.get(url=path, timeout=DEFAULT_TIMEOUT)
        get_utxo_json = get_utxo_response.json()["u"]

        return [
            (utxo["txid"], utxo["vin index"], utxo["vin txid"], utxo["utxo index"])
            for utxo in get_utxo_json
        ]

    @classmethod
    def filter_slp_txid(cls, address, slp_address, unspents, network="mainnet"):

        slp_utxos = SlpAPI.get_all_slp_utxo_by_address(slp_address, network=network)
        baton_info = SlpAPI.get_mint_baton(address=slp_address, network=network)
        baton_txs = []

        if len(baton_info) > 0:
            for baton in baton_info:
                baton_txs.append(("546", baton[0], baton[1], baton[2]))

        # Filters SLP out of unspent pool
        def _is_slp(unspent, slp_utxos):
            return (unspent.txid, unspent.txindex) in [
                (slp_utxo[2], slp_utxo[3]) for slp_utxo in slp_utxos
            ]

        # Grabs UTXOs with batons attached
        def _is_baton(unspent, baton_txs):
            return (unspent.txid, unspent.txindex) in [
                (baton[2], baton[3]) for baton in baton_txs
            ]

        # # Filters baton out of unspent pool
        def _filter_baton_out(unspent, baton_utxo):
            return (unspent.txid, unspent.txindex) in [
                (batonutxo.txid, batonutxo.txindex) for batonutxo in baton_utxo
            ]

        bch_unspents = []
        slp_unspents = []
        batons = []

        for unspent in unspents:
            if _is_slp(unspent, slp_utxos):
                slp_unspents.append(unspent)
            elif _is_baton(unspent, baton_txs):
                batons.append(unspent)
            else:
                bch_unspents.append(unspent)

        # difference = [
        #     unspent for unspent in unspents if not _is_slp(unspent, slp_utxos)
        # ]

        # baton = [unspent for unspent in unspents if _is_baton(unspent, baton_txs)]
        # utxo_without_slp_or_baton = [
        #     i for i in difference if not _filter_baton_out(i, baton)
        # ]
        # slp_utxos = [unspent for unspent in unspents if _is_slp(unspent, slp_utxos)]

        # Temporary names, need to replace
        # TODO: Refactor names

        # return {
        #     "slp_utxos": slp_utxos,
        #     "difference": utxo_without_slp_or_baton,
        #     "baton": baton,
        # }

        return {
            "slp_utxos": slp_unspents,
            "difference": bch_unspents,
            "baton": batons,
        }