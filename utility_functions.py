# backend functions
from random import randint


def dice_roll(rolls, dice_type):
    """
    dice roll function, with support for multiple rolls
    :param rolls: number of rolls to do
    :param dice_type: maximum value possible for the desired dice (es 6 for a d6)
    :return: dictionary containing every roll and a total sum
    """
    rolls_log = []
    for i in range(rolls):
        rolls_log.append(randint(1, dice_type))
    total = sum(rolls_log)

    return {'rolls_log': rolls_log, 'rolls_total': total}


def middle (a:int, b:int, c:int):
    return sorted([a, b, c])[1]
