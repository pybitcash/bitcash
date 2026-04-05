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

from bitcash.keygen import generate_matching_address
from bitcash.wallet import PrivateKey, wif_to_key
from bitcash.network import NetworkAPI, satoshi_to_currency_cached
from bitcash.types import Network, UserOutput


# ---------------------------------------------------------------------------
# Shared option — callback converts the CLI string to a Network enum member
# ---------------------------------------------------------------------------

def _parse_network(
    ctx: click.Context, param: click.Parameter, value: str
) -> Network:
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
# Root group
# ---------------------------------------------------------------------------


@click.group(invoke_without_command=True)
@click.pass_context
def bitcash(ctx: click.Context) -> None:
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


# ---------------------------------------------------------------------------
# gen
# ---------------------------------------------------------------------------


@bitcash.command()  # pyright: ignore
@click.argument("prefix")
@click.option("--cores", "-c", default="all")
def gen(prefix: str, cores: str) -> None:
    """Generate a vanity address matching PREFIX."""
    click.echo(generate_matching_address(prefix, cores))


# ---------------------------------------------------------------------------
# new
# ---------------------------------------------------------------------------


@bitcash.command(name="new")
@NETWORK_OPTION
def new_cmd(network: Network) -> None:
    """Generate a new private key and print WIF + address."""
    key = PrivateKey(network=network.name)
    click.echo(f"WIF:     {key.to_wif()}")
    click.echo(f"Address: {key.address}")


# ---------------------------------------------------------------------------
# balance
# ---------------------------------------------------------------------------


@bitcash.command()
@click.argument("address")
@click.option("--currency", default="satoshi", show_default=True)
@NETWORK_OPTION
def balance(address: str, currency: str, network: Network) -> None:
    """Show the balance of ADDRESS."""
    raw: int = NetworkAPI.get_balance(address, network=network.value)
    if currency == "satoshi":
        click.echo(f"{raw} satoshi")
    else:
        click.echo(satoshi_to_currency_cached(raw, currency))


# ---------------------------------------------------------------------------
# transactions
# ---------------------------------------------------------------------------


@bitcash.command()
@click.argument("address")
@NETWORK_OPTION
def transactions(address: str, network: Network) -> None:
    """List transactions for ADDRESS."""
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
    """List unspent outputs for ADDRESS."""
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
@click.option("--show-balance", is_flag=True, help="Fetch and print balance on each update")
@NETWORK_OPTION
def subscribe_cmd(address: str, show_balance: bool, network: Network) -> None:
    """Watch ADDRESS for real-time transaction activity."""
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
                click.echo(f"[{ts}] {addr}  status={status_hash[:12]}…  balance={bal} sat")
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
@NETWORK_OPTION
def send_cmd(
    wif: str,
    to: str,
    amount: str,
    currency: str,
    fee: int | None,
    message: str | None,
    network: Network,
) -> None:
    """Send BCH using a raw WIF key."""
    key = wif_to_key(wif, regtest=(network == Network.regtest))
    # UserOutput types amount as int but the implementation accepts any
    # Decimal-compatible value; cast to satisfy the type checker.
    txid: str = key.send(
        cast(list[UserOutput], [(to, amount, currency)]),
        fee=fee,
        message=message,
    )
    click.echo(f"Transaction ID: {txid}")


# ---------------------------------------------------------------------------
# wallet subgroup
# ---------------------------------------------------------------------------


@bitcash.group()
def wallet() -> None:
    """Manage named, password-protected wallets."""


@wallet.command(name="new")
@click.argument("name")
@click.option("--wif", default=None, help="Import existing WIF (optional)")
@NETWORK_OPTION
@PASSWORD_OPTION
def wallet_new(name: str, wif: str | None, network: Network, password: str | None) -> None:
    """Create or import a named wallet."""
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
    """List all stored wallets."""
    db = _get_db()
    records = [WalletRecord.from_dict(r) for r in db.all()]
    if not records:
        click.echo("No wallets found.")
    else:
        for r in records:
            click.echo(f"{r.name:20s}  {r.network.name:8s}  {r.address}")


@wallet.command(name="subscribe")
@click.argument("name")
@click.option("--show-balance", is_flag=True, help="Fetch and print balance on each update")
def wallet_subscribe(name: str, show_balance: bool) -> None:
    """Watch wallet NAME for real-time transaction activity."""
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
                click.echo(f"[{ts}] {addr}  status={status_hash[:12]}…  balance={bal} sat")
            else:
                click.echo(f"[{ts}] {addr}  status={status_hash[:12]}…")

    click.echo(f"Subscribing to {name} ({address}) on {record.network.name}. Press Ctrl+C to stop.")
    handle = NetworkAPI.subscribe_address(address, on_update, network=record.network.value)

    try:
        stop_event.wait()
    except KeyboardInterrupt:
        handle.unsubscribe()
        click.echo("\nUnsubscribed.")


@wallet.command(name="balance")
@click.argument("name")
@click.option("--currency", default="satoshi", show_default=True)
def wallet_balance(name: str, currency: str) -> None:
    """Show balance for wallet NAME (no password required)."""
    record = _load_key_from_db(name)
    raw: int = NetworkAPI.get_balance(record.address, network=record.network.value)
    if currency == "satoshi":
        click.echo(f"{raw} satoshi")
    else:
        click.echo(satoshi_to_currency_cached(raw, currency))


@wallet.command(name="send")
@click.argument("name")
@click.argument("to")
@click.argument("amount")
@click.argument("currency")
@click.option("--fee", default=None, type=int, help="Fee in satoshi/byte")
@click.option("--message", default=None, help="OP_RETURN message")
@PASSWORD_OPTION
def wallet_send(
    name: str,
    to: str,
    amount: str,
    currency: str,
    fee: int | None,
    message: str | None,
    password: str | None,
) -> None:
    """Send BCH from wallet NAME."""
    record = _load_key_from_db(name)
    wif: str = _decrypt_wif(record, _prompt_password(password))
    key = wif_to_key(wif, regtest=(record.network == Network.regtest))
    txid: str = key.send(
        cast(list[UserOutput], [(to, amount, currency)]),
        fee=fee,
        message=message,
    )
    click.echo(f"Transaction ID: {txid}")


@wallet.command(name="export")
@click.argument("name")
@PASSWORD_OPTION
def wallet_export(name: str, password: str | None) -> None:
    """Decrypt and print the WIF for wallet NAME."""
    record = _load_key_from_db(name)
    wif: str = _decrypt_wif(record, _prompt_password(password))
    click.echo(f"WIF: {wif}")


@wallet.command(name="delete")
@click.argument("name")
@click.confirmation_option(prompt="Are you sure you want to delete this wallet?")
def wallet_delete(name: str) -> None:
    """Delete wallet NAME."""
    db = _get_db()
    assert Query is not None
    removed = db.remove(Query().name == name)
    if not removed:
        raise click.ClickException(f"Wallet '{name}' not found.")
    click.echo(f"Wallet '{name}' deleted.")
