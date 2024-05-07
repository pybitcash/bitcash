import json
import socket
import ssl
from decimal import Decimal
import typing
from requests.exceptions import ConnectTimeout, ContentDecodingError, SSLError
from typing import Any, Union

from bitcash.exceptions import InvalidEndpointURLProvided
from bitcash.network.APIs import BaseAPI
from bitcash.network.meta import Unspent
from bitcash.network.transaction import Transaction, TxPart
from bitcash.cashaddress import Address
from bitcash.utils import time_cache


context = ssl.create_default_context()
FULCRUM_PROTOCOL = "1.5.0"
# the socket times out in ~600s, a new handshake is performed within that
HANDSHAKE_TIMEOUT = 500

BCH_TO_SAT_MULTIPLIER = 100000000
# TODO: Refactor constant above into a 'constants.py' file


@time_cache(max_age=HANDSHAKE_TIMEOUT)
def handshake(hostname: str, port: int) -> ssl.SSLSocket:
    """
    Perform handshake with the host and establish protocol
    """
    # make socket connection
    sock = socket.create_connection((hostname, port))
    try:
        ssock = context.wrap_socket(sock, server_hostname=hostname)
    except ssl.SSLError as e:
        raise SSLError(f"{hostname=} doesn't support ssl connection") from e

    # send a server.version to establish protocol
    _ = send_json_rpc_payload(
        ssock, "server.version", ["Bitcash", FULCRUM_PROTOCOL]
    )
    # if no errors, then handshake complete

    return ssock


def send_json_rpc_payload(
    sock: Union[socket.socket, ssl.SSLSocket],
    method: str,
    params: list[Any],
    *args,
    **kwargs,
) -> Any:
    """
    Function to send a json rpc 2.0 payload over a given socket instance, and return the
    parsed result.
    """
    payload = {
        "method": method,
        "params": params,
        "jsonrpc": "2.0",
        "id": "bitcash",
    }
    payload_bytes = json.dumps(payload).encode() + b"\n"
    sock.sendall(payload_bytes)  # will raise ssl.SSLZeroReturnError if SSL closes
    data = b""
    while True:
        data += sock.recv(4096)
        # if sock timed out and data is b""
        # or the message completed and has endline char
        if not data or data.endswith(b"\n"):
            break
    if data == b"\n":
        raise ConnectTimeout("TLS/SSL connection has been closed (EOF)")
    return_json = json.loads(data.decode(), parse_float=Decimal)
    if return_json["jsonrpc"] != "2.0" or return_json["id"] != "bitcash":
        raise ContentDecodingError(
            f"Returned json {return_json} is not valid json rpc 2.0"
        )

    if "error" in return_json:
        raise RuntimeError(f"Error in retruned json: {return_json['error']}")

    return return_json["result"]


class FulcrumProtocolAPI(BaseAPI):
    """Fulcrum Protocol API
    Documentation at: https://electrum-cash-protocol.readthedocs.io/en/latest/index.html

    :param network_endpoint: The url for the network endpoint
    """

    # Default endpoints to use for this interface
    DEFAULT_ENDPOINTS = {
        "mainnet": [
            "bch.imaginary.cash:50002",
            "electron.jochen-hoenicke.de:51002",
        ],
        "testnet": [
            "testnet.imaginary.cash:50002",
            "testnet.bitcoincash.network:60002",
        ],
        "regtest": [],
    }

    def __init__(self, network_endpoint: str):
        try:
            assert isinstance(network_endpoint, str)
        except AssertionError:
            raise InvalidEndpointURLProvided(
                f"Provided endpoint '{network_endpoint}' is not a valid URL"
                f" for a Electrum Cash Protocol endpoint"
            )

        if network_endpoint.count(":") != 1:
            raise InvalidEndpointURLProvided(
                f"Provided endpoint '{network_endpoint}' doesn't have hostname and "
                f"port separated by ':'"
            )

        self.hostname, port = network_endpoint.split(":")
        self.port = int(port)

    @property
    def sock(self):
        return handshake(self.hostname, self.port)

    @classmethod
    def get_default_endpoints(cls, network: str):
        return cls.DEFAULT_ENDPOINTS[network]

    def get_blockheight(self, *args, **kwargs):
        result = send_json_rpc_payload(
            self.sock, "blockchain.headers.get_tip", [], *args, **kwargs
        )
        return result["height"]

    def get_balance(self, address, *args, **kwargs):
        result = send_json_rpc_payload(
            self.sock, "blockchain.address.get_balance", [address], *args, **kwargs
        )
        return result["confirmed"] + result["unconfirmed"]

    def get_transactions(self, address, *args, **kwargs):
        result = send_json_rpc_payload(
            self.sock, "blockchain.address.get_history", [address], *args, **kwargs
        )
        transactions = [(tx["tx_hash"], tx["height"]) for tx in result]
        # sort by block height
        transactions.sort(key=lambda x: x[1])
        transactions = [_[0] for _ in transactions][::-1]
        return transactions

    def get_transaction(self, txid, *args, **kwargs):
        result = self.get_raw_transaction(txid, *args, **kwargs)
        blockheight = self.get_blockheight()

        if result["confirmations"] == 0:
            tx_blockheight = None
        else:
            tx_blockheight = blockheight - result["confirmations"] + 1

        tx_data = {"vin": [], "vout": []}

        for vx in ["vin", "vout"]:
            for txout in result[vx]:
                if vx == "vin":
                    txout = self._get_raw_tx_out(txout["txid"], txout["vout"])
                addr = None
                if (
                    "addresses" in txout["scriptPubKey"]
                    and txout["scriptPubKey"]["addresses"] is not None
                ):
                    addr = txout["scriptPubKey"]["addresses"][0]

                category_id = None
                nft_capability = None
                nft_commitment = None
                token_amount = None
                if "tokenData" in txout:
                    token_data = txout["tokenData"]
                    category_id = token_data["category"]
                    token_amount = int(token_data["amount"]) or None
                    if "nft" in token_data:
                        nft_capability = token_data["nft"]["capability"]
                        nft_commitment = (
                            bytes.fromhex(token_data["nft"]["commitment"]) or None
                        )
                part = TxPart(
                    addr,
                    int((txout["value"] * BCH_TO_SAT_MULTIPLIER).to_integral_value()),
                    category_id,
                    nft_capability,
                    nft_commitment,
                    token_amount,
                    asm=txout["scriptPubKey"]["asm"],
                )
                tx_data[vx].append(part)

        value_in = sum([x.amount for x in tx_data["vin"]])
        value_out = sum([x.amount for x in tx_data["vout"]])
        value_fee = value_in - value_out

        tx = Transaction(
            result["txid"],
            tx_blockheight,
            value_in,
            value_out,
            value_fee,
        )

        tx.inputs = tx_data["vin"]
        tx.outputs = tx_data["vout"]

        return tx

    def _get_raw_tx_out(
        self, txid: str, txindex: int, *args, **kwargs
    ) -> dict[str, Any]:
        result = self.get_raw_transaction(txid, *args, **kwargs)

        for vout in result["vout"]:
            if vout["n"] == txindex:
                return vout
        raise RuntimeError(f"Transaction {txid=} doesn't have {txindex=}")

    def get_tx_amount(self, txid: str, txindex: int, *args, **kwargs) -> int:
        result = self.get_raw_transaction(txid, *args, **kwargs)

        for vout in result["vout"]:
            if vout["n"] == txindex:
                sats = int((vout["value"] * BCH_TO_SAT_MULTIPLIER).to_integral_value())
                return sats
        raise RuntimeError(f"Transaction {txid=} doesn't have {txindex=}")

    def get_unspent(self, address: str, *args, **kwargs) -> list[Unspent]:
        result = send_json_rpc_payload(
            self.sock, "blockchain.address.listunspent", [address], *args, **kwargs
        )
        blockheight = self.get_blockheight()
        unspents = []
        for utxo in result:
            confirmations = (
                0 if utxo["height"] == 0 else blockheight - utxo["height"] + 1
            )
            token_data = utxo.get("token_data", {})
            token_category = token_data.get("category", None)
            nft = token_data.get("nft", None)
            if nft is None:
                nft_commitment = None
                nft_capability = None
            else:
                nft_commitment = bytes.fromhex(nft["commitment"])
                nft_capability = nft["capability"]
            token_amount = int(token_data.get("amount"))
            # add unspent
            unspents.append(
                Unspent(
                    int(utxo["value"]),
                    confirmations,
                    Address.from_string(address).scriptcode.hex(),
                    utxo["tx_hash"],
                    utxo["tx_pos"],
                    token_category,
                    nft_capability,
                    nft_commitment or None,  # b"" is None
                    token_amount or None,  # 0 amount is None
                )
            )
        return unspents

    def get_raw_transaction(self, txid: str, *args, **kwargs) -> dict[str, Any]:
        result = send_json_rpc_payload(
            self.sock, "blockchain.transaction.get", [txid, True], *args, **kwargs
        )

        return typing.cast(dict[str, Any], result)

    def broadcast_tx(self, tx_hex: str, *args, **kwargs) -> bool:  # pragma: no cover
        _ = send_json_rpc_payload(
            self.sock, "blockchain.transaction.broadcast", [tx_hex]
        )
        return True
