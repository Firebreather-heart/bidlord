import logging
from datetime import timedelta 
from asgiref.sync import async_to_sync

from celery import shared_task 
from channels.layers import get_channel_layer
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db import IntegrityError, transaction 
from django.core.cache import cache


from .models import AuctionItem, Auction , Bid

logger = logging.getLogger('auction')
User = get_user_model()

@shared_task(name='create_pending_auctions_from_cache')
def create_pending_auctions_from_cache():
    """Create pending auctions from cached auction items."""
    redis_key = 'auction_schedule'
    redis_client = cache.client.get_client()  # type:ignore
    now_ts = timezone.now().timestamp()
    five_mins_later_ts = (timezone.now() + timedelta(minutes=5)).timestamp()

    item_ids_to_start = redis_client.zrangebyscore(
        redis_key, now_ts, five_mins_later_ts
    )
    if not item_ids_to_start:
        logger.info("No auction items to start in the next 5 minutes.")
        return
    
    items = AuctionItem.available_items.filter(
        id__in = [item_id.decode('utf-8') for item_id in item_ids_to_start],
        auction__isnull=True,
    )

    created_count = 0
    for item in items:
        try:
            with transaction.atomic():
                Auction.objects.create(
                    item_for_sale=item,
                    current_price=item.initial_price,
                    ongoing=True
                )
                created_count += 1
                logger.info(f"Created pending auction for item {item.id}")
                redis_client.zrem(redis_key, str(item.id))
        except Exception as e:
            logger.error(f"Error creating auction for item {item.id}: {e}")
    logger.info(f"Total pending auctions created: {created_count}")
    return f"Total pending auctions created: {created_count}"

@shared_task(name='process_bid', bind=True, max_retries=3, default_retry_delay=5)
def process_bid(self, user_id, auction_id, amount):
    """Processes a single bid."""
    lock_key = f"acution_lock:{auction_id}"
    lock_timeout = 10

    try:
        with cache.lock(lock_key, timeout=lock_timeout): # type:ignore
            try:
                auction = Auction.objects.select_related('item_for_sale').get(
                    id=auction_id,
                    item_for_sale__auction_start_date__lte=timezone.now(),
                    item_for_sale__auction_end_date__gte=timezone.now(),
                    )
            except Auction.DoesNotExist:
                logger.warning(f"Auction {auction_id} does not exist or is not active.")
                return "Auction does not exist or is not active."
            
            if amount <= auction.current_price:
                logger.warning(f"Bid amount {amount} is not higher than current price {auction.current_price}.")
                return "Bid amount must be higher than current price."
            
            with transaction.atomic():
                auction.current_price = amount
                auction.save(update_fields=['current_price'])
                auction.item_for_sale.active_price = amount
                auction.item_for_sale.save(update_fields=['active_price'])

                bid = Bid.objects.create(
                    auction = auction,
                    creator = user_id,
                    amount = amount
                )
                logger.info(f"Bid {bid.id} placed on auction {auction.id} by user {user_id} for amount {amount}.")

                channel_layer = get_channel_layer()
                group_name = f"auction_{auction_id}"
                user = User.objects.get(id=user_id)

                async_to_sync(channel_layer.group_send)( #type:ignore
                    group_name,
                    {
                        "type": "auction.update",
                        "message": {
                            "new_price": f"{amount:.2f}",
                            "currency": auction.item_for_sale.price_currency,
                            "bidder": user.username,
                            "timestamp": bid.created_at.isoformat(),
                        }
                    }
                )
                logger.info(f"Successfuly processed bid of {amount} for auction {auction_id}")
    except IntegrityError as e:
        logger.error(f"Database error processing bid for auction {auction_id}: {e}")
    except Exception as e:
        logger.error(f"Error processing bid for auction {auction_id}: {e}")
        try:
            self.retry(exc=e)
        except self.MaxRetriesExceededError:
            logger.error(f"Max retries exceeded for bid on auction {auction_id}")
            return "Failed to process bid after multiple attempts."
    return "Bid processed successfully."

