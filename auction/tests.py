from datetime import timedelta
from unittest.mock import patch, MagicMock
from django.test import TestCase, override_settings
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.core.cache import cache

from auction.models import AuctionItem, Auction, Bid
from auction.tasks import create_pending_auctions_from_cache, process_bid, close_finished_auctions

User = get_user_model()


class AuctionModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="pass123"
        )

    def test_auction_item_creation(self):
        start = timezone.now() + timedelta(hours=1)
        end = start + timedelta(hours=2)

        item = AuctionItem.objects.create(
            creator=self.user,
            item_name="Test Item",
            details="Test description",
            auction_start_date=start,
            auction_end_date=end,
            initial_price="100.00",
            price_currency="Dollars"
        )

        self.assertEqual(item.active_price, item.initial_price)
        self.assertEqual(str(
            item), f"Test Item for sale :{start} -> {end}               -> 100.00 : Dollars")

    def test_auction_creation(self):
        start = timezone.now() - timedelta(minutes=5)
        end = timezone.now() + timedelta(minutes=30)

        item = AuctionItem.objects.create(
            creator=self.user,
            item_name="Laptop",
            details="Gaming laptop",
            auction_start_date=start,
            auction_end_date=end,
            initial_price="500.00",
            active_price="500.00",
            price_currency="Dollars"
        )

        auction = Auction.objects.create(
            item_for_sale=item,
            current_price=item.initial_price,
            ongoing=True
        )

        self.assertEqual(str(auction), f"Auction for {item}")
        self.assertTrue(auction.ongoing)

    def test_bid_creation(self):
        start = timezone.now() - timedelta(minutes=5)
        end = timezone.now() + timedelta(minutes=30)

        item = AuctionItem.objects.create(
            creator=self.user,
            item_name="Phone",
            details="Smartphone",
            auction_start_date=start,
            auction_end_date=end,
            initial_price="200.00",
            active_price="200.00",
            price_currency="Dollars"
        )

        auction = Auction.objects.create(
            item_for_sale=item,
            current_price=item.initial_price,
            ongoing=True
        )

        bid = Bid.objects.create(
            creator=self.user,
            auction=auction,
            amount="250.00"
        )

        self.assertEqual(
            str(bid), f"Bid placed on Auction {auction.id} by {self.user} (250.00)")


@override_settings(CHANNEL_LAYERS={
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer",
    }
})
class CeleryTaskTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="seller", email="seller@example.com", password="pass123"
        )

    @patch('auction.tasks.cache.client.get_client')
    def test_create_pending_auctions_task(self, mock_redis):
        mock_redis_client = MagicMock()
        mock_redis.return_value = mock_redis_client

        start = timezone.now() + timedelta(minutes=3)
        end = start + timedelta(hours=1)

        item = AuctionItem.objects.create(
            creator=self.user,
            item_name="Watch",
            details="Vintage watch",
            auction_start_date=start,
            auction_end_date=end,
            initial_price="150.00",
            active_price="150.00",
            price_currency="Dollars"
        )

        mock_redis_client.zrangebyscore.return_value = [str(item.id).encode()]

        result = create_pending_auctions_from_cache()

        self.assertIn("Total pending auctions created: 1", result)
        self.assertTrue(Auction.objects.filter(item_for_sale=item).exists())

    @patch('auction.tasks.cache.lock')
    def test_process_bid_task(self, mock_cache_lock):
        mock_lock = MagicMock()
        mock_cache_lock.return_value.__enter__ = MagicMock(
            return_value=mock_lock)
        mock_cache_lock.return_value.__exit__ = MagicMock(return_value=False)

        start = timezone.now() - timedelta(minutes=5)
        end = timezone.now() + timedelta(minutes=30)

        item = AuctionItem.objects.create(
            creator=self.user,
            item_name="Tablet",
            details="Android tablet",
            auction_start_date=start,
            auction_end_date=end,
            initial_price="300.00",
            active_price="300.00",
            price_currency="Dollars"
        )

        auction = Auction.objects.create(
            item_for_sale=item,
            current_price=item.initial_price,
            ongoing=True
        )

        result = process_bid(str(self.user.id), str(auction.id), 350.0) #type:ignore

        auction.refresh_from_db()
        self.assertEqual(float(auction.current_price), 350.0)
        self.assertTrue(Bid.objects.filter(
            auction=auction, amount=350.0).exists())

    def test_close_finished_auctions_task(self):
        past_time = timezone.now() - timedelta(hours=1)

        item = AuctionItem.objects.create(
            creator=self.user,
            item_name="Book",
            details="Rare book",
            auction_start_date=past_time - timedelta(hours=2),
            auction_end_date=past_time,
            initial_price="50.00",
            active_price="75.00",
            price_currency="Dollars"
        )

        auction = Auction.objects.create(
            item_for_sale=item,
            current_price="75.00",
            ongoing=True
        )

        bid = Bid.objects.create(
            creator=self.user,
            auction=auction,
            amount="75.00"
        )

        result = close_finished_auctions()

        auction.refresh_from_db()
        self.assertFalse(auction.ongoing)
        self.assertEqual(auction.winner, self.user)
        self.assertIn("Closed 1 auctions", result)
