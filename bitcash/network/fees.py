# import requests
# from requests.exceptions import ConnectionError, HTTPError, Timeout

# Ideally, fast, medium, slow would correlate with actually blocks out.
# Fast, really shoot for getting into the next block no matter what.
# Medium should get in within the next couple blocks, 90% certainty.
# Slow, in a few hours, 90% certainty.
# The default should be medium so you can go up/down from there.
DEFAULT_FEE_FAST = 24
DEFAULT_FEE_MEDIUM = 16
DEFAULT_FEE_SLOW = 8

# FIXME: Need to add in a fees API. Issue #1
# URL = 'https://bitcoincashfees.earn.com/api/v1/fees/recommended'

FEE_SPEED_FAST = 'fast'
FEE_SPEED_MEDIUM = 'medium'
FEE_SPEED_SLOW = 'slow'


# FIXME: Not sure if this is better, bools are better, or creating its
# own type is better.
def get_fee(speed=FEE_SPEED_MEDIUM):
    """Gets the recommended satoshi per byte fee.

    :param speed: One of: 'fast', 'medium', 'slow'.
    :type speed: ``string``
    :rtype: ``int``
    """
    if speed == FEE_SPEED_FAST:
        return DEFAULT_FEE_FAST
    elif speed == FEE_SPEED_MEDIUM:
        return DEFAULT_FEE_MEDIUM
    elif speed == FEE_SPEED_SLOW:
        return DEFAULT_FEE_SLOW
    else:
        raise ValueError('Invalid speed argument.')
