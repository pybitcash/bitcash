from _pytest.monkeypatch import MonkeyPatch
from bitcash.network.APIs import ChaingraphAPI as _capi

from bitcash.network.transaction import Transaction, TxPart
from bitcash.network.APIs.ChaingraphAPI import ChaingraphAPI
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

    def post(self, url, json, *args, **kwargs):
        assert "query" in json
        if len(json.keys()) > 1:
            assert "variables" in json
        return DummyRequest(self.return_json)


class TestChaingraphAPI:

    def setup_method(self):
        self.monkeypatch = MonkeyPatch()
        self.api = ChaingraphAPI("https://dummy.com/v1/graphql")

    def test_get_balance(self):
        return_json = {
            "data": {
              "search_output_prefix": [
                {
                  "value_satoshis": "1000"
                },
                {
                  "value_satoshis": "1000"
                },
                {
                  "value_satoshis": "1000"
                }
              ]
            }
        }
        self.monkeypatch.setattr(_capi,
                                 "session",
                                 DummySession(return_json))
        balance = self.api.get_balance(BITCOIN_CASHADDRESS_CATKN)
        assert balance == 3000

    def test_get_transactions(self):
        return_json = {
            "data": {
              "block": [
                {
                  "height": "793970"
                }
              ],
              "search_output_prefix": [
                {
                  "transaction_hash": "\\x2c39cebc1ea104243f87d78a522ec1d499d98ffc2f145c08d474889573300dd7",
                  "transaction": {
                    "block_inclusions": [
                      {
                        "block": {
                          "height": "788696"
                        }
                      }
                    ]
                  },
                  "spent_by": [
                    {
                      "transaction": {
                        "hash": "\\x616c8f5c64847645a9052d9aec822abf6fb526ec7b01cc918e392cdf24df8f89",
                        "block_inclusions": [
                          {
                            "block": {
                              "height": "789986"
                            }
                          }
                        ]
                      }
                    }
                  ]
                },
                {
                  "transaction_hash": "\\x616c8f5c64847645a9052d9aec822abf6fb526ec7b01cc918e392cdf24df8f89",
                  "transaction": {
                    "block_inclusions": [
                      {
                        "block": {
                          "height": "789986"
                        }
                      }
                    ]
                  },
                  "spent_by": [
                    {
                      "transaction": {
                        "hash": "\\x2cd47128e4af9ab1c3df0bce0305c2bbf5ad7fdecbba3c0b73766294bc88eaf8",
                        "block_inclusions": [
                          {
                            "block": {
                              "height": "790193"
                            }
                          }
                        ]
                      }
                    }
                  ]
                },
                {
                  "transaction_hash": "\\xd07ee04f7e5792ae848b778c8b802283aff77413865582ebba3f3c7c016e82a9",
                  "transaction": {
                    "block_inclusions": [
                      {
                        "block": {
                          "height": "793668"
                        }
                      }
                    ]
                  },
                  "spent_by": [
                    {
                      "transaction": {
                        "hash": "\\xae3cdb099d52da7dd4b1e16762b5788fd151e69836a45aba53adcecb02fccb4a",
                        "block_inclusions": []
                      }
                    }
                  ]
                },
                {
                  "transaction_hash": "\\xae3cdb099d52da7dd4b1e16762b5788fd151e69836a45aba53adcecb02fccb4a",
                  "transaction": {
                    "block_inclusions": []
                  },
                  "spent_by": []
                }
              ]
            }
        }
        self.monkeypatch.setattr(_capi,
                                 "session",
                                 DummySession(return_json))
        transactions = self.api.get_transactions(BITCOIN_CASHADDRESS_CATKN)

        assert transactions == ["ae3cdb099d52da7dd4b1e16762b5788fd151e69836a45aba53adcecb02fccb4a",
                                "d07ee04f7e5792ae848b778c8b802283aff77413865582ebba3f3c7c016e82a9",
                                "2cd47128e4af9ab1c3df0bce0305c2bbf5ad7fdecbba3c0b73766294bc88eaf8",
                                "616c8f5c64847645a9052d9aec822abf6fb526ec7b01cc918e392cdf24df8f89",
                                "2c39cebc1ea104243f87d78a522ec1d499d98ffc2f145c08d474889573300dd7"]

    def test_get_transaction(self):
        return_json = {
            "data": {
              "transaction": [
                {
                  "hash": "\\x446f83e975d2870de740917df1b5221aa4bc52c6e2540188f5897c4ce775b7f4",
                  "fee_satoshis": "525",
                  "input_value_satoshis": "18746",
                  "output_value_satoshis": "18221",
                  "block_inclusions": [
                    {
                      "block": {
                        "height": "792781"
                      }
                    }
                  ],
                  "inputs": [
                    {
                      "value_satoshis": "10000",
                      "unlocking_bytecode": "\\x4177033dfa31b3ab4ad8a147d0b7bd10da60e7fe1df51bf1767f5ba7273767d7ffad55feec5c201ea89c6c07a1c8368d8a378aae2f48ddd2076324769b2c23a1ac4121031aa8f87cde6c87de9bf1bdb9e575801a754d2a600be4d1fc89e36eae6db63bc6",
                      "outpoint": {
                        "locking_bytecode": "\\x76a9148ee26d6c9f58369f94864dc3630cdeb17fae2f2d88ac",
                        "token_category": None,
                        "nonfungible_token_capability": None,
                        "nonfungible_token_commitment": None,
                        "fungible_token_amount": None
                      }
                    },
                    {
                      "value_satoshis": "8746",
                      "unlocking_bytecode": "\\x41b818b5c19459d64c4f16ac8fbaff844a6c0d05de8cf563173737d56908de56033a1e367f3c7cae8cf3240af06659bcde09d543bc064e208a31d576bbf074bb714121031aa8f87cde6c87de9bf1bdb9e575801a754d2a600be4d1fc89e36eae6db63bc6",
                      "outpoint": {
                        "locking_bytecode": "\\x76a9148ee26d6c9f58369f94864dc3630cdeb17fae2f2d88ac",
                        "token_category": None,
                        "nonfungible_token_capability": None,
                        "nonfungible_token_commitment": None,
                        "fungible_token_amount": None
                      }
                    }
                  ],
                  "outputs": [
                    {
                      "value_satoshis": "1000",
                      "locking_bytecode": "\\x76a9148ee26d6c9f58369f94864dc3630cdeb17fae2f2d88ac",
                      "token_category": "\\x8473d94f604de351cdee3030f6c354d36b257861ad8e95bbc0a06fbab2a2f9cf",
                      "nonfungible_token_capability": None,
                      "nonfungible_token_commitment": None,
                      "fungible_token_amount": "140000000000"
                    },
                    {
                      "value_satoshis": "0",
                      "locking_bytecode": "\\x6a0442434d52206b2000be5ce5527cd653c49cdba486e2fd0ec4214da2f71d7e56ad027b2139f448676973742e67697468756275736572636f6e74656e742e636f6d2f6d722d7a776574732f38346230303537383038616632306466333932383135666232376434613636312f726177",
                      "token_category": None,
                      "nonfungible_token_capability": None,
                      "nonfungible_token_commitment": None,
                      "fungible_token_amount": None
                    },
                    {
                      "value_satoshis": "17221",
                      "locking_bytecode": "\\x76a9148ee26d6c9f58369f94864dc3630cdeb17fae2f2d88ac",
                      "token_category": "\\x8473d94f604de351cdee3030f6c354d36b257861ad8e95bbc0a06fbab2a2f9cf",
                      "nonfungible_token_capability": "minting",
                      "nonfungible_token_commitment": "\\x",
                      "fungible_token_amount": "0"
                    }
                  ]
                }
              ]
            }
          }

        self.monkeypatch.setattr(_capi,
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

        assert transaction == tx

        # unconfirmed tx
        return_json = {
            "data": {
              "transaction": [
                {
                  "hash": "\\x2dc926aac9ffb12ffa7dec784440d76e75c545d9ab4e46ea40e6b4ae73ed448f",
                  "fee_satoshis": "255",
                  "input_value_satoshis": "900000",
                  "output_value_satoshis": "899745",
                  "block_inclusions": [],
                  "inputs": [
                    {
                      "value_satoshis": "900000",
                      "unlocking_bytecode": "\\x473044022024d7be8afd3100656889cddc309d2f5fc343a345fe7d7a22191163f463c5aac502200bbcebf4dc1361a2931f585c33a9fdf9816cbc919341b863609551030bcdb97d4141046bad1c4c33157c12dd812e734917f05a65b502658eeb4f164decc087c54f9fca4005df3499ad93f698294ab13259d7da578461930a9cb7312d526ab2d8f82012",
                      "outpoint": {
                        "locking_bytecode": "\\x76a914f3fe91589a61c3d7ec9eb4f28ee3e36ead0e4ba988ac",
                        "token_category": None,
                        "nonfungible_token_capability": None,
                        "nonfungible_token_commitment": None,
                        "fungible_token_amount": None
                      }
                    }
                  ],
                  "outputs": [
                    {
                      "value_satoshis": "899745",
                      "locking_bytecode": "\\x76a914a522e4f6ca57aef5bf893d29029c3e9fc54a67f088ac",
                      "token_category": None,
                      "nonfungible_token_capability": None,
                      "nonfungible_token_commitment": None,
                      "fungible_token_amount": None
                    }
                  ]
                }
              ]
            }
        }
        self.monkeypatch.setattr(_capi,
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
            "data": {
              "output": [
                {
                  "value_satoshis": "1000"
                }
              ]
            }
          }
        self.monkeypatch.setattr(_capi,
                                 "session",
                                 DummySession(return_json))
        amount = self.api.get_tx_amount(
            "446f83e975d2870de740917df1b5221aa4bc52c6e2540188f5897c4ce775b7f4",
            0
        )
        assert amount == 1000

    def test_get_unspent(self):
        return_json = {
            "data": {
              "block": [
                {
                  "height": "794046"
                }
              ],
              "search_output_prefix": [
                {
                  "transaction_hash": "\\x8aa279c9c46a812273c12fe78efff995ab6493cffb130ef54da73d4268a1bc9f",
                  "output_index": "0",
                  "value_satoshis": "1000",
                  "token_category": "\\xb3d668379a421820fe89cf1bda4bfd7295202a516a0fa5ca0c8011e4c2fc256d",
                  "fungible_token_amount": "0",
                  "nonfungible_token_capability": "none",
                  "nonfungible_token_commitment": "\\x0a",
                  "locking_bytecode": "\\x76a9148ee26d6c9f58369f94864dc3630cdeb17fae2f2d88ac",
                  "transaction": {
                    "block_inclusions": [
                      {
                        "block": {
                          "height": "792782"
                        }
                      }
                    ]
                  }
                },
                {
                  "transaction_hash": "\\x9aa279c9c46a812273c12fe78efff995ab6493cffb130ef54da73d4268a1bc9f",
                  "output_index": "0",
                  "value_satoshis": "1000",
                  "token_category": "\\xc3d668379a421820fe89cf1bda4bfd7295202a516a0fa5ca0c8011e4c2fc256d",
                  "fungible_token_amount": "0",
                  "nonfungible_token_capability": "none",
                  "nonfungible_token_commitment": "\\x",
                  "locking_bytecode": "\\x76a9148ee26d6c9f58369f94864dc3630cdeb17fae2f2d88ac",
                  "transaction": {
                    "block_inclusions": [
                      {
                        "block": {
                          "height": "792782"
                        }
                      }
                    ]
                  }
                },
                {
                  "transaction_hash": "\\x1c04b42cdd4fe595040a478315c31d9276abcb00cf8e7d2f9e52f81bade279a3",
                  "output_index": "0",
                  "value_satoshis": "1000",
                  "token_category": "\\x55255e66ab1280fae24896c084c360d5027c1b4ef5b1a5588c4b7af246fdcf7a",
                  "fungible_token_amount": "1000",
                  "nonfungible_token_capability": None,
                  "nonfungible_token_commitment": None,
                  "locking_bytecode": "\\x76a9148ee26d6c9f58369f94864dc3630cdeb17fae2f2d88ac",
                  "transaction": {
                    "block_inclusions": [
                      {
                        "block": {
                          "height": "792785"
                        }
                      }
                    ]
                  }
                },
                {
                  "transaction_hash": "\\x5b2f18d2c214560c4fa21dd2ff18bfa2126e6693dde20d5c516fbaf56c634fdd",
                  "output_index": "1",
                  "value_satoshis": "2512699",
                  "token_category": None,
                  "fungible_token_amount": None,
                  "nonfungible_token_capability": None,
                  "nonfungible_token_commitment": None,
                  "locking_bytecode": "\\x76a9148ee26d6c9f58369f94864dc3630cdeb17fae2f2d88ac",
                  "transaction": {
                    "block_inclusions": [
                      {
                        "block": {
                          "height": "794043"
                        }
                      }
                    ]
                  }
                },
                {
                  "transaction_hash": "\\x6b2f18d2c214560c4fa21dd2ff18bfa2126e6693dde20d5c516fbaf56c634fdd",
                  "output_index": "1",
                  "value_satoshis": "2512699",
                  "token_category": None,
                  "fungible_token_amount": None,
                  "nonfungible_token_capability": None,
                  "nonfungible_token_commitment": None,
                  "locking_bytecode": "\\x76a9148ee26d6c9f58369f94864dc3630cdeb17fae2f2d88ac",
                  "transaction": {
                    "block_inclusions": []
                  }
                }
              ]
            }
        }
        self.monkeypatch.setattr(_capi,
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
                "b3d668379a421820fe89cf1bda4bfd7295202a516a0fa5ca0c8011e4c2fc256d",
                "none",
                b"0a",
                None
            ),
            Unspent(
                1000,
                1265,
                script,
                "9aa279c9c46a812273c12fe78efff995ab6493cffb130ef54da73d4268a1bc9f",
                0,
                "c3d668379a421820fe89cf1bda4bfd7295202a516a0fa5ca0c8011e4c2fc256d",
                "none",
                None,
                None
            ),
            Unspent(
                1000,
                1262,
                script,
                "1c04b42cdd4fe595040a478315c31d9276abcb00cf8e7d2f9e52f81bade279a3",
                0,
                "55255e66ab1280fae24896c084c360d5027c1b4ef5b1a5588c4b7af246fdcf7a",
                None,
                None,
                1000
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

    def test_get_raw_transaction(self):
        return_json = {
            "data": {
              "transaction": [
                {
                  "encoded_hex": "0200000002cff9a2b2ba6fa0c0bb958ead6178256bd354c3f63030eecd51e34d604fd9738400000000644177033dfa31b3ab4ad8a147d0b7bd10da60e7fe1df51bf1767f5ba7273767d7ffad55feec5c201ea89c6c07a1c8368d8a378aae2f48ddd2076324769b2c23a1ac4121031aa8f87cde6c87de9bf1bdb9e575801a754d2a600be4d1fc89e36eae6db63bc600000000cf9a546cb9d6997c68c3c92a2daa658ef8e8778a30e92d7da0b963d0a213ef79010000006441b818b5c19459d64c4f16ac8fbaff844a6c0d05de8cf563173737d56908de56033a1e367f3c7cae8cf3240af06659bcde09d543bc064e208a31d576bbf074bb714121031aa8f87cde6c87de9bf1bdb9e575801a754d2a600be4d1fc89e36eae6db63bc60000000003e80300000000000044efcff9a2b2ba6fa0c0bb958ead6178256bd354c3f63030eecd51e34d604fd9738410ff0078a6982000000076a9148ee26d6c9f58369f94864dc3630cdeb17fae2f2d88ac0000000000000000706a0442434d52206b2000be5ce5527cd653c49cdba486e2fd0ec4214da2f71d7e56ad027b2139f448676973742e67697468756275736572636f6e74656e742e636f6d2f6d722d7a776574732f38346230303537383038616632306466333932383135666232376434613636312f72617745430000000000001976a9148ee26d6c9f58369f94864dc3630cdeb17fae2f2d88ac00000000"
                }
              ]
            }
        }
        self.monkeypatch.setattr(_capi,
                                 "session",
                                 DummySession(return_json))
        tx = self.api.get_raw_transaction(
            "446f83e975d2870de740917df1b5221aa4bc52c6e2540188f5897c4ce775b7f4",
        )
        assert tx == "0200000002cff9a2b2ba6fa0c0bb958ead6178256bd354c3f63030eecd51e34d604fd9738400000000644177033dfa31b3ab4ad8a147d0b7bd10da60e7fe1df51bf1767f5ba7273767d7ffad55feec5c201ea89c6c07a1c8368d8a378aae2f48ddd2076324769b2c23a1ac4121031aa8f87cde6c87de9bf1bdb9e575801a754d2a600be4d1fc89e36eae6db63bc600000000cf9a546cb9d6997c68c3c92a2daa658ef8e8778a30e92d7da0b963d0a213ef79010000006441b818b5c19459d64c4f16ac8fbaff844a6c0d05de8cf563173737d56908de56033a1e367f3c7cae8cf3240af06659bcde09d543bc064e208a31d576bbf074bb714121031aa8f87cde6c87de9bf1bdb9e575801a754d2a600be4d1fc89e36eae6db63bc60000000003e80300000000000044efcff9a2b2ba6fa0c0bb958ead6178256bd354c3f63030eecd51e34d604fd9738410ff0078a6982000000076a9148ee26d6c9f58369f94864dc3630cdeb17fae2f2d88ac0000000000000000706a0442434d52206b2000be5ce5527cd653c49cdba486e2fd0ec4214da2f71d7e56ad027b2139f448676973742e67697468756275736572636f6e74656e742e636f6d2f6d722d7a776574732f38346230303537383038616632306466333932383135666232376434613636312f72617745430000000000001976a9148ee26d6c9f58369f94864dc3630cdeb17fae2f2d88ac00000000"
