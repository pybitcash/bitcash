from _pytest.monkeypatch import MonkeyPatch
from decimal import Decimal

from bitcash.network.APIs import FulcrumProtocolAPI as _fapi
from bitcash.network.transaction import Transaction, TxPart
from bitcash.network.APIs.FulcrumProtocolAPI import FulcrumProtocolAPI
from bitcash.network.meta import Unspent


BITCOIN_CASHADDRESS_CATKN = "bitcoincash:zrweeythv25ltpdypewr54prs6zd3nr5rcjhrnhy2v"


def dummy_handshake(hostname: str, port: int):
    return


class DummySendPayload:
    def __init__(self, return_result):
        self.return_result = return_result

    def __call__(self, sock, message, payload):
        return self.return_result[message]


class TestFulcrumProtolAPI:
    def setup_method(self):
        self.monkeypatch = MonkeyPatch()
        self.monkeypatch.setattr(_fapi, "handshake", dummy_handshake)
        self.api = FulcrumProtocolAPI("dummy.com:50002")

    def test_get_blockheight(self):
        return_result = {
            "height": 800_000,
            "hex": "abcdef",
        }
        self.monkeypatch.setattr(
            _fapi,
            "send_json_rpc_payload",
            DummySendPayload({"blockchain.headers.get_tip": return_result}),
        )
        blockheight = self.api.get_blockheight()
        assert blockheight == 800_000

    def test_get_balance(self):
        return_result = {"confirmed": 3000, "unconfirmed": 0}
        self.monkeypatch.setattr(
            _fapi,
            "send_json_rpc_payload",
            DummySendPayload({"blockchain.address.get_balance": return_result}),
        )
        balance = self.api.get_balance(BITCOIN_CASHADDRESS_CATKN)
        assert balance == 3000

        # zero return
        return_result = {"confirmed": 0, "unconfirmed": 0}
        self.monkeypatch.setattr(
            _fapi,
            "send_json_rpc_payload",
            DummySendPayload({"blockchain.address.get_balance": return_result}),
        )
        balance = self.api.get_balance(BITCOIN_CASHADDRESS_CATKN)
        assert balance == 0

    def test_get_transactions(self):
        return_result = [
            {
                "height": 5,
                "tx_hash": "ae3cdb099d52da7dd4b1e16762b5788fd151e69836a45aba53adcecb02fccb4a",
            },
            {
                "height": 4,
                "tx_hash": "d07ee04f7e5792ae848b778c8b802283aff77413865582ebba3f3c7c016e82a9",
            },
            {
                "height": 3,
                "tx_hash": "2cd47128e4af9ab1c3df0bce0305c2bbf5ad7fdecbba3c0b73766294bc88eaf8",
            },
            {
                "height": 2,
                "tx_hash": "616c8f5c64847645a9052d9aec822abf6fb526ec7b01cc918e392cdf24df8f89",
            },
            {
                "height": 1,
                "tx_hash": "2c39cebc1ea104243f87d78a522ec1d499d98ffc2f145c08d474889573300dd7",
            },
        ]
        self.monkeypatch.setattr(
            _fapi,
            "send_json_rpc_payload",
            DummySendPayload({"blockchain.address.get_history": return_result}),
        )
        transactions = self.api.get_transactions(BITCOIN_CASHADDRESS_CATKN)

        assert transactions == [
            "ae3cdb099d52da7dd4b1e16762b5788fd151e69836a45aba53adcecb02fccb4a",
            "d07ee04f7e5792ae848b778c8b802283aff77413865582ebba3f3c7c016e82a9",
            "2cd47128e4af9ab1c3df0bce0305c2bbf5ad7fdecbba3c0b73766294bc88eaf8",
            "616c8f5c64847645a9052d9aec822abf6fb526ec7b01cc918e392cdf24df8f89",
            "2c39cebc1ea104243f87d78a522ec1d499d98ffc2f145c08d474889573300dd7",
        ]

        # zero return
        return_result = []
        self.monkeypatch.setattr(
            _fapi,
            "send_json_rpc_payload",
            DummySendPayload({"blockchain.address.get_history": return_result}),
        )
        transactions = self.api.get_transactions(BITCOIN_CASHADDRESS_CATKN)

        assert transactions == []

    def test_get_transaction(self):
        # since the get_raw_tx sends the same tx at each vin, the vin at index 0 matches
        # vout at index 0 and same for vin at index 1.
        return_result = {
            "blockhash": "0000000000000000007c302f8790f32efb996a9d162408ce930e0e70ee3cbe8d",
            "blocktime": 1684161846,
            "confirmations": 52305,
            "hash": "446f83e975d2870de740917df1b5221aa4bc52c6e2540188f5897c4ce775b7f4",
            "hex": "0200000002cff9a2b2ba6fa0c0bb958ead6178256bd354c3f63030eecd51e34d604fd9738400000000644177033dfa31b3ab4ad8a147d0b7bd10da60e7fe1df51bf1767f5ba7273767d7ffad55feec5c201ea89c6c07a1c8368d8a378aae2f48ddd2076324769b2c23a1ac4121031aa8f87cde6c87de9bf1bdb9e575801a754d2a600be4d1fc89e36eae6db63bc600000000cf9a546cb9d6997c68c3c92a2daa658ef8e8778a30e92d7da0b963d0a213ef79010000006441b818b5c19459d64c4f16ac8fbaff844a6c0d05de8cf563173737d56908de56033a1e367f3c7cae8cf3240af06659bcde09d543bc064e208a31d576bbf074bb714121031aa8f87cde6c87de9bf1bdb9e575801a754d2a600be4d1fc89e36eae6db63bc60000000003e80300000000000044efcff9a2b2ba6fa0c0bb958ead6178256bd354c3f63030eecd51e34d604fd9738410ff0078a6982000000076a9148ee26d6c9f58369f94864dc3630cdeb17fae2f2d88ac0000000000000000706a0442434d52206b2000be5ce5527cd653c49cdba486e2fd0ec4214da2f71d7e56ad027b2139f448676973742e67697468756275736572636f6e74656e742e636f6d2f6d722d7a776574732f38346230303537383038616632306466333932383135666232376434613636312f72617745430000000000001976a9148ee26d6c9f58369f94864dc3630cdeb17fae2f2d88ac00000000",
            "locktime": 0,
            "size": 524,
            "time": 1684161846,
            "txid": "446f83e975d2870de740917df1b5221aa4bc52c6e2540188f5897c4ce775b7f4",
            "version": 2,
            "vin": [
                {
                    "scriptSig": {
                        "asm": "77033dfa31b3ab4ad8a147d0b7bd10da60e7fe1df51bf1767f5ba7273767d7ffad55feec5c201ea89c6c07a1c8368d8a378aae2f48ddd2076324769b2c23a1ac[ALL|FORKID] 031aa8f87cde6c87de9bf1bdb9e575801a754d2a600be4d1fc89e36eae6db63bc6",
                        "hex": "4177033dfa31b3ab4ad8a147d0b7bd10da60e7fe1df51bf1767f5ba7273767d7ffad55feec5c201ea89c6c07a1c8368d8a378aae2f48ddd2076324769b2c23a1ac4121031aa8f87cde6c87de9bf1bdb9e575801a754d2a600be4d1fc89e36eae6db63bc6",
                    },
                    "sequence": 0,
                    "txid": "446f83e975d2870de740917df1b5221aa4bc52c6e2540188f5897c4ce775b7f4",
                    "vout": 0,
                },
                {
                    "scriptSig": {
                        "asm": "b818b5c19459d64c4f16ac8fbaff844a6c0d05de8cf563173737d56908de56033a1e367f3c7cae8cf3240af06659bcde09d543bc064e208a31d576bbf074bb71[ALL|FORKID] 031aa8f87cde6c87de9bf1bdb9e575801a754d2a600be4d1fc89e36eae6db63bc6",
                        "hex": "41b818b5c19459d64c4f16ac8fbaff844a6c0d05de8cf563173737d56908de56033a1e367f3c7cae8cf3240af06659bcde09d543bc064e208a31d576bbf074bb714121031aa8f87cde6c87de9bf1bdb9e575801a754d2a600be4d1fc89e36eae6db63bc6",
                    },
                    "sequence": 0,
                    "txid": "446f83e975d2870de740917df1b5221aa4bc52c6e2540188f5897c4ce775b7f4",
                    "vout": 1,
                },
            ],
            "vout": [
                {
                    "n": 0,
                    "scriptPubKey": {
                        "addresses": [
                            "bitcoincash:qz8wymtvnavrd8u5sexuxccvm6chlt3095hczr7px4"
                        ],
                        "asm": "OP_DUP OP_HASH160 8ee26d6c9f58369f94864dc3630cdeb17fae2f2d OP_EQUALVERIFY OP_CHECKSIG",
                        "hex": "76a9148ee26d6c9f58369f94864dc3630cdeb17fae2f2d88ac",
                        "reqSigs": 1,
                        "type": "pubkeyhash",
                    },
                    "tokenData": {
                        "amount": "140000000000",
                        "category": "8473d94f604de351cdee3030f6c354d36b257861ad8e95bbc0a06fbab2a2f9cf",
                    },
                    "value": Decimal("0.00001"),
                },
                {
                    "n": 1,
                    "scriptPubKey": {
                        "asm": "OP_RETURN 1380795202 6b2000be5ce5527cd653c49cdba486e2fd0ec4214da2f71d7e56ad027b2139f4 676973742e67697468756275736572636f6e74656e742e636f6d2f6d722d7a776574732f38346230303537383038616632306466333932383135666232376434613636312f726177",
                        "hex": "6a0442434d52206b2000be5ce5527cd653c49cdba486e2fd0ec4214da2f71d7e56ad027b2139f448676973742e67697468756275736572636f6e74656e742e636f6d2f6d722d7a776574732f38346230303537383038616632306466333932383135666232376434613636312f726177",
                        "type": "nulldata",
                    },
                    "value": 0,
                },
            ],
        }
        self.monkeypatch.setattr(
            _fapi,
            "send_json_rpc_payload",
            DummySendPayload(
                {
                    "blockchain.transaction.get": return_result,
                    "blockchain.headers.get_tip": {"height": 845080},
                }
            ),
        )
        transaction = self.api.get_transaction(BITCOIN_CASHADDRESS_CATKN)
        tx = Transaction(
            "446f83e975d2870de740917df1b5221aa4bc52c6e2540188f5897c4ce775b7f4",
            792776,
            1000,
            1000,
            0,
        )
        tx.inputs = [
            TxPart(
                "bitcoincash:qz8wymtvnavrd8u5sexuxccvm6chlt3095hczr7px4",
                1000,
                category_id="8473d94f604de351cdee3030f6c354d36b257861ad8e95bbc0a06fbab2a2f9cf",
                token_amount=140000000000,
                data_hex="76a9148ee26d6c9f58369f94864dc3630cdeb17fae2f2d88ac",
            ),
            TxPart(
                None,
                0,
                data_hex="6a0442434d52206b2000be5ce5527cd653c49cdba486e2fd0ec4214da2f71d7e56ad027b2139f448676973742e67697468756275736572636f6e74656e742e636f6d2f6d722d7a776574732f38346230303537383038616632306466333932383135666232376434613636312f726177",
            ),
        ]
        tx.outputs = [
            TxPart(
                "bitcoincash:qz8wymtvnavrd8u5sexuxccvm6chlt3095hczr7px4",
                1000,
                category_id="8473d94f604de351cdee3030f6c354d36b257861ad8e95bbc0a06fbab2a2f9cf",
                token_amount=140000000000,
                data_hex="76a9148ee26d6c9f58369f94864dc3630cdeb17fae2f2d88ac",
            ),
            TxPart(
                None,
                0,
                data_hex="6a0442434d52206b2000be5ce5527cd653c49cdba486e2fd0ec4214da2f71d7e56ad027b2139f448676973742e67697468756275736572636f6e74656e742e636f6d2f6d722d7a776574732f38346230303537383038616632306466333932383135666232376434613636312f726177",
            ),
        ]

        print(transaction.to_dict())
        print(tx.to_dict())
        assert transaction == tx

        # unconfirmed tx
        for x in ["blockhash", "blocktime", "confirmations", "time"]:
            return_result.pop(x)
        self.monkeypatch.setattr(
            _fapi,
            "send_json_rpc_payload",
            DummySendPayload(
                {
                    "blockchain.transaction.get": return_result,
                    "blockchain.headers.get_tip": {"height": 845080},
                }
            ),
        )
        transaction = self.api.get_transaction(BITCOIN_CASHADDRESS_CATKN)
        tx.block = None
        assert transaction == tx

    def test_get_tx_amount(self):
        return_result = {
            "blockhash": "00000000000000000098d704446b13bb34ebeeabb687edd4e5f930a5ebfcb8b1",
            "blocktime": 1715277577,
            "confirmations": 2,
            "hash": "faea8b55d0a08422a9a363747b5737f9d18a54dbe70dab4c8e8cd89946c173b4",
            "hex": "0100000001cd00487abcfb3a1209d866a2cdb63ef24f3d834e512feaa67ba5ae45155d0766010000006a473044022027d433db2a43816d51707f8126529168788001cfa795fc6484616d60ad2147300220389c8fc40a31133fab1a6757000e32f965d7c5f1ae5c4b2b91e92982a8fe2983412103b632b7037149d41ebaf9ed21321cb5f811f3c61bd6102192e3447cd113040dfaffffffff026e4d23e3000000001976a91411f3e637d0925951f379ee6ef151ccc04873c27488ac6a205300000000001976a9149b0a33f7858e3e3b46298da95e63f2745a66056f88ac00000000",
            "locktime": 0,
            "size": 225,
            "time": 1715277577,
            "txid": "faea8b55d0a08422a9a363747b5737f9d18a54dbe70dab4c8e8cd89946c173b4",
            "version": 1,
            "vin": [
                {
                    "scriptSig": {
                        "asm": "3044022027d433db2a43816d51707f8126529168788001cfa795fc6484616d60ad2147300220389c8fc40a31133fab1a6757000e32f965d7c5f1ae5c4b2b91e92982a8fe2983[ALL|FORKID] 03b632b7037149d41ebaf9ed21321cb5f811f3c61bd6102192e3447cd113040dfa",
                        "hex": "473044022027d433db2a43816d51707f8126529168788001cfa795fc6484616d60ad2147300220389c8fc40a31133fab1a6757000e32f965d7c5f1ae5c4b2b91e92982a8fe2983412103b632b7037149d41ebaf9ed21321cb5f811f3c61bd6102192e3447cd113040dfa",
                    },
                    "sequence": 4294967295,
                    "txid": "66075d1545aea57ba6ea2f514e833d4ff23eb6cda266d809123afbbc7a4800cd",
                    "vout": 1,
                }
            ],
            "vout": [
                {
                    "n": 0,
                    "scriptPubKey": {
                        "addresses": [
                            "bitcoincash:qqgl8e3h6zf9j50n08hxau23enqysu7zwscgz405rc"
                        ],
                        "asm": "OP_DUP OP_HASH160 11f3e637d0925951f379ee6ef151ccc04873c274 OP_EQUALVERIFY OP_CHECKSIG",
                        "hex": "76a91411f3e637d0925951f379ee6ef151ccc04873c27488ac",
                        "reqSigs": 1,
                        "type": "pubkeyhash",
                    },
                    "value": Decimal("38.10741614"),
                },
                {
                    "n": 1,
                    "scriptPubKey": {
                        "addresses": [
                            "bitcoincash:qzds5vlhsk8ruw6x9xx6jhnr7f695es9duz4ctlv4a"
                        ],
                        "asm": "OP_DUP OP_HASH160 9b0a33f7858e3e3b46298da95e63f2745a66056f OP_EQUALVERIFY OP_CHECKSIG",
                        "hex": "76a9149b0a33f7858e3e3b46298da95e63f2745a66056f88ac",
                        "reqSigs": 1,
                        "type": "pubkeyhash",
                    },
                    "value": Decimal("0.05447786"),
                },
            ],
        }
        self.monkeypatch.setattr(
            _fapi,
            "send_json_rpc_payload",
            DummySendPayload({"blockchain.transaction.get": return_result}),
        )
        amount = self.api.get_tx_amount(
            "faea8b55d0a08422a9a363747b5737f9d18a54dbe70dab4c8e8cd89946c173b4", 0
        )
        assert amount == 3810741614

    def test_get_unspent(self):
        return_result = [
            {
                "height": 825636,
                "token_data": {
                    "amount": "10000",
                    "category": "357dc834af514958b5cb9d5407c26af12e81f442599fbfb99f108563cea126f0",
                },
                "tx_hash": "bfd2f488f33a77fced7ea4d0bc694ab64fadb0e0f66bf101438b3eb88b2411c3",
                "tx_pos": 0,
                "value": 657,
            },
            {
                "height": 825636,
                "token_data": {
                    "amount": "10000",
                    "category": "afe979e6b52e37d29f6c4d7edd922bddb91b5e4d55ebfa8cd59a0f90bc03b802",
                    "nft": {"capability": "none", "commitment": "62697463617368"},
                },
                "tx_hash": "bfd2f488f33a77fced7ea4d0bc694ab64fadb0e0f66bf101438b3eb88b2411c3",
                "tx_pos": 1,
                "value": 681,
            },
            {
                "height": 825636,
                "token_data": {
                    "amount": "0",
                    "category": "afe979e6b52e37d29f6c4d7edd922bddb91b5e4d55ebfa8cd59a0f90bc03b802",
                    "nft": {"capability": "minting", "commitment": ""},
                },
                "tx_hash": "bfd2f488f33a77fced7ea4d0bc694ab64fadb0e0f66bf101438b3eb88b2411c3",
                "tx_pos": 2,
                "value": 648,
            },
            {
                "height": 825636,
                "token_data": {
                    "amount": "10000",
                    "category": "60f451f3cb0ea81fd6c68cf2d42b708bfdf6d74cd08d75c8a7a515ff8adce4ae",
                    "nft": {"capability": "minting", "commitment": ""},
                },
                "tx_hash": "bfd2f488f33a77fced7ea4d0bc694ab64fadb0e0f66bf101438b3eb88b2411c3",
                "tx_pos": 3,
                "value": 895078,
            },
        ]
        self.monkeypatch.setattr(
            _fapi,
            "send_json_rpc_payload",
            DummySendPayload(
                {
                    "blockchain.address.listunspent": return_result,
                    "blockchain.headers.get_tip": {"height": 845080},
                }
            ),
        )
        unspents = self.api.get_unspent(BITCOIN_CASHADDRESS_CATKN)
        assert unspents == [
            Unspent(
                amount=657,
                confirmations=19445,
                script="76a914dd9c917762a9f585a40e5c3a54238684d8cc741e88ac",
                txid="bfd2f488f33a77fced7ea4d0bc694ab64fadb0e0f66bf101438b3eb88b2411c3",
                txindex=0,
                category_id="357dc834af514958b5cb9d5407c26af12e81f442599fbfb99f108563cea126f0",
                token_amount=10000,
            ),
            Unspent(
                amount=681,
                confirmations=19445,
                script="76a914dd9c917762a9f585a40e5c3a54238684d8cc741e88ac",
                txid="bfd2f488f33a77fced7ea4d0bc694ab64fadb0e0f66bf101438b3eb88b2411c3",
                txindex=1,
                category_id="afe979e6b52e37d29f6c4d7edd922bddb91b5e4d55ebfa8cd59a0f90bc03b802",
                nft_capability="none",
                nft_commitment=b"bitcash",
                token_amount=10000,
            ),
            Unspent(
                amount=648,
                confirmations=19445,
                script="76a914dd9c917762a9f585a40e5c3a54238684d8cc741e88ac",
                txid="bfd2f488f33a77fced7ea4d0bc694ab64fadb0e0f66bf101438b3eb88b2411c3",
                txindex=2,
                category_id="afe979e6b52e37d29f6c4d7edd922bddb91b5e4d55ebfa8cd59a0f90bc03b802",
                nft_capability="minting",
            ),
            Unspent(
                amount=895078,
                confirmations=19445,
                script="76a914dd9c917762a9f585a40e5c3a54238684d8cc741e88ac",
                txid="bfd2f488f33a77fced7ea4d0bc694ab64fadb0e0f66bf101438b3eb88b2411c3",
                txindex=3,
                category_id="60f451f3cb0ea81fd6c68cf2d42b708bfdf6d74cd08d75c8a7a515ff8adce4ae",
                nft_capability="minting",
                token_amount=10000,
            ),
        ]

        # zero return
        return_result = []
        self.monkeypatch.setattr(
            _fapi,
            "send_json_rpc_payload",
            DummySendPayload(
                {
                    "blockchain.address.listunspent": return_result,
                    "blockchain.headers.get_tip": {"height": 845080},
                }
            ),
        )
        unspents = self.api.get_unspent(BITCOIN_CASHADDRESS_CATKN)
        assert unspents == []

    def test_get_raw_transaction(self):
        return_result = {"dummy": "dummy"}
        self.monkeypatch.setattr(
            _fapi,
            "send_json_rpc_payload",
            DummySendPayload({"blockchain.transaction.get": return_result}),
        )
        tx = self.api.get_raw_transaction(
            "446f83e975d2870de740917df1b5221aa4bc52c6e2540188f5897c4ce775b7f4",
        )
        assert tx == {"dummy": "dummy"}
