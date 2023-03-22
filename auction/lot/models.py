import decimal
import datetime
import logging
from django.db import models
from django.urls import reverse
from django.conf import settings as dj_settings
import django.utils as dj_utils
import django.core.exceptions as dj_exceptions
from . import tasks
from auction.celery_app import celeryApp
from auction.redis_app import redisApp

PRICE_DIGITS = 12
PRICE_DECIMAL_PLACES = 2
logger = logging.getLogger('custom_debug')


class ValidatnErrors:
    """ Hints to admin on the form based on class Lot."""
    NEGATIVE_PRICE = "StartPrice can't be negative!"
    SET_TIME = "Please set auction StartTime and auction EndTime."
    INCORRECT_TIME = "The EndTime can't be greater than the StartTime!"
    INCORRECT_TIME_NS = "When auction state is 'Not started', the following inequality must hold: "\
        "auction EndTime > auction StartTime > current time."
    INCORRECT_TIME_ST = "When auction state is 'Started', the following inequality must hold: "\
        "auction EndTime > current time > auction StartTime."
    INCORRECT_TIME_FI = "When auction state is 'Finished', the following inequality must hold: "\
        "current time > auction EndTime > auction StartTime."
    NOT_LEGAL = "Auction state transition {} is illegal!"
    NOT_DRAFT = "AuctionState must be 'Draft' for modification of any field!"


class Lot(models.Model):
    """ Lot is one of the objects or group of objects that are being sold."""
    DESCR_LEN = 240
    IMAGE_UPLOAD_TO = 'lots/%Y/%m/%d/'
    MIN_START_PRICE = decimal.Decimal('1.00')
    START_PRICE_VN = 'StartPrice, roubles'

    class AuctionStates(models.TextChoices):
        DRAFT = 'DR', 'Draft'               # set it if you don't know start or end auction time
        NOT_STARTED = 'NS', 'Not started'   # set it to start the auction
        STARTED = 'ST', 'Started'           # only 'modifyAuctnState' task can set this state
        FINISHED = 'FI', 'Finished'         # only 'modifyAuctnState' task can set this state

    # constants describing possible auction state transitions
    # each transition is f'{initialState}-{finalState}' string
    NO_TRANSITN = {f"{AuctionStates.DRAFT}-{AuctionStates.DRAFT}",
                   f"{AuctionStates.NOT_STARTED}-{AuctionStates.NOT_STARTED}",
                   f"{AuctionStates.STARTED}-{AuctionStates.STARTED}",
                   f"{AuctionStates.FINISHED}-{AuctionStates.FINISHED}"}
    INIT_AUCTN_TRANSTN = f"{AuctionStates.DRAFT}-{AuctionStates.NOT_STARTED}"
    LEGAL_TRANSITNS = {*NO_TRANSITN,
                       INIT_AUCTN_TRANSTN,
                       f"{AuctionStates.NOT_STARTED}-{AuctionStates.STARTED}",
                       f"{AuctionStates.STARTED}-{AuctionStates.FINISHED}",
                       f"{AuctionStates.NOT_STARTED}-{AuctionStates.DRAFT}",
                       f"{AuctionStates.STARTED}-{AuctionStates.DRAFT}"}

    description = models.CharField(max_length=DESCR_LEN, blank=False)
    startPrice = models.DecimalField(max_digits=PRICE_DIGITS,
                                     decimal_places=PRICE_DECIMAL_PLACES,
                                     blank=False,
                                     verbose_name=START_PRICE_VN)
    imageLeft = models.ImageField(upload_to=IMAGE_UPLOAD_TO)
    imageRight = models.ImageField(upload_to=IMAGE_UPLOAD_TO)
    startTime = models.DateTimeField()  # auction start time
    endTime = models.DateTimeField()    # auction end time
    auctionState = models.CharField(choices=AuctionStates.choices,
                                    default=AuctionStates.DRAFT,
                                    max_length=len(AuctionStates.NOT_STARTED),
                                    blank=False)
    lastModified = models.DateTimeField(auto_now=True, editable=False)

    class Meta:
        ordering = ['id']
        verbose_name = 'lot'

    def get_absolute_url(self) -> str:
        return reverse('lot:lotStakes', args=[self.id])

    def getValidateAuctnStateTransitn(self, validate: bool = False) -> str:
        """ Detect auction state transition chosen by admin and validate is it legal
            and what fields it's possible to change during this state transition.
        Args:
            validate (bool, optional): whether to check the form filled out by the admin.
                                       Defaults to False.
        Raises:
            dj_exceptions.ValidationError: hint to admin
        Returns:
            str: auction state transition
        """
        try:
            lot = Lot.objects.get(pk=self.pk)
            auctnDbState = lot.auctionState
            auctnDbStateDisplay = lot.get_auctionState_display()
        except Lot.DoesNotExist:
            # first creation
            auctnDbState = Lot.AuctionStates.DRAFT
            auctnDbStateDisplay = auctnDbState.label

        transitn = f"{auctnDbState}-{self.auctionState}"

        if validate:
            if auctnDbState != self.auctionState and transitn not in Lot.LEGAL_TRANSITNS:
                auctnStateDisplay = self.get_auctionState_display()
                transitnDisplay = f"'{auctnDbStateDisplay}' - '{auctnStateDisplay}'"
                raise dj_exceptions.ValidationError(
                    ValidatnErrors.NOT_LEGAL.format(transitnDisplay))

            if transitn in (Lot.LEGAL_TRANSITNS - {Lot.INIT_AUCTN_TRANSTN}) and \
                    self.auctionState != Lot.AuctionStates.DRAFT:
                # can't change any field besides 'auctionState' in these state transitions
                for field in Lot._meta.get_fields():
                    if field.name != 'auctionState' and field.name != Stake._meta.verbose_name:
                        dbValue = getattr(lot, field.name)
                        newValue = getattr(self, field.name)
                        if dbValue != newValue:
                            logger.debug(f"{transitn=}, {field=}, {dbValue=} {newValue=}")
                            raise dj_exceptions.ValidationError(ValidatnErrors.NOT_DRAFT)
        return transitn

    def scheduleAuctnTask(self, prevAuctnState: str, newAuctnState: str,
                          startTime: datetime.datetime) -> None:
        """ Schedule 'modifyAuctnState' celery task for auction state transition.
            Save 'modifyAuctnState' task id in Redis in format:
            'lot':{lotId}:'task_{initialAuctnState}-{finalAuctnState}':{taskId}.
        Args:
            prevAuctnState (str): current auctionState Lot field
            newAuctnState (str): auctionState Lot field after finishing of 'modifyAuctnState' task
            startTime (datetime.datetime): time to launch 'modifyAuctnState' task
        """
        logger.debug("Scheduling auctn tasks...")
        asyncResult = tasks.modifyAuctnState.apply_async(
            (self.pk, prevAuctnState, newAuctnState,
             self.startTime.isoformat(), self.endTime.isoformat()), eta=startTime)
        redisApp.hset(f'lot:{self.id}', mapping={
                      f"task_{prevAuctnState}-{newAuctnState}": asyncResult.task_id})
        logger.debug(f"Task {asyncResult.task_id} for transition {prevAuctnState}-{newAuctnState}"
                     " is created.")

    def revokeAuctnTasks(self, transitn: str) -> None:
        """ Revoke 'modifyAuctnState' celery auction task that was scheduled
            in self.scheduleAuctnTask(..). Remove this task id from Redis.
        Args:
            transitn (str): format - f'{initialAuctnState}-{finalAuctnState}'
        """
        taskId = redisApp.hget(f'lot:{self.id}', f'task_{transitn}')
        if taskId is None:
            logger.debug(f"No tasks have been created for transition {transitn}.")
            return
        taskId = taskId.decode()

        logger.debug(
            f"Revoking task {taskId} for state transition {transitn} of lot with id {self.id}...")
        celeryApp.control.revoke(taskId)
        redisApp.hdel(f'lot:{self.id}', f'task_{transitn}')
        logger.debug(f"Revoke of task {taskId} done")

    def clean(self) -> None:
        """ Validate admin form based on Lot class.
        Raises:
            dj_exceptions.ValidationError: hint to admin
        """
        super(Lot, self).clean()

        if self.startPrice < 0:
            raise dj_exceptions.ValidationError(ValidatnErrors.NEGATIVE_PRICE)

        if self.auctionState in {Lot.AuctionStates.NOT_STARTED, Lot.AuctionStates.STARTED,
                                 Lot.AuctionStates.FINISHED}:
            if self.startTime is None or self.endTime is None:
                raise dj_exceptions.ValidationError(ValidatnErrors.SET_TIME)
            if self.endTime < self.startTime:
                raise dj_exceptions.ValidationError(ValidatnErrors.INCORRECT_TIME)

        curTime = dj_utils.timezone.now()
        if self.auctionState == Lot.AuctionStates.NOT_STARTED and \
                not self.endTime > self.startTime > curTime:
            raise dj_exceptions.ValidationError(ValidatnErrors.INCORRECT_TIME_NS)
        if self.auctionState == Lot.AuctionStates.STARTED and \
                not self.endTime > curTime > self.startTime:
            raise dj_exceptions.ValidationError(ValidatnErrors.INCORRECT_TIME_ST)
        if self.auctionState == Lot.AuctionStates.FINISHED and \
                not curTime > self.endTime > self.startTime:
            raise dj_exceptions.ValidationError(ValidatnErrors.INCORRECT_TIME_FI)

        self.getValidateAuctnStateTransitn(validate=True)  # TODO: False for testing

    def save(self, *args: tuple, **kwargs: dict) -> None:
        """ Validate and save the current instance, scheduling or/and revoking celery auction tasks.
        """
        transitn = self.getValidateAuctnStateTransitn(validate=True)  # TODO: False for testing

        if transitn == f"{Lot.AuctionStates.NOT_STARTED}-{Lot.AuctionStates.DRAFT}":
            self.revokeAuctnTasks(f"{Lot.AuctionStates.NOT_STARTED}-{Lot.AuctionStates.STARTED}")
            self.revokeAuctnTasks(f"{Lot.AuctionStates.STARTED}-{Lot.AuctionStates.FINISHED}")

        if transitn == f"{Lot.AuctionStates.STARTED}-{Lot.AuctionStates.DRAFT}":
            self.revokeAuctnTasks(f"{Lot.AuctionStates.STARTED}-{Lot.AuctionStates.FINISHED}")

        super(Lot, self).save(*args, **kwargs)

        if transitn == Lot.INIT_AUCTN_TRANSTN:
            self.scheduleAuctnTask(
                Lot.AuctionStates.NOT_STARTED, Lot.AuctionStates.STARTED, self.startTime)
            self.scheduleAuctnTask(
                Lot.AuctionStates.STARTED, Lot.AuctionStates.FINISHED, self.endTime)

    def __str__(self) -> str:
        return str(self.id)


class Stake(models.Model):
    """ Auction stake on the lot made by one of users."""
    LOT_VN, TIME_VN, USER_VN, STAKE_VN = 'Lot', 'Time', 'User', 'Stake, roubles'
    LOT_N, TIME_N, USER_N, STAKE_N = 'lot', 'time', 'user', 'stakeValue'
    UI_VN = [TIME_VN, USER_VN, STAKE_VN]
    MIN_PRICE_STEP = decimal.Decimal('1.00')
    MIN_STEP_RATE = decimal.Decimal('0.02')  # nextStake ~ lastStake * (1. + MIN_STEP_RATE)
    NUM_SIGNIFICANT_DIGITS = 2

    lot = models.ForeignKey(Lot, on_delete=models.CASCADE, verbose_name=LOT_VN, blank=False)
    time = models.DateTimeField(auto_now_add=True, editable=False, verbose_name=TIME_VN)
    user = models.ForeignKey(dj_settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             verbose_name=USER_VN, blank=False)
    stakeValue = models.DecimalField(max_digits=PRICE_DIGITS,
                                     decimal_places=PRICE_DECIMAL_PLACES,
                                     verbose_name=STAKE_VN,
                                     blank=False)

    class Meta:
        ordering = ['time']
        verbose_name = 'stake'
