import decimal
import logging
import celery
import django.contrib.auth
import django.utils as dj_utils
from . import models, utils

logger = logging.getLogger('custom_debug')


class ValidatnErrors:
    """ Hints to user on lot auction page."""
    INCORRECT_PARAM = "{} parameter is incorrect!"
    NOT_PRICE = "{} can contain only digits and '.'!"
    DOES_NOT_EXIST = "{} object doesn't exist!"
    USER_NOT_EXIST = "Please log in."
    NO_AUCTN = "Auction isn't in progress!"
    SMALL_STAKE = "Your input stake is less chan next minimum possible stake!"
    MODIFIED_STATE = "Auction state was modified after creation of job. Expected: {0}, "\
        "current: {1}."


@celery.shared_task
def submitStake(lotId: str, userId: int, inputStake: str = None) -> tuple([dict, str, str | None]):
    """ Validate input parameters, add inputStake to database, calculate next minimal stake.
        If inputStake is None, inputStake = next minimal stake.
    Args:
        lotId (str): lot id
        userId (int): id of user who wants to submit stake
        inputStake (str): stake value
    Returns:
        tuple([dict, str, str | None]): (newStake, f"{nextMinStake:,.2f}", errorText)
                                         newStake keys: Stake.TIME_N, Stake.USER_N, Stake.STAKE_N
    """
    newStake, nextMinStake = None, 0.0
    errorReturn = (newStake, f"{nextMinStake:,.2f}")

    try:
        if inputStake:
            inputStake = decimal.Decimal(inputStake)
    except Exception:
        return *errorReturn, ValidatnErrors.NOT_PRICE.format('Input stake')

    try:
        lotId = int(lotId)
    except ValueError:
        return *errorReturn, ValidatnErrors.INCORRECT_PARAM.format('lotId')

    try:
        lot = models.Lot.objects.get(pk=lotId)
    except models.Lot.DoesNotExist:
        return *errorReturn, ValidatnErrors.DOES_NOT_EXIST.format('Lot')

    if lot.auctionState != models.Lot.AuctionStates.STARTED:
        return *errorReturn, ValidatnErrors.NO_AUCTN

    try:
        User = django.contrib.auth.get_user_model()
        user = User.objects.get(pk=userId)
    except User.DoesNotExist:
        return *errorReturn, ValidatnErrors.USER_NOT_EXIST

    prevStake = lot.startPrice
    try:
        lastStake = models.Stake.objects.filter(lot_id=lotId).last()
        if lastStake:
            prevStake = lastStake.stakeValue
    except models.Stake.DoesNotExist:
        pass

    if lastStake:
        minPriceStep = utils.calcMinStakeStep(prevStake)
    else:
        minPriceStep = decimal.Decimal('0.00')

    if not inputStake:
        inputStake = prevStake + minPriceStep
    elif inputStake < prevStake + minPriceStep:
        return *errorReturn, ValidatnErrors.SMALL_STAKE
    minPriceStep = utils.calcMinStakeStep(inputStake)
    nextMinStake = inputStake + minPriceStep

    newObj = models.Stake.objects.create(lot=lot, user=user, stakeValue=inputStake)

    newStake = {models.Stake.TIME_N: getattr(newObj, models.Stake.TIME_N)
                .strftime(utils.TIME_FORMAT),
                models.Stake.USER_N: user.username,
                models.Stake.STAKE_N: f"{getattr(newObj, models.Stake.STAKE_N):,.2f}"}

    return newStake, f"{nextMinStake:,.2f}", None


@celery.shared_task
def modifyAuctnState(lotId: int, initState: str, newState: str, startTime: str,
                     endTime: str) -> None:
    """ Transfer auction state from NOT_STARTED to STARTED or from STARTED to FINISHED
        if auctionState and auction time aren't changed after scheduling of this task.
    Args:
        lotId (int): lot id
        initState (str): auctionState Lot field on the moment of scheduling this task
        newState (str): auctionState Lot field after finishing of this task
        startTime (str): auction start time
        endTime (str): auction end time
    """
    try:
        lot = models.Lot.objects.get(pk=lotId)
    except models.Lot.DoesNotExist:
        logger.debug(ValidatnErrors.DOES_NOT_EXIST.format('Lot'))
        return

    if lot.auctionState != initState:
        logger.debug(ValidatnErrors.MODIFIED_STATE.format(initState, lot.auctionState))
        return

    curTime = dj_utils.timezone.now()
    startTime = celery.utils.iso8601.parse_iso8601(startTime)
    endTime = celery.utils.iso8601.parse_iso8601(endTime)

    # NOT_STARTED-STARTED
    if initState == models.Lot.AuctionStates.NOT_STARTED and \
        newState == models.Lot.AuctionStates.STARTED and \
            curTime >= startTime and curTime < endTime and startTime == lot.startTime:
        lot.auctionState = newState
        lot.save()

    # STARTED-FINISHED
    if initState == models.Lot.AuctionStates.STARTED and \
        newState == models.Lot.AuctionStates.FINISHED and \
            curTime >= endTime and endTime == lot.endTime:
        lot.auctionState = newState
        lot.save()
