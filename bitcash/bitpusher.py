import bitcash


def create_pushdata(lst_of_pushdata):
    '''
    Takes in a list of (pushdata, encoding type) tuples
    Returns binary encoded OP_RETURN pushdata (automatically adds intervening OP_CODES specifying number of bytes in each pushdata element)
    0x6a (i.e. OP_RETURN) is added in other, auxillary functions; only pushdata is returned.
    Max 220 bytes of pushdata

    Example:

        lst_of_pushdata =  [('6d01', 'hex'),
                            ('bitPUSHER', 'utf-8')]

        as per memo.cash protocol @ https://memo.cash/protocol
        This will result in a "Set name" action to "bitPUSHER"

        raw OP_RETURN will be:

            0e 6a 02 6d01 09 626974505553484552

                0e                  - 14 bytes to follow (in hex)
                6a                  - OP_RETURN
                02                  - 2 bytes of pushdata to follow
                6d01                - "communication channel" for memo.cash - "set name" action
                09                  - 9 bytes to follow
                626974505553484552  - "BitPusher" utf-8 encoded bytes --> hex representation

        Currently (this module) only allows up to 220 bytes maximum at present.
        Will soon increase this capability dramatically by allowing for overflow.

        RECOMMENDED WORKFLOW
        # Import private key with bitcash
            my_key = bitcash.PrivateKey('WIF Compressed (base58) here')
            my_key.get_unspents() #necessary step --> updates my_key.unspents object variable

        # Output OP_RETURN pushdata as bytes and store in variable
            pushdata = bitPUSHER.create_pushdata(lst_of_pushdata) --> outputs OP_RETURN pushdata as bytes and stores in variable

        # Create rawtx ready for broadcast (fee = 1 sat/byte; sending 0.0001 BCH back to own address)
            rawtx = my_key.create_transaction([(my_key.address, 0.0001, 'bch')], fee=1, message=pushdata, custom_PUSHDATA=True)

        # Broadcast rawtx
            bitcash.network.services.NetworkAPI.broadcast_tx(rawtx)
            --> look at block explorer or wallet to see new transaction!
    '''
    pushdata = b''

    for i in range(len(lst_of_pushdata)):

        encoding = lst_of_pushdata[i][1]
        if encoding == 'utf-8':
            pushdata += len(lst_of_pushdata[i][0]).to_bytes(1, byteorder='little') + lst_of_pushdata[i][0].encode('utf-8')

        elif encoding == 'hex' and len(lst_of_pushdata[i][0]) % 2 != 0:
            raise ValueError("hex encoded pushdata must have length = a multiple of two")

        elif encoding == 'hex' and len(lst_of_pushdata[i][0]) % 2 == 0:
            pushdata += (len(lst_of_pushdata[i][0]) // 2).to_bytes(1, byteorder='little') + bitcash.utils.hex_to_bytes(lst_of_pushdata[i][0])

    # check for size
    if len(pushdata) > 220:
        raise ValueError("Total bytes in OP_RETURN cannot exceed 220 bytes at present - apologies")

    return pushdata
