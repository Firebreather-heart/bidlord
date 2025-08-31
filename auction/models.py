import uuid

from django.db import models
from django.contrib.auth import get_user_model

from storage.size_adapters import get_size_adapter

from .managers import ActiveAuctionManager, ObjectManager

User = get_user_model()

# Create your models here.


class Currency(models.TextChoices):
    DOLLAR = 'Dollars', 'Dollars'
    POUNDS = 'Pounds', 'Pounds'
    NAIRA = 'Naira', 'Naira'
    EUROS = 'Euro', 'Euro'


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class UUIDModel(models.Model):
    id = models.UUIDField(
        unique=True, primary_key=True, default=uuid.uuid4
    )

    class Meta:
        abstract = True

    def delete(self, *args, **kwargs):
        """Soft delete the model instance."""
        self.is_deleted = True
        self.save(*args, **kwargs)


class AuctionItemImage(UUIDModel):
    # Media should seriously be handled by #cloudinary or the like, so nothing beyond this will be provided
    image = models.ImageField(upload_to='/auction_images', )
    size = models.BigIntegerField(default=0)
    creator = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='created_auction_item_images')
    is_deleted = models.BooleanField(default=False)
    # archived items can't be modified
    is_archived = models.BooleanField(default=False)
    available_images = ObjectManager()

    def get_url(self):
        return self.image.url
    
    def soft_delete(self):
        self.is_deleted = True 
        self.save()

    def save(self, *args, **kwargs):
        if not self.size and self.image:
            adapter = get_size_adapter(self.image.storage)
            self.size = adapter.get_size(self.image)
        super().save(*args, **kwargs)


class AuctionItem(TimeStampedModel, UUIDModel):
    creator = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="created_auction_items")
    images = models.ManyToManyField(AuctionItemImage, )
    item_name = models.CharField(max_length=100)
    details = models.TextField()
    auction_start_date = models.DateTimeField()
    auction_end_date = models.DateTimeField()
    initial_price = models.DecimalField(max_digits=30, decimal_places=2)
    active_price = models.DecimalField(max_digits=30, decimal_places=2)
    price_currency = models.CharField(
        max_length=10, choices=Currency.choices, default=Currency.DOLLAR)
    available_items = ObjectManager()
    is_deleted = models.BooleanField(default=False)
    is_archived = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Auction Item"
        verbose_name_plural = "Auction Items"

    def __str__(self) -> str:
        return f"{self.item_name} for sale :{self.auction_start_date} -> {self.auction_end_date} \
              -> {self.active_price} : {self.price_currency}"

    def save(self, *args, **kwargs):
        if not self.id:
            self.active_price = self.initial_price
        return super().save(*args, **kwargs)


class Auction(TimeStampedModel, UUIDModel):
    """Auctions are system created, not user created, based on the time specified on items"""
    item_for_sale = models.OneToOneField(
        'AuctionItem', on_delete=models.CASCADE, related_name='auction')
    current_price = models.DecimalField(max_digits=30, decimal_places=2)
    ongoing = models.BooleanField(default=True)
    active_auctions = ActiveAuctionManager()
    winner = models.ForeignKey(
        User, on_delete=models.CASCADE, null=True, blank=True,)

    def __str__(self) -> str:
        return f"Auction for {self.item_for_sale}"


class Bid(TimeStampedModel, UUIDModel):
    creator = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="bids_placed")
    auction = models.ForeignKey(
        'Auction', on_delete=models.CASCADE, related_name="active_bids")
    amount = models.DecimalField(max_digits=30, decimal_places=2)
    is_deleted = models.BooleanField(default=False)
    available_bids = ObjectManager()
    # I won't add a currency field, no point in bidding with a different currency

    def __str__(self) -> str:
        return f"Bid placed on Auction {self.auction.id} by {self.creator} ({self.amount})"
