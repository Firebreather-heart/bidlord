from django.urls import path
from . import views

urlpatterns = [
    path('items/', views.AuctionItemListAPIView.as_view(),
         name='list_auction_item'),
    path('items/create/', views.AuctionItemCreateAPIView.as_view(),
         name="create_auction_item"),
    path('items/details/<uuid:item_id>/', views.AuctionItemDetailAPIView.as_view(),
         name='auction_item_detail'),
    path('items/<uuid:item_id>/', views.AuctionItemUpdateDeleteAPIView.as_view(),
         name='update_delete_auction_item'),
    path('items/images/<uuid:auction_id>/',
         views.AuctionItemImagesAPIView.as_view(), name='list_create_delete_auction_item_images'),
    path('', views.AuctionAPIView.as_view(), name="auction_view"),
    path('auctions/<uuid:auction_id>/bid', views.PlaceBidAPIView.as_view(), name='place_bid'),
]
