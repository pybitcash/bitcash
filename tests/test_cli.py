from unittest.mock import patch, MagicMock
import pytest
from click.testing import CliRunner
from tinydb import TinyDB
from tinydb.storages import MemoryStorage

from bitcash.cli import bitcash
import bitcash.cli as cli_module
from tests.samples import (
    WALLET_FORMAT_COMPRESSED_MAIN,
    WALLET_FORMAT_COMPRESSED_TEST,
    BITCOIN_CASHADDRESS_COMPRESSED,
    BITCOIN_CASHADDRESS_TEST_COMPRESSED,
)


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def isolated_db(monkeypatch):
    """Patch _get_db() to use an in-memory TinyDB."""
    db = TinyDB(storage=MemoryStorage)

    def _fake_get_db():
        return db

    monkeypatch.setattr(cli_module, "_get_db", _fake_get_db)
    return db


# ---------------------------------------------------------------------------
# TestNew
# ---------------------------------------------------------------------------


class TestNew:
    def test_new_mainnet(self, runner):
        result = runner.invoke(bitcash, ["new"])
        assert result.exit_code == 0
        assert "WIF:" in result.output
        assert "Address:" in result.output
        assert "bitcoincash:" in result.output

    def test_new_testnet(self, runner):
        result = runner.invoke(bitcash, ["new", "--network", "test"])
        assert result.exit_code == 0
        assert "bchtest:" in result.output

    def test_new_regtest(self, runner):
        result = runner.invoke(bitcash, ["new", "--network", "regtest"])
        assert result.exit_code == 0
        assert "bchreg:" in result.output


# ---------------------------------------------------------------------------
# TestGen
# ---------------------------------------------------------------------------


class TestGen:
    def test_gen_returns_address(self, runner):
        with patch(
            "bitcash.cli.generate_matching_address",
            return_value=("WIF123", "bitcoincash:qtest"),
        ):
            result = runner.invoke(bitcash, ["gen", "q"])
            assert result.exit_code == 0


# ---------------------------------------------------------------------------
# TestBalance
# ---------------------------------------------------------------------------


class TestBalance:
    def test_balance_satoshi(self, runner):
        with patch("bitcash.cli.NetworkAPI.get_balance", return_value=500000):
            result = runner.invoke(
                bitcash,
                ["balance", BITCOIN_CASHADDRESS_COMPRESSED],
            )
            assert result.exit_code == 0
            assert "500000 satoshi" in result.output

    def test_balance_zero(self, runner):
        with patch("bitcash.cli.NetworkAPI.get_balance", return_value=0):
            result = runner.invoke(
                bitcash,
                ["balance", BITCOIN_CASHADDRESS_COMPRESSED],
            )
            assert result.exit_code == 0
            assert "0 satoshi" in result.output

    def test_balance_testnet(self, runner):
        with patch("bitcash.cli.NetworkAPI.get_balance", return_value=100) as mock_bal:
            result = runner.invoke(
                bitcash,
                ["balance", BITCOIN_CASHADDRESS_TEST_COMPRESSED, "--network", "test"],
            )
            assert result.exit_code == 0
            mock_bal.assert_called_once_with(
                BITCOIN_CASHADDRESS_TEST_COMPRESSED, network="testnet"
            )


# ---------------------------------------------------------------------------
# TestTransactions
# ---------------------------------------------------------------------------


class TestTransactions:
    def test_transactions_found(self, runner):
        with patch(
            "bitcash.cli.NetworkAPI.get_transactions",
            return_value=["txid1", "txid2"],
        ):
            result = runner.invoke(
                bitcash, ["transactions", BITCOIN_CASHADDRESS_COMPRESSED]
            )
            assert result.exit_code == 0
            assert "txid1" in result.output
            assert "txid2" in result.output

    def test_transactions_empty(self, runner):
        with patch("bitcash.cli.NetworkAPI.get_transactions", return_value=[]):
            result = runner.invoke(
                bitcash, ["transactions", BITCOIN_CASHADDRESS_COMPRESSED]
            )
            assert result.exit_code == 0
            assert "No transactions found." in result.output


# ---------------------------------------------------------------------------
# TestUnspents
# ---------------------------------------------------------------------------


class TestUnspents:
    def test_unspents_found(self, runner):
        mock_utxo = MagicMock()
        mock_utxo.__str__ = MagicMock(return_value="Unspent(amount=1000, ...)")
        with patch(
            "bitcash.cli.NetworkAPI.get_unspent",
            return_value=[mock_utxo],
        ):
            result = runner.invoke(
                bitcash, ["unspents", BITCOIN_CASHADDRESS_COMPRESSED]
            )
            assert result.exit_code == 0
            assert "Unspent" in result.output

    def test_unspents_empty(self, runner):
        with patch("bitcash.cli.NetworkAPI.get_unspent", return_value=[]):
            result = runner.invoke(
                bitcash, ["unspents", BITCOIN_CASHADDRESS_COMPRESSED]
            )
            assert result.exit_code == 0
            assert "No unspents found." in result.output


# ---------------------------------------------------------------------------
# TestSend
# ---------------------------------------------------------------------------


class TestSend:
    def test_send_mainnet(self, runner):
        with patch("bitcash.cli.wif_to_key") as mock_wif:
            mock_key = MagicMock()
            mock_key.send.return_value = "deadbeef"
            mock_wif.return_value = mock_key
            result = runner.invoke(
                bitcash,
                [
                    "send",
                    "--wif",
                    WALLET_FORMAT_COMPRESSED_MAIN,
                    BITCOIN_CASHADDRESS_COMPRESSED,
                    "1000",
                    "satoshi",
                ],
            )
            assert result.exit_code == 0
            assert "deadbeef" in result.output

    def test_send_with_fee_and_message(self, runner):
        with patch("bitcash.cli.wif_to_key") as mock_wif:
            mock_key = MagicMock()
            mock_key.send.return_value = "cafebabe"
            mock_wif.return_value = mock_key
            result = runner.invoke(
                bitcash,
                [
                    "send",
                    "--wif",
                    WALLET_FORMAT_COMPRESSED_MAIN,
                    BITCOIN_CASHADDRESS_COMPRESSED,
                    "500",
                    "satoshi",
                    "--fee",
                    "2",
                    "--message",
                    "hello",
                ],
            )
            assert result.exit_code == 0
            mock_key.send.assert_called_once_with(
                [(BITCOIN_CASHADDRESS_COMPRESSED, "500", "satoshi")],
                fee=2,
                message="hello",
            )


# ---------------------------------------------------------------------------
# TestSubscribe
# ---------------------------------------------------------------------------


class TestSubscribe:
    def _make_fake_subscribe(self, *events):
        """Returns a subscribe side_effect that fires events synchronously."""

        def fake_subscribe(address, callback, network):
            for status_hash in events:
                callback(address, status_hash)
            return MagicMock()

        return fake_subscribe

    def test_subscribe_update(self, runner):
        with patch(
            "bitcash.cli.NetworkAPI.subscribe_address",
            side_effect=self._make_fake_subscribe("abc123def456", "unsubscribed"),
        ):
            result = runner.invoke(
                bitcash, ["subscribe", BITCOIN_CASHADDRESS_COMPRESSED]
            )
        assert result.exit_code == 0
        assert "abc123def456"[:12] in result.output
        assert "Unsubscribed" in result.output

    def test_subscribe_no_history(self, runner):
        with patch(
            "bitcash.cli.NetworkAPI.subscribe_address",
            side_effect=self._make_fake_subscribe(None, "unsubscribed"),
        ):
            result = runner.invoke(
                bitcash, ["subscribe", BITCOIN_CASHADDRESS_COMPRESSED]
            )
        assert result.exit_code == 0
        assert "no history" in result.output

    def test_subscribe_show_balance(self, runner):
        with (
            patch(
                "bitcash.cli.NetworkAPI.subscribe_address",
                side_effect=self._make_fake_subscribe("deadbeef1234", "unsubscribed"),
            ),
            patch("bitcash.cli.NetworkAPI.get_balance", return_value=42000),
        ):
            result = runner.invoke(
                bitcash,
                ["subscribe", BITCOIN_CASHADDRESS_COMPRESSED, "--show-balance"],
            )
        assert result.exit_code == 0
        assert "42000 sat" in result.output

    def test_subscribe_error_event(self, runner):
        with patch(
            "bitcash.cli.NetworkAPI.subscribe_address",
            side_effect=self._make_fake_subscribe("error:timeout", "unsubscribed"),
        ):
            result = runner.invoke(
                bitcash, ["subscribe", BITCOIN_CASHADDRESS_COMPRESSED]
            )
        assert result.exit_code == 0
        assert "Error:" in result.output


# ---------------------------------------------------------------------------
# TestWalletSubscribe
# ---------------------------------------------------------------------------


class TestWalletSubscribe:
    def _make_fake_subscribe(self, *events):
        def fake_subscribe(address, callback, network):
            for status_hash in events:
                callback(address, status_hash)
            return MagicMock()

        return fake_subscribe

    def test_wallet_subscribe(self, runner, isolated_db):
        runner.invoke(
            bitcash,
            [
                "wallet",
                "new",
                "watcher",
                "--wif",
                WALLET_FORMAT_COMPRESSED_MAIN,
                "--password",
                "pass",
            ],
        )
        with patch(
            "bitcash.cli.NetworkAPI.subscribe_address",
            side_effect=self._make_fake_subscribe("cafebabe5678", "unsubscribed"),
        ):
            result = runner.invoke(bitcash, ["wallet", "subscribe", "watcher"])
        assert result.exit_code == 0
        assert "cafebabe5678"[:12] in result.output

    def test_wallet_subscribe_not_found(self, runner, isolated_db):
        result = runner.invoke(bitcash, ["wallet", "subscribe", "ghost"])
        assert result.exit_code != 0
        assert "not found" in result.output


# ---------------------------------------------------------------------------
# TestWalletNew
# ---------------------------------------------------------------------------


class TestWalletNew:
    def test_wallet_new_generates_key(self, runner, isolated_db):
        result = runner.invoke(
            bitcash,
            ["wallet", "new", "mywallet", "--password", "secret"],
        )
        assert result.exit_code == 0, result.output
        assert "Wallet 'mywallet' created." in result.output
        assert "bitcoincash:" in result.output

    def test_wallet_new_import_wif(self, runner, isolated_db):
        result = runner.invoke(
            bitcash,
            [
                "wallet",
                "new",
                "imported",
                "--wif",
                WALLET_FORMAT_COMPRESSED_MAIN,
                "--password",
                "secret",
            ],
        )
        assert result.exit_code == 0, result.output
        assert BITCOIN_CASHADDRESS_COMPRESSED in result.output

    def test_wallet_new_duplicate_fails(self, runner, isolated_db):
        runner.invoke(bitcash, ["wallet", "new", "dupe", "--password", "pass"])
        result = runner.invoke(bitcash, ["wallet", "new", "dupe", "--password", "pass"])
        assert result.exit_code != 0
        assert "already exists" in result.output

    def test_wallet_new_wif_network_mismatch(self, runner, isolated_db):
        result = runner.invoke(
            bitcash,
            [
                "wallet",
                "new",
                "bad",
                "--wif",
                WALLET_FORMAT_COMPRESSED_MAIN,
                "--network",
                "test",
                "--password",
                "pass",
            ],
        )
        assert result.exit_code != 0
        assert "does not match" in result.output

    def test_wallet_new_testnet_wif(self, runner, isolated_db):
        result = runner.invoke(
            bitcash,
            [
                "wallet",
                "new",
                "testwallet",
                "--wif",
                WALLET_FORMAT_COMPRESSED_TEST,
                "--network",
                "test",
                "--password",
                "pass",
            ],
        )
        assert result.exit_code == 0, result.output
        assert BITCOIN_CASHADDRESS_TEST_COMPRESSED in result.output


# ---------------------------------------------------------------------------
# TestWalletList
# ---------------------------------------------------------------------------


class TestWalletList:
    def test_wallet_list_empty(self, runner, isolated_db):
        result = runner.invoke(bitcash, ["wallet", "list"])
        assert result.exit_code == 0
        assert "No wallets found." in result.output

    def test_wallet_list_shows_entries(self, runner, isolated_db):
        runner.invoke(
            bitcash,
            ["wallet", "new", "alpha", "--password", "pass"],
        )
        result = runner.invoke(bitcash, ["wallet", "list"])
        assert result.exit_code == 0
        assert "alpha" in result.output
        assert "main" in result.output


# ---------------------------------------------------------------------------
# TestWalletBalance
# ---------------------------------------------------------------------------


class TestWalletBalance:
    def test_wallet_balance_no_password(self, runner, isolated_db):
        runner.invoke(
            bitcash,
            ["wallet", "new", "richkey", "--password", "secret"],
        )
        with patch("bitcash.cli.NetworkAPI.get_balance", return_value=777):
            result = runner.invoke(bitcash, ["wallet", "balance", "richkey"])
        assert result.exit_code == 0
        assert "777 satoshi" in result.output

    def test_wallet_balance_not_found(self, runner, isolated_db):
        result = runner.invoke(bitcash, ["wallet", "balance", "ghost"])
        assert result.exit_code != 0
        assert "not found" in result.output


# ---------------------------------------------------------------------------
# TestWalletSend
# ---------------------------------------------------------------------------


class TestWalletSend:
    def test_wallet_send(self, runner, isolated_db):
        runner.invoke(
            bitcash,
            ["wallet", "new", "spender", "--password", "mypassword"],
        )
        with patch("bitcash.cli.wif_to_key") as mock_wif:
            mock_key = MagicMock()
            mock_key.send.return_value = "txhash123"
            mock_wif.return_value = mock_key
            result = runner.invoke(
                bitcash,
                [
                    "wallet",
                    "send",
                    "spender",
                    BITCOIN_CASHADDRESS_COMPRESSED,
                    "100",
                    "satoshi",
                    "--password",
                    "mypassword",
                ],
            )
        assert result.exit_code == 0, result.output
        assert "txhash123" in result.output

    def test_wallet_send_wrong_password(self, runner, isolated_db):
        runner.invoke(
            bitcash,
            ["wallet", "new", "spender2", "--password", "correct"],
        )
        result = runner.invoke(
            bitcash,
            [
                "wallet",
                "send",
                "spender2",
                BITCOIN_CASHADDRESS_COMPRESSED,
                "100",
                "satoshi",
                "--password",
                "wrong",
            ],
        )
        assert result.exit_code != 0
        assert "Incorrect password" in result.output


# ---------------------------------------------------------------------------
# TestWalletExport
# ---------------------------------------------------------------------------


class TestWalletExport:
    def test_wallet_export(self, runner, isolated_db):
        runner.invoke(
            bitcash,
            [
                "wallet",
                "new",
                "exportme",
                "--wif",
                WALLET_FORMAT_COMPRESSED_MAIN,
                "--password",
                "mypass",
            ],
        )
        result = runner.invoke(
            bitcash,
            ["wallet", "export", "exportme", "--password", "mypass"],
        )
        assert result.exit_code == 0, result.output
        assert WALLET_FORMAT_COMPRESSED_MAIN in result.output

    def test_wallet_export_wrong_password(self, runner, isolated_db):
        runner.invoke(
            bitcash,
            [
                "wallet",
                "new",
                "exportme2",
                "--wif",
                WALLET_FORMAT_COMPRESSED_MAIN,
                "--password",
                "correct",
            ],
        )
        result = runner.invoke(
            bitcash,
            ["wallet", "export", "exportme2", "--password", "wrong"],
        )
        assert result.exit_code != 0
        assert "Incorrect password" in result.output


# ---------------------------------------------------------------------------
# TestWalletDelete
# ---------------------------------------------------------------------------


class TestWalletDelete:
    def test_wallet_delete(self, runner, isolated_db):
        runner.invoke(
            bitcash,
            ["wallet", "new", "tobedeleted", "--password", "pass"],
        )
        result = runner.invoke(
            bitcash,
            ["wallet", "delete", "tobedeleted", "--yes"],
        )
        assert result.exit_code == 0, result.output
        assert "deleted" in result.output

        # Confirm it's gone
        result2 = runner.invoke(bitcash, ["wallet", "balance", "tobedeleted"])
        assert result2.exit_code != 0
        assert "not found" in result2.output

    def test_wallet_delete_not_found(self, runner, isolated_db):
        result = runner.invoke(
            bitcash,
            ["wallet", "delete", "nosuchname", "--yes"],
        )
        assert result.exit_code != 0
        assert "not found" in result.output


# ---------------------------------------------------------------------------
# Root group: no subcommand → help
# ---------------------------------------------------------------------------


class TestRootGroup:
    def test_no_subcommand_shows_help(self, runner):
        result = runner.invoke(bitcash, [])
        assert result.exit_code == 0
        assert "Usage:" in result.output
