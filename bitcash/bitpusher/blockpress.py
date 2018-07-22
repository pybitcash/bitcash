from bitcash.bitpusher import bitpusher

'''
PLEASE TAKE NOTE:

Blockpress.com's syncing script has crashed and therefore posts will not appear on blockpress.com until they fix it.
You posts WILL be recognised on block explorers and on https://www.chainfeed.org/

Hopefully this bug on the blockpress server is fixed soon

'''

BLOCKPRESS_SET_NAME = '8d01'
BLOCKPRESS_CREATE_TEXT_POST = '8d02'
BLOCKPRESS_REPLY_TO_POSTS = '8d03'
BLOCKPRESS_LIKE_POST = '8d04'
BLOCKPRESS_FOLLOW_PROFILE = '8d06'
BLOCKPRESS_UNFOLLOW_PROFILE = '8d07'
BLOCKPRESS_SET_PROFILE_HEADER = '8d08'
BLOCKPRESS_CREATE_MEDIA_POST = '8d09'
BLOCKPRESS_SET_PROFILE_AVATAR = '8d010'
BLOCKPRESS_CREATE_POST_IN_COMMUNITY = '8d11'


def set_name(PrivateKey, new_name, fee=1):
    '''Sets name of blockpress.com account to new_name
    param: new_name(77 bytes)'''

    lst_of_pushdata = [(BLOCKPRESS_SET_NAME, 'hex'), (new_name, 'utf-8')]
    return bitpusher.bitpush(PrivateKey, lst_of_pushdata, fee=1)


def create_text_post(PrivateKey, text, fee=1):
    # Sets name of blockpress.com account to new_name
    # text(217) (upgraded from 77 bytes)
    lst_of_pushdata = [(BLOCKPRESS_CREATE_TEXT_POST, 'hex'), (text, 'utf-8')]
    return bitpusher.bitpush(PrivateKey, lst_of_pushdata, fee=1)


def reply_to_posts(PrivateKey, txhash, text, fee=1):
    # Sets name of blockpress.com account to new_name
    # txhash(32) Text (184 bytes)
    lst_of_pushdata = [(BLOCKPRESS_SET_NAME, 'hex'),
                       (txhash, 'hex'), (text, 'utf-8')]
    return bitpusher.bitpush(PrivateKey, lst_of_pushdata, fee=1)


"""
more functions to go here
"""
