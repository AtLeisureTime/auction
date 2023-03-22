import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from . import tasks

logger = logging.getLogger("custom_debug")


class AuctnConsumer(AsyncWebsocketConsumer):
    """ The aim of the class is to receive stake from one of users,
        call submitStake Celery task,
        send submitted stake to all users viewing lot page.
    """
    async def connect(self) -> None:
        """ Add channel to the group."""
        self.id = self.scope['url_route']['kwargs']['lot_id']
        self.group_name = f'lot_{self.id}'
        # join group
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        # accept connection
        await self.accept()

    async def disconnect(self, code: int) -> None:
        """ Discard channel from the group."""
        logger.debug(f"Disconnect called: {code=}")
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    async def receive(self, text_data, bytes_data=None) -> None:
        """ Receive data from WebSocket, call submitStake task, send result to the group."""
        logger.debug(f"WebSocket --data--> {text_data}")
        textDataJson = json.loads(text_data)
        inputStake = textDataJson['inputStake'] if textDataJson.get('inputStake') else None
        user = self.scope['user']
        lotId = self.scope['url_route']['kwargs']['lot_id']

        # schedule submitStake task and wait result
        result = tasks.submitStake.delay(lotId, user.id, inputStake)
        newStake, nextMinStake, stakeSubmitError = result.get()
        logger.debug(f"submitStake task output - {nextMinStake=}, {stakeSubmitError=}")

        # send data to each channel in the group
        await self.channel_layer.group_send(
            self.group_name,
            {
                'type': 'newStakeWasAdded',
                'newStake': newStake,
                'nextMinStake': nextMinStake,
                'stakeSubmitError': stakeSubmitError,
                'sender': user.id,
            }
        )

    async def newStakeWasAdded(self, event) -> None:
        """ Send data of 'newStakeWasAdded' event to channel."""
        logger.debug(f"--submitStake result--> WebSocket: {event}")
        await self.send(text_data=json.dumps(event))
