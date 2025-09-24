import logging
from django.db.models.signals import post_delete, post_save 
from django.contrib.postgres.search import SearchVector
from django.core.cache import cache
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


@receiver(post_save, sender=AuctionItem)
def update_search_vector(sender, instance, **kwargs):
    """
    Automatically update the search_vector field whenever an AuctionItem is saved.
    """
    AuctionItem.objects.filter(pk=instance.pk).update(
        search_vector=SearchVector(
            'item_name', 'details', config='english')
    )
