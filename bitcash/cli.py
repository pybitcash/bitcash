from __future__ import annotations

import datetime
import os
import threading
from dataclasses import dataclass
from typing import Any, cast

try:
    import click  # pyright: ignore
except ImportError:
    raise ImportError("Please install the 'click' package to use this CLI tool.")

try:
    import appdirs  # pyright: ignore
except ImportError:
    appdirs = None  # type: ignore[assignment]

try:
    import privy  # pyright: ignore
except ImportError:
    privy = None  # type: ignore[assignment]

try:
    from tinydb import TinyDB, Query  # pyright: ignore
except ImportError:
    TinyDB = None  # type: ignore[assignment,misc]
    Query = None  # type: ignore[assignment]

from bitcash.cashtoken import Unspents as CashtokenUnspents
from bitcash.format import address_to_cashtokenaddress
from bitcash.keygen import generate_matching_address
from bitcash.wallet import PrivateKey, wif_to_key
from bitcash.network import NetworkAPI, satoshi_to_currency_cached
from bitcash.types import Network, NFTCapability, TokenData, UserOutput


# ---------------------------------------------------------------------------
# Shared option — callback converts the CLI string to a Network enum member
# ---------------------------------------------------------------------------


def _parse_network(ctx: click.Context, param: click.Parameter, value: str) -> Network:
    return Network[value]


PASSWORD_OPTION = click.option(
    "--password",
    "-p",
    envvar="BITCASH_WALLET_PASSWORD",
    default=None,
    help="Wallet password (or set BITCASH_WALLET_PASSWORD env var; prompts if omitted)",
)

NETWORK_OPTION = click.option(
    "--network",
    "-n",
    type=click.Choice([n.name for n in Network]),
    default=Network.main.name,
    show_default=True,
    callback=_parse_network,
)


def _parse_nft_commitment(
    ctx: click.Context, param: click.Parameter, value: str | None
) -> bytes | None:
    if value is None:
        return None
    try:
        return bytes.fromhex(value)
    except ValueError:
        raise click.BadParameter("must be a valid hex string")


CATEGORY_ID_OPTION = click.option(
    "--category-id",
    default=None,
    help="CashToken category ID (hex)",
)

NFT_CAPABILITY_OPTION = click.option(
    "--nft-capability",
    type=click.Choice([c.name for c in NFTCapability]),
    default=None,
    help="NFT capability",
)

NFT_COMMITMENT_OPTION = click.option(
    "--nft-commitment",
    default=None,
    callback=_parse_nft_commitment,
    help="NFT commitment (hex)",
)

TOKEN_AMOUNT_OPTION = click.option(
    "--token-amount",
    default=None,
    type=int,
    help="Fungible token amount",
)

CASHTOKEN_FLAG = click.option(
    "--cashtoken", is_flag=True, help="Also show CashToken holdings"
)


# ---------------------------------------------------------------------------
# Wallet record
# ---------------------------------------------------------------------------


@dataclass
class WalletRecord:
    name: str
    network: Network
    address: str
    encrypted_wif: str

    def to_dict(self) -> dict[str, str]:
        return {
            "name": self.name,
            "network": self.network.name,
            "address": self.address,
            "encrypted_wif": self.encrypted_wif,
        }

    @classmethod
    def from_dict(cls, data: dict[str, str]) -> WalletRecord:
        return cls(
            name=data["name"],
            network=Network[data["network"]],
            address=data["address"],
            encrypted_wif=data["encrypted_wif"],
        )


# ---------------------------------------------------------------------------
# DB helpers
# ---------------------------------------------------------------------------


def _get_db() -> Any:  # returns TinyDB when available
    if TinyDB is None or appdirs is None:
        raise click.ClickException(
            "Wallet commands require optional dependencies. "
            "Install them with: pip install 'bitcash[cli]'"
        )
    data_dir: str = appdirs.user_data_dir("bitcash")
    os.makedirs(data_dir, exist_ok=True)
    return TinyDB(os.path.join(data_dir, "wallets.json"))


def _load_key_from_db(name: str) -> WalletRecord:
    db = _get_db()
    assert Query is not None
    results: list[dict[str, str]] = db.search(Query().name == name)
    if not results:
        raise click.ClickException(f"Wallet '{name}' not found.")
    return WalletRecord.from_dict(results[0])


def _prompt_password(password: str | None, *, confirm: bool = False) -> str:
    if password is not None:
        return password
    return click.prompt("Password", hide_input=True, confirmation_prompt=confirm)


def _decrypt_wif(record: WalletRecord, password: str) -> str:
    if privy is None:
        raise click.ClickException(
            "Wallet commands require optional dependencies. "
            "Install them with: pip install 'bitcash[cli]'"
        )
    try:
        return privy.peek(record.encrypted_wif, password).decode()
    except Exception:
        raise click.ClickException("Incorrect password or corrupted wallet data.")


# ---------------------------------------------------------------------------
# CashToken helpers
# ---------------------------------------------------------------------------


def _print_cashtoken_balance(tokendata: dict[str, TokenData]) -> None:
    if not tokendata:
        click.echo("No tokens found.")
        return
    for category_id, data in tokendata.items():
        click.echo(f"Category: {category_id}")
        if data.token_amount is not None:
            click.echo(f"  Fungible amount: {data.token_amount}")
        if data.nft:
            click.echo(f"  NFTs ({len(data.nft)}):")
            for nft in data.nft:
                commitment = nft.commitment.hex() if nft.commitment else "(none)"
                click.echo(
                    f"    capability={nft.capability.name}  commitment(hex)={commitment}"
                )


def _build_output(
    to: str,
    amount: str,
    currency: str,
    category_id: str | None,
    nft_capability: str | None,
    nft_commitment: bytes | None,
    token_amount: int | None,
) -> UserOutput:
    if category_id is None:
        return cast(UserOutput, (to, amount, currency))
    return cast(
        UserOutput,
        (
            to,
            amount,
            currency,
            category_id,
            nft_capability,
            nft_commitment,
            token_amount,
        ),
    )


# ---------------------------------------------------------------------------
# Root group
# ---------------------------------------------------------------------------


@click.group(invoke_without_command=True)
@click.pass_context
def bitcash(ctx: click.Context) -> None:
    """BitCash: Python Bitcoin Cash Library."""
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


# ---------------------------------------------------------------------------
# gen
# ---------------------------------------------------------------------------


@bitcash.command()  # pyright: ignore
@click.argument("prefix")
@click.option("--cores", "-c", default="all")
def gen(prefix: str, cores: str) -> None:
    """Generate a vanity address whose address starts with PREFIX.

    CPU-intensive and may run for a long time depending on prefix length.
    No network calls. Prints a (WIF, address) pair when a match is found.
    """
    click.echo(generate_matching_address(prefix, cores))


# ---------------------------------------------------------------------------
# cashtoken-address
# ---------------------------------------------------------------------------


@bitcash.command(name="cashtoken-address")
@click.argument("address")
def cashtoken_address_cmd(address: str) -> None:
    """Convert ADDRESS to its CashToken-signalling form (bitcoincash:zz...).

    Pure local conversion — no network calls. CashToken-signalling addresses
    are required as destinations when sending tokens via the send commands.
    """
    click.echo(address_to_cashtokenaddress(address))


# ---------------------------------------------------------------------------
# new
# ---------------------------------------------------------------------------


@bitcash.command(name="new")
@NETWORK_OPTION
def new_cmd(network: Network) -> None:
    """Generate a new private key and print its WIF and address.

    No network calls. Each invocation produces a unique key — never reuses keys.
    Store the WIF securely; it cannot be recovered if lost.
    """
    key = PrivateKey(network=network.name)
    click.echo(f"WIF:     {key.to_wif()}")
    click.echo(f"Address: {key.address}")


# ---------------------------------------------------------------------------
# balance
# ---------------------------------------------------------------------------


@bitcash.command()
@click.argument("address")
@click.option("--currency", default="satoshi", show_default=True)
@CASHTOKEN_FLAG
@NETWORK_OPTION
def balance(address: str, currency: str, cashtoken: bool, network: Network) -> None:
    """Show the BCH balance of ADDRESS, and optionally its CashToken holdings.

    Always fetches the BCH balance via a network call. With --cashtoken, also
    fetches UTXOs to aggregate fungible token amounts and NFTs per category ID.
    Output is human-readable; use 'bitcash schema' for machine-readable field names.
    """
    raw: int = NetworkAPI.get_balance(address, network=network.value)
    if currency == "satoshi":
        click.echo(f"{raw} satoshi")
    else:
        click.echo(satoshi_to_currency_cached(raw, currency))
    if cashtoken:
        utxos = NetworkAPI.get_unspent(address, network=network.value)
        agg = CashtokenUnspents(utxos)
        _print_cashtoken_balance(agg.tokendata)


# ---------------------------------------------------------------------------
# transactions
# ---------------------------------------------------------------------------


@bitcash.command()
@click.argument("address")
@NETWORK_OPTION
def transactions(address: str, network: Network) -> None:
    """List all transaction IDs for ADDRESS, one per line.

    Read-only network call. Prints nothing (exit 0) if the address has no history.
    """
    txs: list[str] = NetworkAPI.get_transactions(address, network=network.value)
    if not txs:
        click.echo("No transactions found.")
    else:
        for txid in txs:
            click.echo(txid)


# ---------------------------------------------------------------------------
# unspents
# ---------------------------------------------------------------------------


@bitcash.command()
@click.argument("address")
@NETWORK_OPTION
def unspents(address: str, network: Network) -> None:
    """List all unspent transaction outputs (UTXOs) for ADDRESS, one per line.

    Read-only network call. Each line includes txid, vout index, amount in
    satoshi, and any CashToken prefix data attached to that UTXO.
    """
    utxos = NetworkAPI.get_unspent(address, network=network.value)
    if not utxos:
        click.echo("No unspents found.")
    else:
        for u in utxos:
            click.echo(u)


# ---------------------------------------------------------------------------
# subscribe (stateless)
# ---------------------------------------------------------------------------


@bitcash.command(name="subscribe")
@click.argument("address")
@click.option(
    "--show-balance", is_flag=True, help="Fetch and print balance on each update"
)
@NETWORK_OPTION
def subscribe_cmd(address: str, show_balance: bool, network: Network) -> None:
    """Watch ADDRESS for real-time transaction activity over a persistent connection.

    Blocks until Ctrl+C or the server sends an unsubscribed event. Each update
    prints a timestamped status hash. With --show-balance, also fetches and
    prints the current BCH balance on each update. Not suitable for scripted
    one-shot use — prefer 'balance' or 'transactions' for polling.
    """
    stop_event = threading.Event()

    def on_update(addr: str, status_hash: str | None) -> None:
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        if status_hash is None:
            click.echo(f"[{ts}] {addr}  (no history)")
        elif status_hash.startswith("error:"):
            click.echo(f"[{ts}] Error: {status_hash}", err=True)
        elif status_hash == "unsubscribed":
            click.echo(f"[{ts}] Unsubscribed.")
            stop_event.set()
        else:
            if show_balance:
                bal: int = NetworkAPI.get_balance(addr, network=network.value)
                click.echo(
                    f"[{ts}] {addr}  status={status_hash[:12]}…  balance={bal} sat"
                )
            else:
                click.echo(f"[{ts}] {addr}  status={status_hash[:12]}…")

    click.echo(f"Subscribing to {address} on {network.name}. Press Ctrl+C to stop.")
    handle = NetworkAPI.subscribe_address(address, on_update, network=network.value)

    try:
        stop_event.wait()
    except KeyboardInterrupt:
        handle.unsubscribe()
        click.echo("\nUnsubscribed.")


# ---------------------------------------------------------------------------
# send (stateless)
# ---------------------------------------------------------------------------


@bitcash.command(name="send")
@click.option("--wif", required=True, help="Sender WIF private key")
@click.argument("to")
@click.argument("amount")
@click.argument("currency")
@click.option("--fee", default=None, type=int, help="Fee in satoshi/byte")
@click.option("--message", default=None, help="OP_RETURN message")
@CATEGORY_ID_OPTION
@NFT_CAPABILITY_OPTION
@NFT_COMMITMENT_OPTION
@TOKEN_AMOUNT_OPTION
@NETWORK_OPTION
def send_cmd(
    wif: str,
    to: str,
    amount: str,
    currency: str,
    fee: int | None,
    message: str | None,
    category_id: str | None,
    nft_capability: str | None,
    nft_commitment: bytes | None,
    token_amount: int | None,
    network: Network,
) -> None:
    """Sign and broadcast a BCH transaction using a raw WIF private key.

    Amount is converted from currency to satoshi automatically. Prints the
    transaction ID on success. To include CashTokens, provide --category-id;
    the destination address must be a CashToken-signalling address
    (bitcoincash:zz...) — use 'cashtoken-address' to convert if needed.
    --nft-commitment expects a hex string.
    """
    key = wif_to_key(wif, regtest=(network == Network.regtest))
    output = _build_output(
        to, amount, currency, category_id, nft_capability, nft_commitment, token_amount
    )
    txid: str = key.send(
        [output],
        fee=fee,
        message=message,
    )
    click.echo(f"Transaction ID: {txid}")


# ---------------------------------------------------------------------------
# wallet subgroup
# ---------------------------------------------------------------------------


@bitcash.group()
def wallet() -> None:
    """Manage named, password-protected wallets stored in a local TinyDB file.

    Wallets are stored at the platform user-data directory
    (e.g. ~/.local/share/bitcash/wallets.json on Linux). The private key is
    encrypted with privy using the wallet password; the address is stored in
    plaintext for read-only commands that don't need the password.
    """


@wallet.command(name="new")
@click.argument("name")
@click.option("--wif", default=None, help="Import existing WIF (optional)")
@NETWORK_OPTION
@PASSWORD_OPTION
def wallet_new(
    name: str, wif: str | None, network: Network, password: str | None
) -> None:
    """Create a new wallet or import an existing WIF into the local wallet store.

    Fails if a wallet with NAME already exists. Without --wif, generates a
    fresh private key. With --wif, the WIF's network must match --network.
    Password is required to encrypt the key; prompts interactively if omitted.
    Prints the wallet address on success.
    """
    if privy is None:
        raise click.ClickException(
            "Wallet commands require optional dependencies. "
            "Install them with: pip install 'bitcash[cli]'"
        )

    db = _get_db()
    assert Query is not None
    if db.search(Query().name == name):
        raise click.ClickException(f"Wallet '{name}' already exists.")

    if wif:
        key = wif_to_key(wif, regtest=(network == Network.regtest))
        if key._network != network:
            raise click.ClickException(
                f"WIF network '{key._network.name}' does not match --network '{network.name}'."
            )
    else:
        key = PrivateKey(network=network.name)

    pw: str = _prompt_password(password, confirm=True)
    encrypted_wif: str = privy.hide(key.to_wif().encode(), pw)

    record = WalletRecord(
        name=name,
        network=network,
        address=key.address,
        encrypted_wif=encrypted_wif,
    )
    db.insert(record.to_dict())
    click.echo(f"Wallet '{name}' created.")
    click.echo(f"Address: {key.address}")


@wallet.command(name="list")
def wallet_list() -> None:
    """List all wallets in the local store — name, network, and address.

    No password required. No network calls.
    """
    db = _get_db()
    records = [WalletRecord.from_dict(r) for r in db.all()]
    if not records:
        click.echo("No wallets found.")
    else:
        for r in records:
            click.echo(f"{r.name:20s}  {r.network.name:8s}  {r.address}")


@wallet.command(name="subscribe")
@click.argument("name")
@click.option(
    "--show-balance", is_flag=True, help="Fetch and print balance on each update"
)
def wallet_subscribe(name: str, show_balance: bool) -> None:
    """Watch wallet NAME for real-time transaction activity.

    Resolves the address from the local wallet store — no password required.
    Otherwise behaves identically to 'subscribe'. Blocks until Ctrl+C.
    """
    record = _load_key_from_db(name)
    address: str = record.address
    stop_event = threading.Event()

    def on_update(addr: str, status_hash: str | None) -> None:
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        if status_hash is None:
            click.echo(f"[{ts}] {addr}  (no history)")
        elif status_hash.startswith("error:"):
            click.echo(f"[{ts}] Error: {status_hash}", err=True)
        elif status_hash == "unsubscribed":
            click.echo(f"[{ts}] Unsubscribed.")
            stop_event.set()
        else:
            if show_balance:
                bal: int = NetworkAPI.get_balance(addr, network=record.network.value)
                click.echo(
                    f"[{ts}] {addr}  status={status_hash[:12]}…  balance={bal} sat"
                )
            else:
                click.echo(f"[{ts}] {addr}  status={status_hash[:12]}…")

    click.echo(
        f"Subscribing to {name} ({address}) on {record.network.name}. Press Ctrl+C to stop."
    )
    handle = NetworkAPI.subscribe_address(
        address, on_update, network=record.network.value
    )

    try:
        stop_event.wait()
    except KeyboardInterrupt:
        handle.unsubscribe()
        click.echo("\nUnsubscribed.")


@wallet.command(name="balance")
@click.argument("name")
@click.option("--currency", default="satoshi", show_default=True)
@CASHTOKEN_FLAG
def wallet_balance(name: str, currency: str, cashtoken: bool) -> None:
    """Show the BCH balance for wallet NAME, and optionally its CashToken holdings.

    Resolves the address from the local wallet store — no password required.
    Otherwise behaves identically to 'balance'.
    """
    record = _load_key_from_db(name)
    raw: int = NetworkAPI.get_balance(record.address, network=record.network.value)
    if currency == "satoshi":
        click.echo(f"{raw} satoshi")
    else:
        click.echo(satoshi_to_currency_cached(raw, currency))
    if cashtoken:
        utxos = NetworkAPI.get_unspent(record.address, network=record.network.value)
        agg = CashtokenUnspents(utxos)
        _print_cashtoken_balance(agg.tokendata)


@wallet.command(name="send")
@click.argument("name")
@click.argument("to")
@click.argument("amount")
@click.argument("currency")
@click.option("--fee", default=None, type=int, help="Fee in satoshi/byte")
@click.option("--message", default=None, help="OP_RETURN message")
@CATEGORY_ID_OPTION
@NFT_CAPABILITY_OPTION
@NFT_COMMITMENT_OPTION
@TOKEN_AMOUNT_OPTION
@PASSWORD_OPTION
def wallet_send(
    name: str,
    to: str,
    amount: str,
    currency: str,
    fee: int | None,
    message: str | None,
    category_id: str | None,
    nft_capability: str | None,
    nft_commitment: bytes | None,
    token_amount: int | None,
    password: str | None,
) -> None:
    """Decrypt wallet NAME and broadcast a signed BCH transaction.

    Password is required to decrypt the stored WIF; prompts interactively if
    omitted, or reads from BITCASH_WALLET_PASSWORD env var. Prints the
    transaction ID on success. CashToken behaviour is identical to 'send'.
    """
    record = _load_key_from_db(name)
    wif: str = _decrypt_wif(record, _prompt_password(password))
    key = wif_to_key(wif, regtest=(record.network == Network.regtest))
    output = _build_output(
        to, amount, currency, category_id, nft_capability, nft_commitment, token_amount
    )
    txid: str = key.send(
        [output],
        fee=fee,
        message=message,
    )
    click.echo(f"Transaction ID: {txid}")


@wallet.command(name="export")
@click.argument("name")
@PASSWORD_OPTION
def wallet_export(name: str, password: str | None) -> None:
    """Decrypt and print the WIF for wallet NAME.

    Password required. Treat the output as a secret — anyone with the WIF
    has full control of the funds.
    """
    record = _load_key_from_db(name)
    wif: str = _decrypt_wif(record, _prompt_password(password))
    click.echo(f"WIF: {wif}")


@wallet.command(name="delete")
@click.argument("name")
@click.confirmation_option(prompt="Are you sure you want to delete this wallet?")
def wallet_delete(name: str) -> None:
    """Remove wallet NAME from the local store.

    Asks for confirmation unless --yes is passed. Only deletes the local
    record — funds on-chain are unaffected. Fails if NAME does not exist.
    """
    db = _get_db()
    assert Query is not None
    removed = db.remove(Query().name == name)
    if not removed:
        raise click.ClickException(f"Wallet '{name}' not found.")
    click.echo(f"Wallet '{name}' deleted.")
