from typing import Protocol

from django.utils import timezone
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from .models import Auction, AuctionItem, AuctionItemImage, Bid
from accounts.serializers import UserSerializer


class Archivable(Protocol):
    is_archived: bool
    is_deleted: bool


class ArchiveProtectionMixin:
    def validate(self, attrs):
        instance: Archivable = self.instance  # type:ignore
        if instance and (instance.is_archived or instance.is_deleted):
            raise ValueError("Cannot modify an archived or deleted item")
        return super().validate(attrs)  # type:ignore


class AuctionItemImageSerializer(ArchiveProtectionMixin, serializers.ModelSerializer):
    url = serializers.SerializerMethodField()
    creator = UserSerializer()
    class Meta:
        model = AuctionItemImage
        fields = ['id', 'url']
        read_only_fields = ['id', 'creator',  'created_at', 'updated_at']

    def get_url(self, obj):
        request = self.context.get('request')
        if obj.image and request:
            return request.build_absolute_uri(obj.image.url)
        return None


class AuctionItemSerializer(ArchiveProtectionMixin, serializers.ModelSerializer):
    images = AuctionItemImageSerializer(many=True, )
    creator = UserSerializer()

    class Meta:
        model = AuctionItem
        fields = '__all__'
        read_only_fields = ['id', 'creator',  'created_at', 'updated_at']

    def update(self, instance, validated_data):
        if self.instance.auction_start_date <= timezone.now(): #type:ignore
            raise ValidationError("Cannot change auction details after auction has started")
        return super().update(instance, validated_data)



class AuctionSerializer(serializers.ModelSerializer):
    item_for_sale = AuctionItemSerializer(read_only = True)

    class Meta:
        model = Auction 
        fields = '__all__'


class BidSerializer(serializers.ModelSerializer):
    pass
