import uuid
from datetime import timedelta

from django.utils import timezone
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from auction.models import AuctionItem, Auction, Bid, AuctionItemImage


User = get_user_model()


def auth_client(user):
    refresh = RefreshToken.for_user(user)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")
    return client


class AuctionItemFlowTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="seller", email="seller@example.com", password="pass1234"
        )
        self.client = auth_client(self.user)

    def test_create_and_list_auction_items(self):
        start = timezone.now() + timedelta(hours=1)
        end = start + timedelta(hours=2)
        payload = {
            "item_name": "Vintage Watch",
            "details": "Rare collectors edition",
            "auction_start_date": start.isoformat(),
            "auction_end_date": end.isoformat(),
            "initial_price": "100.00",
            "price_currency": "Dollars",
        }
        url = reverse("create_auction_item")
        res = self.client.post(url, payload, format="json")
        body = res.json()
        self.assertEqual(res.status_code, 201, body)
        item_id = body.get("data", {}).get("id")

        list_url = reverse("list_auction_item")
        list_res = self.client.get(list_url)
        list_body = list_res.json()
        self.assertEqual(list_res.status_code, 200)
        self.assertTrue(len(list_body.get("data")) >= 1)

        detail_url = reverse("auction_item_detail",
                             kwargs={"item_id": item_id})
        detail_res = self.client.get(detail_url)
        detail_body = detail_res.json()
        self.assertEqual(detail_res.status_code, 200)
        self.assertEqual(detail_body["data"]["item_name"], "Vintage Watch")

    def test_update_and_delete_auction_item(self):
        start = timezone.now() + timedelta(hours=1)
        end = start + timedelta(hours=2)
        item = AuctionItem.objects.create(
            creator=self.user,
            item_name="Old Camera",
            details="Working condition",
            auction_start_date=start,
            auction_end_date=end,
            initial_price="50.00",
            active_price="50.00",
            price_currency="Dollars",
        )

        update_url = reverse("update_delete_auction_item",
                             kwargs={"item_id": str(item.id)})
        res = self.client.put(
            update_url, {"item_name": "Updated Camera"}, format="json")
        res_body = res.json()
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res_body["data"]["item_name"], "Updated Camera")

        # not ongoing -> can delete
        del_res = self.client.delete(update_url)
        self.assertIn(del_res.status_code, (200, 204))


class AuctionBiddingTests(APITestCase):
    def setUp(self):
        self.seller = User.objects.create_user(
            username="seller", email="seller@example.com", password="pass1234"
        )
        self.bidder = User.objects.create_user(
            username="bidder", email="bidder@example.com", password="pass1234"
        )
        start = timezone.now() - timedelta(minutes=5)
        end = timezone.now() + timedelta(minutes=30)
        self.item = AuctionItem.objects.create(
            creator=self.seller,
            item_name="Laptop",
            details="Gaming",
            auction_start_date=start,
            auction_end_date=end,
            initial_price="200.00",
            active_price="200.00",
            price_currency="Dollars",
        )
        self.auction = Auction.objects.create(
            item_for_sale=self.item,
            current_price=self.item.initial_price,
            ongoing=True,
        )
        self.client = auth_client(self.bidder)

    def test_place_bid_enqueues_task(self):
        url = reverse("place_bid", kwargs={"auction_id": str(self.auction.id)})
        # Patch Celery delay to avoid needing a broker in tests
        from unittest.mock import patch
        with patch("auction.views.process_bid") as mocked_task:
            mocked_task.delay.return_value = None
            res = self.client.post(url, {"amount": 250}, format="json")
            self.assertEqual(res.status_code, 202)


class SearchTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="seller", email="seller@example.com", password="pass1234"
        )
        self.client = APIClient()
        start = timezone.now() + timedelta(hours=1)
        end = start + timedelta(hours=2)
        AuctionItem.objects.create(
            creator=self.user,
            item_name="Apple iPhone",
            details="Smartphone",
            auction_start_date=start,
            auction_end_date=end,
            initial_price="300.00",
            active_price="300.00",
            price_currency="Dollars",
        )

    def test_master_search_requires_query(self):
        url = reverse("master_search")
        res = self.client.get(url)
        self.assertEqual(res.status_code, 400)

    def test_master_search_returns_results(self):
        url = reverse("master_search")
        res = self.client.get(url, {"q": "iphone"})
        self.assertEqual(res.status_code, 200)
        self.assertIn("data", res.json())
