import pytest
import bitcash.slp_create as s
from bitcash.exceptions import SlpSerializingError


genesis_type_1 = '6a04534c500001010747454e45534953036161610c746f6b656e203120746573744c004c0001004c000800000000000003e8'
genesis_type_65 = '6a04534c500001410747454e45534953036262620d746f6b656e20363520746573744c004c0001014c000800000000000003e8'
genesis_type_129 = '6a04534c500001810747454e45534953036363630e746f6b656e2031323920746573740c7777772e746573742e636f6d4c00010101020800000000000003e8'
genesis_no_ticker = '6a04534c500001010747454e455349534c000c746f6b656e203120746573744c004c0001004c000800000000000003e8'
genesis_no_token_name = '6a04534c500001010747454e45534953036162634c004c004c00010001020800000000000003e8'

mint_token_id = 'ae885f8e1bd2a09c5f8dcf19cb9a837d8c48b370190f31841b8a4817ebdbb9d7'
mint_type_1 = '6a04534c50000101044d494e5420ae885f8e1bd2a09c5f8dcf19cb9a837d8c48b370190f31841b8a4817ebdbb9d74c000800000000000003e8'
mint_type_129 = '6a04534c50000181044d494e5420ae885f8e1bd2a09c5f8dcf19cb9a837d8c48b370190f31841b8a4817ebdbb9d701020800000000000003e8'

send_type_1 = '6a04534c500001010453454e4420ae885f8e1bd2a09c5f8dcf19cb9a837d8c48b370190f31841b8a4817ebdbb9d708000000000000000508000000000000000a080000000000000007'
send_type_129 = '6a04534c500001810453454e4420ae885f8e1bd2a09c5f8dcf19cb9a837d8c48b370190f31841b8a4817ebdbb9d7080000000000000032080000000000000001080000000000000047'

test_ui_string_chunks = [b'SLP\x00', b'\x01', b'SEND', b'\xae\x88_\x8e\x1b\xd2\xa0\x9c_\x8d\xcf\x19\xcb\x9a\x83}\x8cH\xb3p\x19\x0f1\x84\x1b\x8aH\x17\xeb\xdb\xb9\xd7', b'\x00\x00\x00\x00\x00\x00\x00\x05', b'\x00\x00\x00\x00\x00\x00\x00\n', b'\x00\x00\x00\x00\x00\x00\x00\x07']

def test_Genesis_Op_Return_token_1():

    result = s.buildGenesisOpReturn(
        ticker="aaa",
        token_name="token 1 test",
        token_document_url=None,
        token_document_hash_hex=None,
        decimals=0,
        baton_vout=None,
        initial_token_mint_quantity=1000,
        token_type=1)

    assert result == genesis_type_1

def test_Genesis_Op_Return_token_65():

    result = s.buildGenesisOpReturn(
        ticker="bbb",
        token_name="token 65 test",
        token_document_url=None,
        token_document_hash_hex=None,
        decimals=1,
        baton_vout=None,
        initial_token_mint_quantity=1000,
        token_type=65)

    assert result == genesis_type_65

def test_Genesis_Op_Return_token_129():

    result = s.buildGenesisOpReturn(
        ticker="ccc",
        token_name="token 129 test",
        token_document_url="www.test.com",
        token_document_hash_hex="",
        decimals=1,
        baton_vout=2,
        initial_token_mint_quantity=1000,
        token_type=129)

    assert result == genesis_type_129

def test_Genesis_Op_Return_token_129_2():

    result = s.buildGenesisOpReturn(
        ticker="ccc",
        token_name="token 129 test",
        token_document_url="www.test.com",
        token_document_hash_hex="",
        decimals=1,
        baton_vout=2,
        initial_token_mint_quantity=1000,
        token_type="SLP129")

    assert result == genesis_type_129

def test_Genesis_Op_Return_invalid_hash():
    with pytest.raises(SlpSerializingError):
        s.buildGenesisOpReturn(
        ticker="ddd",
        token_name="token invalid hash test",
        token_document_url="www.test.com",
        token_document_hash_hex="1234",
        decimals=1,
        baton_vout=2,
        initial_token_mint_quantity=1000,
        token_type=129)
    
def test_Genesis_Op_Return_invalid_token_type():
    with pytest.raises(Exception) as exec:
        buildGenesisOpReturn(
            ticker="eee",
            token_name="token 111 test",
            token_document_url="",
            token_document_hash_hex="",
            decimals=1,
            baton_vout=2,
            initial_token_mint_quantity=1000,
            token_type=999)
        assert exec.value.message == "Unsupported token type"

def test_genesis_op_return_no_ticker():
    result = s.buildGenesisOpReturn(
        ticker=None,
        token_name="token 1 test",
        token_document_url=None,
        token_document_hash_hex=None,
        decimals=0,
        baton_vout=None,
        initial_token_mint_quantity=1000,
        token_type=1)

    assert result == genesis_no_ticker

def test_genesis_op_return_no_token_name():
    result = s.buildGenesisOpReturn(
        ticker="abc",
        token_name=None,
        token_document_url=None,
        token_document_hash_hex=None,
        decimals=0,
        baton_vout=2,
        initial_token_mint_quantity=1000,
        token_type=1)

    assert result == genesis_no_token_name

def test_genesis_op_return_decimals():
    with pytest.raises(SlpSerializingError):
        result = s.buildGenesisOpReturn(
            ticker="abc",
            token_name="decimals",
            token_document_url=None,
            token_document_hash_hex=None,
            decimals=11,
            baton_vout=None,
            initial_token_mint_quantity=1000,
            token_type=1)

def test_genesis_op_return_baton_vout():
    with pytest.raises(SlpSerializingError):
        result = s.buildGenesisOpReturn(
            ticker="abc",
            token_name="decimals",
            token_document_url=None,
            token_document_hash_hex=None,
            decimals=11,
            baton_vout=1,
            initial_token_mint_quantity=1000,
            token_type=1)

    
def test_mint_op_return_type_1():
    result = s.buildMintOpReturn(
        token_id_hex = mint_token_id, 
        baton_vout = None, 
        token_mint_quantity = 1000, 
        token_type = 1
        )

    assert result == mint_type_1

def test_mint_op_return_type_129():
    result = s.buildMintOpReturn(
        token_id_hex = mint_token_id, 
        baton_vout = 2, 
        token_mint_quantity = 1000, 
        token_type = 129
        )

    assert result == mint_type_129

def test_mint_op_return_invalid_token_type():
    with pytest.raises(Exception) as exec:
        result = s.buildMintOpReturn(
            token_id_hex = mint_token_id, 
            baton_vout = None, 
            token_mint_quantity = 1000, 
            token_type = 43
            )

        assert exec.value.message == "Unsupported token type"

def test_mint_op_return_invalid_tokenid_length():
    with pytest.raises(SlpSerializingError):
        result = s.buildMintOpReturn(
            token_id_hex = 'F1', 
            baton_vout = None, 
            token_mint_quantity = 1000, 
            token_type = 1
            )

def test_mint_op_return_invalid_baton_vout():
    with pytest.raises(SlpSerializingError):
        result = s.buildMintOpReturn(
            token_id_hex = mint_token_id, 
            baton_vout = 1, 
            token_mint_quantity = 1000, 
            token_type = 1
            )

def test_send_type_1():
    result = s.buildSendOpReturn(
        token_id_hex = mint_token_id, 
        output_qty_array = [5, 10, 7], 
        token_type = 1
    )

    assert result == send_type_1

def test_send_type_129():
    result = s.buildSendOpReturn(
        token_id_hex = mint_token_id, 
        output_qty_array = [50, 1, 71], 
        token_type = 129
    )

    assert result == send_type_129

def test_send_0_outputs():
    with pytest.raises(SlpSerializingError):
        result = s.buildSendOpReturn(
        token_id_hex = mint_token_id, 
        output_qty_array = [], 
        token_type = 129
        )

def test_send_20_outputs():
    with pytest.raises(SlpSerializingError):
        result = s.buildSendOpReturn(
        token_id_hex = mint_token_id, 
        output_qty_array = [
            50, 14, 71, 2, 511,
            51, 13, 72, 20, 52,
            52, 12, 73, 21, 53,
            53, 11, 74, 22, 51
        ], 
        token_type = 129
        )

def test_send_invalid_tokenid_length():
    with pytest.raises(SlpSerializingError):
        result = s.buildSendOpReturn(
        token_id_hex = "F1", 
        output_qty_array = [5], 
        token_type = 129
        )


