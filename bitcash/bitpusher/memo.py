from bitcash.bitpusher import bitpusher

'''
Simple API for interacting with the memo.cash OP_RETURN protocol
'''

ACTION_SET_NAME = '6d01'
ACTION_POST = '6d02'
ACTION_REPLY = '6d03'
ACTION_LIKE_OR_TIP = '6d04'
ACTION_SET_PROFILE_TEXT = '6d05'
ACTION_FOLLOW_USER = '6d06'
ACTION_UNFOLLOW_USER = '6d07'
ACTION_SET_PROFILE_PICTURE = '6d0a'
ACTION_REPOST_MEMO = '6d0b'
ACTION_POST_TOPIC_MESSAGE = '6d0c'
ACTION_TOPIC_FOLLOW = '6d0d'
ACTION_TOPIC_UNFOLLOW = '6d0e'
ACTION_CREATE_POLL = '6d10'
ACTION_ADD_POLL_OPTION = '6d13'
ACTION_POLL_VOTE = '6d14'


def set_name(PrivateKey, new_name, fee=1):
    # Sets name of memo.cash account to new_name
    # name(217)
    lst_of_pushdata = [(ACTION_SET_NAME, 'hex'), (new_name, 'utf-8')]
    return bitpusher.bitpush(PrivateKey, lst_of_pushdata, fee=1)


def post(PrivateKey, post, fee=1):
    # Posts on memo.cash account
    # message(217)
    lst_of_pushdata = [(ACTION_POST, 'hex'), (post, 'utf-8')]
    return bitpusher.bitpush(PrivateKey, lst_of_pushdata, fee=1)


def reply(PrivateKey, tx_hash, reply, fee=1):
    # Replies on memo.cash account
    # txhash(30), message(184)
    lst_of_pushdata = [(ACTION_REPLY, 'hex'),
                       (tx_hash, 'hex'), (reply, 'utf-8')]
    return bitpusher.bitpush(PrivateKey, lst_of_pushdata, fee=1)


'''
# FIXME: Will need to add in ability to specify how much to tip the person (for address corresponding to the tx_hash)

def like_or_tip(PrivateKey, tx_hash, tip, fee=1):
    # Sends a tip on memo.cash account
    # txhash(30)
    lst_of_pushdata = [(ACTION_LIKE_OR_TIP, 'hex'), (tx_hash, 'hex'), (tip, 'utf-8')]
    return bitpusher.bitpush(PrivateKey, lst_of_pushdata, fee=1)'''


def set_profile_text(PrivateKey, profile_text, fee=1):
    # Sets profile text on memo.cash account
    # message(217)
    lst_of_pushdata = [(ACTION_SET_PROFILE_TEXT, 'hex'),
                       (profile_text, 'utf-8')]
    return bitpusher.bitpush(PrivateKey, lst_of_pushdata, fee=1)


def follow_user(PrivateKey, address, fee=1):
    # Sets profile text on memo.cash account
    # address(35)
    lst_of_pushdata = [(ACTION_FOLLOW_USER, 'hex'), (address, 'utf-8')]
    return bitpusher.bitpush(PrivateKey, lst_of_pushdata, fee=1)


def unfollow_user(PrivateKey, address, fee=1):
    # Sets profile text on memo.cash account
    # address(35)
    lst_of_pushdata = [(ACTION_UNFOLLOW_USER, 'hex'), (address, 'utf-8')]
    return bitpusher.bitpush(PrivateKey, lst_of_pushdata, fee=1)


def set_profile_picture(PrivateKey, picture_url, fee=1):
    # Sets profile text on memo.cash account
    # url(217)
    lst_of_pushdata = [(ACTION_SET_PROFILE_PICTURE, 'hex'),
                       (picture_url, 'utf-8')]
    return bitpusher.bitpush(PrivateKey, lst_of_pushdata, fee=1)


'''
# FIXME: Not actually yet part of the memo.cash protocol - here only for completion

def repost_memo(PrivateKey, memo, fee=1):
    # Sets profile text on memo.cash account
    # txhash(30), message(184)
    lst_of_pushdata = [(ACTION_REPOST_MEMO, 'hex'), (memo, 'utf-8')]
    return bitpusher.bitpush(PrivateKey, lst_of_pushdata, fee=1)'''


def post_topic_message(PrivateKey, topic_name, message, fee=1):
    # Sets profile text on memo.cash account
    # topic_name(variable), message(214 - topic length)
    lst_of_pushdata = [(ACTION_POST_TOPIC_MESSAGE, 'hex'),
                       (topic_name, 'utf-8'), (message, 'utf-8')]
    return bitpusher.bitpush(PrivateKey, lst_of_pushdata, fee=1)


def topic_follow(PrivateKey, topic_name, fee=1):
    # Sets profile text on memo.cash account
    # topic_name(variable)
    lst_of_pushdata = [(ACTION_TOPIC_FOLLOW, 'hex'), (topic_name, 'utf-8')]
    return bitpusher.bitpush(PrivateKey, lst_of_pushdata, fee=1)


def topic_unfollow(PrivateKey, topic_name, fee=1):
    # Sets profile text on memo.cash account
    # topic_name(variable)
    lst_of_pushdata = [(ACTION_TOPIC_UNFOLLOW, 'hex'), (topic_name, 'utf-8')]
    return bitpusher.bitpush(PrivateKey, lst_of_pushdata, fee=1)


'''
# FIXME: Not ready yet

def create_poll(PrivateKey, poll_type, option_count, question, fee=1):
    # Sets profile text on memo.cash account
    # poll_type(1), option_count(1), question(209)
    lst_of_pushdata = [(ACTION_TOPIC_UNFOLLOW, 'hex'), (poll_type, 'hex'), (option_count, 'hex'), (question, 'utf-8')]
    return bitpusher.bitpush(PrivateKey, lst_of_pushdata, fee=1)'''

'''
# FIXME: Not ready yet

def add_poll_option(PrivateKey, poll_tx_hash, option, fee=1):
    # Sets profile text on memo.cash account
    # poll_txhash(30), option(184)
    lst_of_pushdata = [(ACTION_TOPIC_UNFOLLOW, 'hex'), (poll_tx_hash, 'hex'), (option, 'utf-8')]
    return bitpusher.bitpush(PrivateKey, lst_of_pushdata, fee=1)'''

'''
# FIXME: Not ready yet

def poll_vote(PrivateKey, poll_tx_hash, comment, fee=1):
    # Sets profile text on memo.cash account
    # poll_txhash(30), comment(184)
    lst_of_pushdata = [(ACTION_TOPIC_UNFOLLOW, 'hex'), (poll_tx_hash, 'hex'), (comment, 'utf-8')]
    return bitpusher.bitpush(PrivateKey, lst_of_pushdata, fee=1)'''
