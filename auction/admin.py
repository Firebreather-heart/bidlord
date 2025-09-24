from django.contrib import admin
from .models import AuctionItem, AuctionItemImage, Auction, Bid


@admin.register(AuctionItemImage)
class AuctionItemImageAdmin(admin.ModelAdmin):
    list_display = ("id", "creator", "size", "is_deleted",
                    "is_archived", "created_at_display")
    search_fields = ("id", "creator__username")
    list_filter = ("is_deleted", "is_archived")

    def created_at_display(self, obj):
        return getattr(obj, 'created_at', None)


@admin.register(AuctionItem)
class AuctionItemAdmin(admin.ModelAdmin):
    list_display = ("item_name", "creator", "auction_start_date", "auction_end_date",
                    "active_price", "price_currency", "is_deleted", "is_archived")
    search_fields = ("item_name", "creator__username")
    list_filter = ("price_currency", "is_deleted", "is_archived")


@admin.register(Auction)
class AuctionAdmin(admin.ModelAdmin):
    list_display = ("id", "item_for_sale",
                    "current_price", "ongoing", "winner")
    search_fields = ("id", "item_for_sale__item_name", "winner__username")
    list_filter = ("ongoing",)


@admin.register(Bid)
class BidAdmin(admin.ModelAdmin):
    list_display = ("id", "auction", "creator", "amount", "is_deleted")
    search_fields = ("id", "auction__id", "creator__username")
    list_filter = ("is_deleted",)
