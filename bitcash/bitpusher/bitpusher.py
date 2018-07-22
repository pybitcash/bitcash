from bitcash import utils
from bitcash.network.services import NetworkAPI
from bitcash.bitpusher import memo
from bitcash.bitpusher import blockpress


def create_pushdata(lst_of_pushdata):
    '''
    Creates encoded OP_RETURN pushdata as bytes
    Returns binary encoded OP_RETURN pushdata (automatically adds intervening OP_CODES specifying number of bytes in each pushdata element)
    0x6a (i.e. OP_RETURN) is added in other, auxillary functions; only pushdata is returned.
    Max 220 bytes of pushdata

    Parameters
    ----------
    lst_of_pushdata : array of tuples
        1-D array of 2-D tuples (pushdata, encoding)

    Returns
    -------
    pushdata : bytes

    Examples
    --------

    lst_of_pushdata =  [('6d01', 'hex'),
                        ('bitPUSHER', 'utf-8')]

    as per memo.cash protocol @ https://memo.cash/protocol this results in a "Set name" action to "bitPUSHER"

    raw OP_RETURN will be:

        0e 6a 02 6d01 09 626974505553484552

            0e                  - 14 bytes to follow (in hex)
            6a                  - OP_RETURN
            02                  - 2 bytes of pushdata to follow
            6d01                - "communication channel" for memo.cash - "set name" action
            09                  - 9 bytes to follow
            626974505553484552  - "bitPUSHER" utf-8 encoded bytes --> hex representation

    Currently (this module) only allows up to 220 bytes maximum - as multiple OP_RETURNS in one transaction is considered non-standard.

    RECOMMENDED WORKFLOW
    # Import private key with bitcash
        my_key = bitcash.PrivateKey('WIF Compressed (base58) here')
        my_key.get_unspents() #necessary step --> updates my_key.unspents object variable

    # Create lst_of_pushdata
        lst_of_pushdata =  [('6d01', 'hex'),
                            ('bitPUSHER', 'utf-8')]

    # Output OP_RETURN pushdata as bytes and store in variable
        pushdata = bitcash.bitpusher.create_pushdata(lst_of_pushdata)

    # Create rawtx ready for broadcast (fee = 1 sat/byte; sending 0.0001 BCH back to own address)
        rawtx = my_key.create_transaction([(my_key.address, 0.0001, 'bch')], fee=1, message=pushdata, custom_PUSHDATA=True)

    # Broadcast rawtx
        bitcash.network.services.NetworkAPI.broadcast_tx(rawtx)
        --> look at block explorer or wallet to see new transaction!

    ALTERNATIVE DEFAULT SETUP FOR AUTOMATING ABOVE STEPS --> See bitpusher()
    '''
    pushdata = b''

    for i in range(len(lst_of_pushdata)):

        encoding = lst_of_pushdata[i][1]
        if encoding == 'utf-8':
            pushdata += len(lst_of_pushdata[i][0]).to_bytes(
                1, byteorder='little') + lst_of_pushdata[i][0].encode('utf-8')

        elif encoding == 'hex' and len(lst_of_pushdata[i][0]) % 2 != 0:
            raise ValueError(
                "hex encoded pushdata must have length = a multiple of two")

        elif encoding == 'hex' and len(lst_of_pushdata[i][0]) % 2 == 0:
            pushdata += (len(lst_of_pushdata[i][0]) // 2).to_bytes(
                1, byteorder='little') + utils.hex_to_bytes(lst_of_pushdata[i][0])

    # check for size
    if len(pushdata) > 220:
        raise ValueError(
            "Total bytes in OP_RETURN cannot exceed 220 bytes at present - apologies")

    return pushdata


def rawtx(PrivateKey, lst_of_pushdata, fee=1):
    '''creates a rawtx with OP_RETURN metadata

    Parameters
    ----------
    PrivateKey : bitcash.PrivateKey object

    pushdata : lst_of_pushdata in a 1-D array of 2-D tuples (pushdata, encoding)

    fee : sat/byte (defaults to 1 satoshi per byte)

    Returns
    -------
    rawtx ready to broadcast
    '''

    PrivateKey.get_unspents()
    pushdata = create_pushdata(lst_of_pushdata)
    rawtx = PrivateKey.create_transaction(
        [(PrivateKey.address, 0.0001, 'bch')], fee=1, message=pushdata, custom_pushdata=True)
    return rawtx


def bitpush(PrivateKey, lst_of_pushdata, fee=1):
    '''
    All-in-one function for generating a rawtx with desired OP_RETURN metadata and broadcasting it to the blockchain

    Parameters
    ----------
    PrivateKey : bitcash.PrivateKey object

    pushdata : lst_of_pushdata in a 1-D array of 2-D tuples (pushdata, encoding)

    fee : sat/byte (defaults to 1 satoshi per byte)

    Returns
    -------
    broadcasts rawtx

    Examples
    --------
    lst_of_pushdata = [('6d01','hex'), ('my_new_memocash_name', 'utf-8')]
    bitpush(my_key, lst_of_pushdata)
    '''

    PrivateKey.get_unspents()
    pushdata = create_pushdata(lst_of_pushdata)
    rawtx = PrivateKey.create_transaction(
        [(PrivateKey.address, 0.0001, 'bch')], fee=1, message=pushdata, custom_pushdata=True)

    return NetworkAPI.broadcast_tx(rawtx)
