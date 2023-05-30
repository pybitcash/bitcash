import pytest
from _pytest.monkeypatch import MonkeyPatch
from bitcash.network.APIs import BitcoinDotComAPI as _bapi

from bitcash.network.transaction import Transaction, TxPart
from bitcash.network.APIs.BitcoinDotComAPI import BitcoinDotComAPI
from bitcash.network.meta import Unspent


BITCOIN_CASHADDRESS_CATKN = "bitcoincash:zzfyvx77v2pmgc0vulwlfkl3uzjgh5gnmq37yf2mzf"


class DummyRequest:

    def __init__(self, return_json):
        self.return_json = return_json

    def json(self, *args, **kwargs):
        return self.return_json

    def raise_for_status(self):
        pass


class DummySession:

    def __init__(self, return_json):
        self.return_json = return_json

    def get(self, url, *args, **kwargs):
        return DummyRequest(self.return_json)


class TestBitcoinDotComAPI:

    def setup_method(self):
        self.monkeypatch = MonkeyPatch()
        self.api = BitcoinDotComAPI("https://dummy.com/v2/")

    def test_get_balance(self):
        return_json = {
            "balanceSat": 2500,
            "unconfirmedBalanceSat": 500,
            "balance": 0.00899289,
            "unconfirmedBalance": 0,
            "transactions": [
              "afe979e6b52e37d29f6c4d7edd922bddb91b5e4d55ebfa8cd59a0f90bc03b802",
              "311e30abebb9d6b35d3d02308bec3985988aa0ef997bffa7bca821fe6094f17f",
              "fec7bff45086ac961e8f2289a9f280f7710144979a61b0a11121f674fed85b15"
            ],
            "txAppearances": 3,
            "unconfirmedTxAppearances": 0,
            "totalReceived": 0.02699026,
            "totalReceivedSat": 2699026,
            "totalSent": 0.01799737,
            "totalSentSat": 1799737,
            "legacyAddress": "1MCmtwrNwGdBAJ42MfAn4UKEns17tGQTAs",
            "cashAddress": "bitcoincash:qrweeythv25ltpdypewr54prs6zd3nr5rc4asdez4l",
            "slpAddress": "simpleledger:qrweeythv25ltpdypewr54prs6zd3nr5rcexmkvztp",
            "currentPage": 0,
            "pagesTotal": None
        }
        self.monkeypatch.setattr(_bapi,
                                 "session",
                                 DummySession(return_json))
        balance = self.api.get_balance(BITCOIN_CASHADDRESS_CATKN)
        assert balance == 3000

        # zero return
        return_json = {
            "balanceSat": 0,
            "unconfirmedBalanceSat": 0,
            "balance": 0,
            "unconfirmedBalance": 0,
            "transactions": [],
            "txAppearances": 0,
            "unconfirmedTxAppearances": 0,
            "totalReceived": 0,
            "totalReceivedSat": 0,
            "totalSent": 0,
            "totalSentSat": 0,
            "legacyAddress": "1AaY9371BsWXnLDz1jD4PYeuehA2PMidZY",
            "cashAddress": "bitcoincash:qp53pksewwhtufkkcs76ycl5nq9t0kr6kq4uwkyu54",
            "slpAddress": "simpleledger:qp53pksewwhtufkkcs76ycl5nq9t0kr6kqe89d3u2t",
            "currentPage": 0,
            "pagesTotal": None
        }
        self.monkeypatch.setattr(_bapi,
                                 "session",
                                 DummySession(return_json))
        balance = self.api.get_balance(BITCOIN_CASHADDRESS_CATKN)
        assert balance == 0

    def test_get_transactions(self):
        return_json = {
            "balanceSat": 2500,
            "unconfirmedBalanceSat": 500,
            "balance": 0.00899289,
            "unconfirmedBalance": 0,
            "transactions": [
              "ae3cdb099d52da7dd4b1e16762b5788fd151e69836a45aba53adcecb02fccb4a",
              "d07ee04f7e5792ae848b778c8b802283aff77413865582ebba3f3c7c016e82a9",
              "2cd47128e4af9ab1c3df0bce0305c2bbf5ad7fdecbba3c0b73766294bc88eaf8",
              "616c8f5c64847645a9052d9aec822abf6fb526ec7b01cc918e392cdf24df8f89",
              "2c39cebc1ea104243f87d78a522ec1d499d98ffc2f145c08d474889573300dd7"
            ],
            "txAppearances": 3,
            "unconfirmedTxAppearances": 0,
            "totalReceived": 0.02699026,
            "totalReceivedSat": 2699026,
            "totalSent": 0.01799737,
            "totalSentSat": 1799737,
            "legacyAddress": "1MCmtwrNwGdBAJ42MfAn4UKEns17tGQTAs",
            "cashAddress": "bitcoincash:qrweeythv25ltpdypewr54prs6zd3nr5rc4asdez4l",
            "slpAddress": "simpleledger:qrweeythv25ltpdypewr54prs6zd3nr5rcexmkvztp",
            "currentPage": 0,
            "pagesTotal": None
        }
        self.monkeypatch.setattr(_bapi,
                                 "session",
                                 DummySession(return_json))
        transactions = self.api.get_transactions(BITCOIN_CASHADDRESS_CATKN)

        assert transactions == ["ae3cdb099d52da7dd4b1e16762b5788fd151e69836a45aba53adcecb02fccb4a",
                                "d07ee04f7e5792ae848b778c8b802283aff77413865582ebba3f3c7c016e82a9",
                                "2cd47128e4af9ab1c3df0bce0305c2bbf5ad7fdecbba3c0b73766294bc88eaf8",
                                "616c8f5c64847645a9052d9aec822abf6fb526ec7b01cc918e392cdf24df8f89",
                                "2c39cebc1ea104243f87d78a522ec1d499d98ffc2f145c08d474889573300dd7"]

        # zero return
        return_json = {
            "balanceSat": 0,
            "unconfirmedBalanceSat": 0,
            "balance": 0,
            "unconfirmedBalance": 0,
            "transactions": [],
            "txAppearances": 0,
            "unconfirmedTxAppearances": 0,
            "totalReceived": 0,
            "totalReceivedSat": 0,
            "totalSent": 0,
            "totalSentSat": 0,
            "legacyAddress": "1AaY9371BsWXnLDz1jD4PYeuehA2PMidZY",
            "cashAddress": "bitcoincash:qp53pksewwhtufkkcs76ycl5nq9t0kr6kq4uwkyu54",
            "slpAddress": "simpleledger:qp53pksewwhtufkkcs76ycl5nq9t0kr6kqe89d3u2t",
            "currentPage": 0,
            "pagesTotal": None
        }
        self.monkeypatch.setattr(_bapi,
                                 "session",
                                 DummySession(return_json))
        transactions = self.api.get_transactions(BITCOIN_CASHADDRESS_CATKN)

        assert transactions == []

    def test_get_transaction(self):
        return_json = {
            "in_mempool": False,
            "in_orphanpool": False,
            "txid": "446f83e975d2870de740917df1b5221aa4bc52c6e2540188f5897c4ce775b7f4",
            "size": 524,
            "version": 2,
            "locktime": 0,
            "vin": [
              {
                "txid": "8473d94f604de351cdee3030f6c354d36b257861ad8e95bbc0a06fbab2a2f9cf",
                "vout": 0,
                "scriptSig": {
                  "asm": "77033dfa31b3ab4ad8a147d0b7bd10da60e7fe1df51bf1767f5ba7273767d7ffad55feec5c201ea89c6c07a1c8368d8a378aae2f48ddd2076324769b2c23a1ac41 031aa8f87cde6c87de9bf1bdb9e575801a754d2a600be4d1fc89e36eae6db63bc6",
                  "hex": "4177033dfa31b3ab4ad8a147d0b7bd10da60e7fe1df51bf1767f5ba7273767d7ffad55feec5c201ea89c6c07a1c8368d8a378aae2f48ddd2076324769b2c23a1ac4121031aa8f87cde6c87de9bf1bdb9e575801a754d2a600be4d1fc89e36eae6db63bc6"
                },
                "sequence": 0,
                "cashAddress": "bitcoincash:qz8wymtvnavrd8u5sexuxccvm6chlt3095hczr7px4",
                "n": 0,
                "value": 0.0001
              },
              {
                "txid": "79ef13a2d063b9a07d2de9308a77e8f88e65aa2d2ac9c3687c99d6b96c549acf",
                "vout": 1,
                "scriptSig": {
                  "asm": "b818b5c19459d64c4f16ac8fbaff844a6c0d05de8cf563173737d56908de56033a1e367f3c7cae8cf3240af06659bcde09d543bc064e208a31d576bbf074bb7141 031aa8f87cde6c87de9bf1bdb9e575801a754d2a600be4d1fc89e36eae6db63bc6",
                  "hex": "41b818b5c19459d64c4f16ac8fbaff844a6c0d05de8cf563173737d56908de56033a1e367f3c7cae8cf3240af06659bcde09d543bc064e208a31d576bbf074bb714121031aa8f87cde6c87de9bf1bdb9e575801a754d2a600be4d1fc89e36eae6db63bc6"
                },
                "sequence": 0,
                "cashAddress": "bitcoincash:qz8wymtvnavrd8u5sexuxccvm6chlt3095hczr7px4",
                "n": 1,
                "value": 0.00008746
              }
            ],
            "vout": [
              {
                "value": 0.00001,
                "n": 0,
                "scriptPubKey": {
                  "asm": "OP_DUP OP_HASH160 8ee26d6c9f58369f94864dc3630cdeb17fae2f2d OP_EQUALVERIFY OP_CHECKSIG",
                  "hex": "76a9148ee26d6c9f58369f94864dc3630cdeb17fae2f2d88ac",
                  "reqSigs": 1,
                  "type": "pubkeyhash",
                  "addresses": [
                    "bitcoincash:qz8wymtvnavrd8u5sexuxccvm6chlt3095hczr7px4"
                  ],
                  "cashAddrs": [
                    "bitcoincash:qz8wymtvnavrd8u5sexuxccvm6chlt3095hczr7px4"
                  ]
                },
                "tokenData": {
                  "category": "8473d94f604de351cdee3030f6c354d36b257861ad8e95bbc0a06fbab2a2f9cf",
                  "amount": "140000000000"
                },
                "spentTxId": None,
                "spentIndex": None,
                "spentHeight": None
              },
              {
                "value": 0,
                "n": 1,
                "scriptPubKey": {
                  "asm": "OP_RETURN 1380795202 6b2000be5ce5527cd653c49cdba486e2fd0ec4214da2f71d7e56ad027b2139f4 676973742e67697468756275736572636f6e74656e742e636f6d2f6d722d7a776574732f38346230303537383038616632306466333932383135666232376434613636312f726177",
                  "hex": "6a0442434d52206b2000be5ce5527cd653c49cdba486e2fd0ec4214da2f71d7e56ad027b2139f448676973742e67697468756275736572636f6e74656e742e636f6d2f6d722d7a776574732f38346230303537383038616632306466333932383135666232376434613636312f726177",
                  "type": "nulldata"
                },
                "spentTxId": None,
                "spentIndex": None,
                "spentHeight": None
              },
              {
                "value": 0.00017221,
                "n": 2,
                "scriptPubKey": {
                  "asm": "OP_DUP OP_HASH160 8ee26d6c9f58369f94864dc3630cdeb17fae2f2d OP_EQUALVERIFY OP_CHECKSIG",
                  "hex": "76a9148ee26d6c9f58369f94864dc3630cdeb17fae2f2d88ac",
                  "reqSigs": 1,
                  "type": "pubkeyhash",
                  "addresses": [
                    "bitcoincash:qz8wymtvnavrd8u5sexuxccvm6chlt3095hczr7px4"
                  ],
                  "cashAddrs": [
                    "bitcoincash:qz8wymtvnavrd8u5sexuxccvm6chlt3095hczr7px4"
                  ]
                },
                "tokenData":{
                    "category": "8473d94f604de351cdee3030f6c354d36b257861ad8e95bbc0a06fbab2a2f9cf",
                    "amount": 0,
                    "nft": {
                        "capability": "minting",
                        "commitment": ""
                    }
                },
                "spentTxId": None,
                "spentIndex": None,
                "spentHeight": None
              }
            ],
            "blockhash": "0000000000000000007c302f8790f32efb996a9d162408ce930e0e70ee3cbe8d",
            "confirmations": 2172,
            "time": 1684161846,
            "blocktime": 1684161846,
            "valueIn": 0.00018746,
            "valueOut": 0.00018221,
            "fees": 0.00000525,
            "blockheight": 792781
        }
        self.monkeypatch.setattr(_bapi,
                                 "session",
                                 DummySession(return_json))
        transaction = self.api.get_transaction(BITCOIN_CASHADDRESS_CATKN)
        tx = Transaction(
            "446f83e975d2870de740917df1b5221aa4bc52c6e2540188f5897c4ce775b7f4",
            792781,
            18746,
            18221,
            525
        )
        tx.inputs = [
            TxPart(
                "bitcoincash:qz8wymtvnavrd8u5sexuxccvm6chlt3095hczr7px4",
                10000,
                data_hex="4177033dfa31b3ab4ad8a147d0b7bd10da60e7fe1df51bf1767f5ba7273767d7ffad55feec5c201ea89c6c07a1c8368d8a378aae2f48ddd2076324769b2c23a1ac4121031aa8f87cde6c87de9bf1bdb9e575801a754d2a600be4d1fc89e36eae6db63bc6"
            ),
            TxPart(
                "bitcoincash:qz8wymtvnavrd8u5sexuxccvm6chlt3095hczr7px4",
                8746,
                data_hex="41b818b5c19459d64c4f16ac8fbaff844a6c0d05de8cf563173737d56908de56033a1e367f3c7cae8cf3240af06659bcde09d543bc064e208a31d576bbf074bb714121031aa8f87cde6c87de9bf1bdb9e575801a754d2a600be4d1fc89e36eae6db63bc6"
            )
        ]
        tx.outputs = [
            TxPart(
                "bitcoincash:qz8wymtvnavrd8u5sexuxccvm6chlt3095hczr7px4",
                1000,
                catagory_id="8473d94f604de351cdee3030f6c354d36b257861ad8e95bbc0a06fbab2a2f9cf",
                token_amount=140000000000,
                data_hex="76a9148ee26d6c9f58369f94864dc3630cdeb17fae2f2d88ac"
            ),
            TxPart(
                None,
                0,
                data_hex="6a0442434d52206b2000be5ce5527cd653c49cdba486e2fd0ec4214da2f71d7e56ad027b2139f448676973742e67697468756275736572636f6e74656e742e636f6d2f6d722d7a776574732f38346230303537383038616632306466333932383135666232376434613636312f726177"
            ),
            TxPart(
                "bitcoincash:qz8wymtvnavrd8u5sexuxccvm6chlt3095hczr7px4",
                17221,
                catagory_id="8473d94f604de351cdee3030f6c354d36b257861ad8e95bbc0a06fbab2a2f9cf",
                nft_capability="minting",
                data_hex="76a9148ee26d6c9f58369f94864dc3630cdeb17fae2f2d88ac"
            )
        ]

        print(transaction.to_dict())
        print(tx.to_dict())
        assert transaction == tx

        # unconfirmed tx
        return_json = {
            "in_mempool": True,
            "in_orphanpool": False,
            "txid": "2dc926aac9ffb12ffa7dec784440d76e75c545d9ab4e46ea40e6b4ae73ed448f",
            "size": 223,
            "version": 1,
            "locktime": 0,
            "vin": [
              {
                "txid": "87dfe5b5af5526a7652ee23ca9ded6862f9a490de219bb7c85f5010c3b8ebc4a",
                "vout": 0,
                "scriptSig": {
                  "asm": "3044022024d7be8afd3100656889cddc309d2f5fc343a345fe7d7a22191163f463c5aac502200bbcebf4dc1361a2931f585c33a9fdf9816cbc919341b863609551030bcdb97d41 046bad1c4c33157c12dd812e734917f05a65b502658eeb4f164decc087c54f9fca4005df3499ad93f698294ab13259d7da578461930a9cb7312d526ab2d8f82012",
                  "hex": "473044022024d7be8afd3100656889cddc309d2f5fc343a345fe7d7a22191163f463c5aac502200bbcebf4dc1361a2931f585c33a9fdf9816cbc919341b863609551030bcdb97d4141046bad1c4c33157c12dd812e734917f05a65b502658eeb4f164decc087c54f9fca4005df3499ad93f698294ab13259d7da578461930a9cb7312d526ab2d8f82012"
                },
                "sequence": 4294967295,
                "cashAddress": "bitcoincash:qrelay2cnfsu84lvn6609rhrudh26rjt4y6ddw55lf",
                "n": 0,
                "value": 0.009
              }
            ],
            "vout": [
              {
                "value": 0.00899745,
                "n": 0,
                "scriptPubKey": {
                  "asm": "OP_DUP OP_HASH160 a522e4f6ca57aef5bf893d29029c3e9fc54a67f0 OP_EQUALVERIFY OP_CHECKSIG",
                  "hex": "76a914a522e4f6ca57aef5bf893d29029c3e9fc54a67f088ac",
                  "reqSigs": 1,
                  "type": "pubkeyhash",
                  "addresses": [
                    "bitcoincash:qzjj9e8keft6aadl3y7jjq5u860u2jn87qxwpv9nzl"
                  ],
                  "cashAddrs": [
                    "bitcoincash:qzjj9e8keft6aadl3y7jjq5u860u2jn87qxwpv9nzl"
                  ]
                },
                "spentTxId": None,
                "spentIndex": None,
                "spentHeight": None
              }
            ],
            "confirmations": 0,
            "time": 1684050728,
            "valueIn": 0.009,
            "valueOut": 0.00899745,
            "fees": 0.00000255,
          }
        self.monkeypatch.setattr(_bapi,
                                 "session",
                                 DummySession(return_json))
        transaction = self.api.get_transaction(BITCOIN_CASHADDRESS_CATKN)
        tx = Transaction(
            "2dc926aac9ffb12ffa7dec784440d76e75c545d9ab4e46ea40e6b4ae73ed448f",
            None,
            900000,
            899745,
            255
        )
        tx.inputs = [
            TxPart(
                "bitcoincash:qrelay2cnfsu84lvn6609rhrudh26rjt4y6ddw55lf",
                900000,
                data_hex="473044022024d7be8afd3100656889cddc309d2f5fc343a345fe7d7a22191163f463c5aac502200bbcebf4dc1361a2931f585c33a9fdf9816cbc919341b863609551030bcdb97d4141046bad1c4c33157c12dd812e734917f05a65b502658eeb4f164decc087c54f9fca4005df3499ad93f698294ab13259d7da578461930a9cb7312d526ab2d8f82012"
            )
        ]
        tx.outputs = [
            TxPart(
                "bitcoincash:qzjj9e8keft6aadl3y7jjq5u860u2jn87qxwpv9nzl",
                899745,
                data_hex="76a914a522e4f6ca57aef5bf893d29029c3e9fc54a67f088ac"
            )
        ]

        assert transaction == tx

    def test_get_tx_amount(self):
        return_json = {
            "vout": [
                {
                    "value": 0.00001
                }
            ]
        }
        self.monkeypatch.setattr(_bapi,
                                 "session",
                                 DummySession(return_json))
        amount = self.api.get_tx_amount(
            "446f83e975d2870de740917df1b5221aa4bc52c6e2540188f5897c4ce775b7f4",
            0
        )
        assert amount == 1000

    def test_get_unspent(self):
        return_json = {
            "utxos": [
              {
                "height": 792782,
                "txid": "8aa279c9c46a812273c12fe78efff995ab6493cffb130ef54da73d4268a1bc9f",
                "vout": 0,
                "satoshis": 1000,
                "amount": 0.00001,
                "confirmations": 1265,
                "tokenData": {
                    "category": "b3d668379a421820fe89cf1bda4bfd7295202a516a0fa5ca0c8011e4c2fc256d",
                    "amount": 0,
                    "nft": {
                        "capability": "none",
                        "commitment": "0a"
                    }
                }
              },
              {
                "height": 792782,
                "txid": "9aa279c9c46a812273c12fe78efff995ab6493cffb130ef54da73d4268a1bc9f",
                "vout": 0,
                "satoshis": 1000,
                "amount": 0.00001,
                "confirmations": 1265,
                "tokenData": {
                    "category": "c3d668379a421820fe89cf1bda4bfd7295202a516a0fa5ca0c8011e4c2fc256d",
                    "amount": 0,
                    "nft": {
                        "capability": "none",
                        "commitment": ""
                    }
                }
              },
              {
                "height": 792785,
                "txid": "1c04b42cdd4fe595040a478315c31d9276abcb00cf8e7d2f9e52f81bade279a3",
                "vout": 0,
                "satoshis": 1000,
                "amount": 0.00001,
                "confirmations": 1262,
                "tokenData": {
                    "category": "55255e66ab1280fae24896c084c360d5027c1b4ef5b1a5588c4b7af246fdcf7a",
                    "amount": 1000,
                }
              },
              {
                "height": 794043,
                "txid": "5b2f18d2c214560c4fa21dd2ff18bfa2126e6693dde20d5c516fbaf56c634fdd",
                "vout": 1,
                "satoshis": 2512699,
                "amount": 0.02512699,
                "confirmations": 4,
              },
              {
                "height": 0,
                "txid": "6b2f18d2c214560c4fa21dd2ff18bfa2126e6693dde20d5c516fbaf56c634fdd",
                "vout": 1,
                "satoshis": 2512699,
                "amount": 0.02512699,
                "confirmations": 0,
              },
            ],
            "legacyAddress": "1E2WChGBeJXtLtrwAfb4KwYF61C99BJ47K",
            "cashAddress": "bitcoincash:qz8wymtvnavrd8u5sexuxccvm6chlt3095hczr7px4",
            "slpAddress": "simpleledger:qz8wymtvnavrd8u5sexuxccvm6chlt3095mrfctpct",
            "scriptPubKey": "76a9148ee26d6c9f58369f94864dc3630cdeb17fae2f2d88ac",
            "asm": "OP_DUP OP_HASH160 8ee26d6c9f58369f94864dc3630cdeb17fae2f2d OP_EQUALVERIFY OP_CHECKSIG"
        }
        self.monkeypatch.setattr(_bapi,
                                 "session",
                                 DummySession(return_json))
        unspents = self.api.get_unspent(BITCOIN_CASHADDRESS_CATKN)
        script = "76a9148ee26d6c9f58369f94864dc3630cdeb17fae2f2d88ac"
        assert unspents == [
            Unspent(
                1000,
                1265,
                script,
                "8aa279c9c46a812273c12fe78efff995ab6493cffb130ef54da73d4268a1bc9f",
                0,
                # "b3d668379a421820fe89cf1bda4bfd7295202a516a0fa5ca0c8011e4c2fc256d",
                # "none",
                # b"\n",
                # None
            ),
            Unspent(
                1000,
                1265,
                script,
                "9aa279c9c46a812273c12fe78efff995ab6493cffb130ef54da73d4268a1bc9f",
                0,
                # "c3d668379a421820fe89cf1bda4bfd7295202a516a0fa5ca0c8011e4c2fc256d",
                # "none",
                # None,
                # None
            ),
            Unspent(
                1000,
                1262,
                script,
                "1c04b42cdd4fe595040a478315c31d9276abcb00cf8e7d2f9e52f81bade279a3",
                0,
                # "55255e66ab1280fae24896c084c360d5027c1b4ef5b1a5588c4b7af246fdcf7a",
                # None,
                # None,
                # 1000
            ),
            Unspent(
                2512699,
                4,
                script,
                "5b2f18d2c214560c4fa21dd2ff18bfa2126e6693dde20d5c516fbaf56c634fdd",
                1,
                None,
                None,
                None,
                None
            ),
            Unspent(
                2512699,
                0,
                script,
                "6b2f18d2c214560c4fa21dd2ff18bfa2126e6693dde20d5c516fbaf56c634fdd",
                1,
                None,
                None,
                None,
                None
            ),
        ]

        # zero return
        return_json = {
            "utxos": [],
            "legacyAddress": "1AaY9371BsWXnLDz1jD4PYeuehA2PMidZY",
            "cashAddress": "bitcoincash:qp53pksewwhtufkkcs76ycl5nq9t0kr6kq4uwkyu54",
            "slpAddress": "simpleledger:qp53pksewwhtufkkcs76ycl5nq9t0kr6kqe89d3u2t",
            "scriptPubKey": "",
            "asm": ""
        }
        self.monkeypatch.setattr(_bapi,
                                 "session",
                                 DummySession(return_json))
        unspents = self.api.get_unspent(BITCOIN_CASHADDRESS_CATKN)
        assert unspents == []

    def test_get_raw_transaction(self):
        return_json = {
          "dummy": "dummy"
        }
        self.monkeypatch.setattr(_bapi,
                                 "session",
                                 DummySession(return_json))
        tx = self.api.get_raw_transaction(
            "446f83e975d2870de740917df1b5221aa4bc52c6e2540188f5897c4ce775b7f4",
        )
        assert tx == {"dummy": "dummy"}
