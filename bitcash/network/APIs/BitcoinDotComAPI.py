from bitcash.network.http import session
from decimal import Decimal
from bitcash.exceptions import InvalidEndpointURLProvided
from bitcash.network import currency_to_satoshi
from bitcash.network.meta import Unspent
from bitcash.network.transaction import Transaction, TxPart

# This class is the interface for Bitcash to interact with
# Bitcoin.com based RESTful interfaces.

BCH_TO_SAT_MULTIPLIER = 100000000
# TODO: Refactor constant above into a 'constants.py' file


class BitcoinDotComAPI:
    """ rest.bitcoin.com API """

    def __init__(self, network_endpoint: str):
        try:
            assert isinstance(network_endpoint, str)
            assert network_endpoint[:4] == "http"
            assert network_endpoint[-4:] == "/v2/"
        except AssertionError:
            raise InvalidEndpointURLProvided(f"Provided endpoint '{network_endpoint}' is not a valid URL for a Bitcoin.com-based REST endpoint")

        self.network_endpoint = network_endpoint

    # Default endpoints to use for this interface
    DEFAULT_ENDPOINTS = {
        "mainnet": ["https://rest.bch.actorforth.org/v2/",
                    "https://rest.bitcoin.com/v2/"],
        "testnet": ["https://trest.bitcoin.com/v2/"],
        "regtest": ["http://localhost:12500/v2/"],
    }

    # Paths specific to rest.bitcoin.com-based endpoints
    PATHS = {
        "unspent": "address/utxo/{}",
        "address": "address/details/{}",
        "raw-tx": "rawtransactions/sendRawTransaction",
        "tx-details": "transaction/details/{}",
    }

    @classmethod
    def get_default_endpoints(cls, network):
        return cls.DEFAULT_ENDPOINTS[network]

    def make_endpoint_url(self, path):
        return self.network_endpoint + self.PATHS[path]

    def get_balance(self, address, *args, **kwargs):
        api_url = self.make_endpoint_url("address").format(address)
        r = session.get(api_url, *args, **kwargs)
        r.raise_for_status()
        data = r.json()
        return data["balanceSat"] + data["unconfirmedBalanceSat"]

    def get_transactions(self, address, *args, **kwargs):
        api_url = self.make_endpoint_url("address").format(address)
        r = session.get(api_url, *args, **kwargs)
        r.raise_for_status()
        return r.json()["transactions"]

    def get_transaction(self, txid, *args, **kwargs):
        api_url = self.make_endpoint_url("tx-details").format(txid)
        r = session.get(api_url, *args, **kwargs)
        r.raise_for_status()
        response = r.json(parse_float=Decimal)

        tx = Transaction(
            response["txid"],
            response["blockheight"],
            (Decimal(response["valueIn"]) * BCH_TO_SAT_MULTIPLIER).normalize(),
            (Decimal(response["valueOut"]) * BCH_TO_SAT_MULTIPLIER).normalize(),
            (Decimal(response["fees"]) * BCH_TO_SAT_MULTIPLIER).normalize(),
        )

        for txin in response["vin"]:
            part = TxPart(txin["cashAddress"], txin["value"], txin["scriptSig"]["asm"])
            tx.add_input(part)

        for txout in response["vout"]:
            addr = None
            if (
                "cashAddrs" in txout["scriptPubKey"]
                and txout["scriptPubKey"]["cashAddrs"] is not None
            ):
                addr = txout["scriptPubKey"]["cashAddrs"][0]

            part = TxPart(
                addr,
                (Decimal(txout["value"]) * BCH_TO_SAT_MULTIPLIER).normalize(),
                txout["scriptPubKey"]["asm"],
            )
            tx.add_output(part)

        return tx

    def get_tx_amount(self, txid, txindex, *args, **kwargs):
        api_url = self.make_endpoint_url("tx-details").format(txid)
        r = session.get(api_url, *args, **kwargs)
        r.raise_for_status()
        response = r.json(parse_float=Decimal)
        return (
            Decimal(response["vout"][txindex]["value"]) * BCH_TO_SAT_MULTIPLIER
        ).normalize()

    def get_unspent(self, address, *args, **kwargs):
        api_url = self.make_endpoint_url("unspent").format(address)
        r = session.get(api_url, *args, **kwargs)
        r.raise_for_status()
        return [
            Unspent(
                currency_to_satoshi(tx["amount"], "bch"),
                tx["confirmations"],
                r.json()["scriptPubKey"],
                tx["txid"],
                tx["vout"],
            )
            for tx in r.json()["utxos"]
        ]

    def get_raw_transaction(self, txid, *args, **kwargs):
        api_url = self.make_endpoint_url("tx-details").format(txid)
        r = session.get(api_url, *args, **kwargs)
        r.raise_for_status()
        return r.json(parse_float=Decimal)

    def broadcast_tx(self, tx_hex, *args, **kwargs):  # pragma: no cover
        api_url = self.make_endpoint_url("raw-tx")
        r = session.post(api_url, json={"hexes": [tx_hex]}, *args, **kwargs)
        return r.status_code == 200
