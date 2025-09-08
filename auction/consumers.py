import json
import logging 
from channels.generic.websocket import AsyncWebsocketConsumer

logger = logging.getLogger('auction')

class AuctionConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.auction_id = self.scope['url_route']['kwargs']['auction_id']
        self.auction_group_name = f'auction_{self.auction_id}'

        await self.channel_layer.group_add(  # type: ignore
            self.auction_group_name,
            self.channel_name
        )
        await self.accept()
        logger.info(f"websocker connected for auction {self.auction_id}")

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard( # type: ignore
            self.auction_group_name,
            self.channel_name
        )
        logger.info(f"Websocket disconnected for auction {self.auction_id}")

    async def auction_update(self, event):
        message = event['mesage']
        await self.send(text_data=json.dumps({
            'type': 'auction_update',
            'data':message
        }))
