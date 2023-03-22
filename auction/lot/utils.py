import logging
import decimal
from . import models

TIME_FORMAT = '%b %d, %Y %H:%M:%S.%f %z'  # for UI
logger = logging.getLogger('custom_debug')


def calcMinStakeStep(prevStake: decimal.Decimal) -> decimal.Decimal:
    """ Calculate minimal stake step using the last stake of current auction.
    Args:
        prevStake (decimal.Decimal): last stakeValue
    Returns:
        decimal.Decimal: minimal stake step
    """
    if prevStake < models.Lot.MIN_START_PRICE:
        return models.Lot.MIN_START_PRICE

    minStakeStep = prevStake * models.Stake.MIN_STEP_RATE
    numDigitsBeforeDot = len(str(minStakeStep).split('.')[0])
    numDigitsToRound = models.Stake.NUM_SIGNIFICANT_DIGITS - numDigitsBeforeDot
    minStakeStep = round(minStakeStep, numDigitsToRound)
    minStakeStep = round(minStakeStep, models.PRICE_DECIMAL_PLACES)
    minStakeStep = max(models.Stake.MIN_PRICE_STEP, minStakeStep)
    logging.debug(f"{prevStake=}, {minStakeStep=}")
    return minStakeStep
