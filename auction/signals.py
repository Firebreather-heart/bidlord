import logging
from django.db.models.signals import post_delete
from django.dispatch import receiver
from .models import AuctionItem 

logger = logging.getLogger('auction')

@receiver(post_delete, sender=AuctionItem)
def remove_auction_from_redis(sender, instance, **kwargs):
    try:
        redis_key = "auction_schedule"
        member = instance.id
        cache.client.get_client().zrem(redis_key, member)  # type:ignore
    except Exception as e:
        logger.error(f"Error removing auction item {instance.id} from Redis sorted set: {e}")