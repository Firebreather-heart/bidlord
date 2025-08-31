from django.urls import path
from . import views

urlpatterns = [
    path('items/', views.AuctionItemListAPIView.as_view(),
         name='list_auction_item'),
    path('items/create/', views.AuctionItemCreateUpdateDeleteAPIView.as_view(),
         name="create_auction_item"),
    path('items/<uuid:item_id>/', views.AuctionItemDetailAPIView.as_view(),
         name='auction_item_detail'),
    path('items/<uuid:item_id>/', views.AuctionItemCreateUpdateDeleteAPIView.as_view(),
         name='update_delete_auction_item'),
    path('items/images/<uuid:auction_id>/',
         views.AuctionItemImagesAPIView.as_view(), name='list_create_delete_auction_item_images'),
]
