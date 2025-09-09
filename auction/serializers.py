from django.utils import timezone
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field

from .mixins import ArchiveProtectionMixin

from .models import Auction, AuctionItem, AuctionItemImage, Bid
from accounts.serializers import UserSerializer


class AuctionItemImageCreateSerializer(serializers.Serializer):
    images = serializers.ListField(
        child=serializers.ImageField(max_length=5*1024*1024),
        write_only=True,
        required=False,
        allow_empty=True,
        max_length=10,
        help_text="Upload up to 10 Images (5mb each) in total, considering any previously uploaded images"
    )


class AuctionItemImageSerializer(ArchiveProtectionMixin, serializers.ModelSerializer):
    url = serializers.SerializerMethodField()
    creator = UserSerializer()

    class Meta:
        model = AuctionItemImage
        fields = ['id', 'url', 'creator',]
        read_only_fields = ['id', 'creator',]

    @extend_schema_field(OpenApiTypes.URI)
    def get_url(self, obj) -> str | None:
        request = self.context.get('request')
        if obj.image and request:
            return request.build_absolute_uri(obj.image.url)
        return None


class AuctionItemCreateSerializer(serializers.ModelSerializer):
    images = serializers.ListField(
        child=serializers.ImageField(max_length=5*1024*1024),
        write_only=True,
        required=False,
        allow_empty=True,
        max_length=10,
        help_text="Upload up to 10 Images (5mb each)"
    )

    class Meta:
        model = AuctionItem
        fields = [
            'item_name', 'details', 'initial_price', 'price_currency',
            'auction_start_date', 'auction_end_date', 'images'
        ]
        extra_kwargs = {
            'item_name': {'help_text': 'Name of the auction item'},
            'details': {'help_text': 'Detailed description of the item'},
            'price_currency': {'help_text': 'Dollars | Pounds | Naira | Euro'},
            'initial_price': {'help_text': 'Starting bid price'},
            'auction_start_date': {'help_text': 'When the auction starts (ISO format)'},
            'auction_end_date': {'help_text': 'When the auction ends, at least 30 mins after (ISO format)'},
        }

    def _validate_images(self, images: list):
        if len(images) > 10:
            raise ValidationError("Maximum allowed images is 10")

        total_size = sum(img.size for img in images)
        if total_size > (50 * 1024 * 1024):
            raise ValidationError("Total image upload size cannot exceed 50mb")

        return images

    def _validate_auction_end_date(self, value):
        start_date = self.initial_data.get('auction_start_date')  # type:ignore
        if start_date:
            from dateutil import parser
            start_datetime = parser.parse(start_date) if isinstance(
                start_date, str) else start_date
            interval = value - start_datetime
            if (value <= start_datetime) or (interval.seconds < 1800):
                raise ValidationError(
                    "End date-time must be set at least 30 mins after start")
            return value

    def _validate_initial_price(self, value):
        if value <= 0:
            raise ValidationError("Initial price must be greater than zero")
        return value

    def validate(self, attrs):
        if attrs.get('images'):
            attrs['images'] = self._validate_images(attrs['images'])
        if attrs.get('auction_end_date'):
            attrs['auction_end_date'] = self._validate_auction_end_date(
                attrs['auction_end_date'])
        if attrs.get('initial_price'):
            attrs['initial_price'] = self._validate_initial_price(
                attrs['initial_price'])
        return super().validate(attrs)

    def create(self, validated_data):
        images_data = validated_data.pop('images', [])

        auction_item = AuctionItem.objects.create(**validated_data)

        for file in images_data:
            image = AuctionItemImage.objects.create(
                image=file, creator=self.context['request'].user)
            auction_item.images.add(image)

        return auction_item


class AuctionItemSerializer(ArchiveProtectionMixin, serializers.ModelSerializer):
    images = AuctionItemImageSerializer(many=True, )
    creator = UserSerializer()

    class Meta:
        model = AuctionItem
        fields = '__all__'
        read_only_fields = ['id', 'creator',  'created_at', 'updated_at']

    def update(self, instance, validated_data):
        if self.instance.auction_start_date <= timezone.now():  # type:ignore
            raise ValidationError(
                "Cannot change auction details after auction has started")
        return super().update(instance, validated_data)


class AuctionItemUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuctionItem
        fields = [
            'item_name', 'details', 'initial_price', 'price_currency',
            'auction_start_date', 'auction_end_date'
        ]
        extra_kwargs = {
            'item_name': {'help_text': 'Name of the auction item'},
            'details': {'help_text': 'Detailed description of the item'},
            'price_currency': {'help_text': 'Dollars | Pounds | Naira | Euro'},
            'initial_price': {'help_text': 'Starting bid price'},
            'auction_start_date': {'help_text': 'When the auction starts (ISO format)'},
            'auction_end_date': {'help_text': 'When the auction ends, at least 30 mins after (ISO format)'},
        }

    def _validate_auction_end_date(self, value):
        start_date = self.initial_data.get('auction_start_date')  # type:ignore
        if start_date:
            from dateutil import parser
            start_datetime = parser.parse(start_date) if isinstance(
                start_date, str) else start_date
            interval = value - start_datetime
            if (value <= start_datetime) or (interval.seconds < 1800):
                raise ValidationError(
                    "End date-time must be set at least 30 mins after start")
            return value

    def _validate_initial_price(self, value):
        if value <= 0:
            raise ValidationError("Initial price must be greater than zero")
        return value

    def validate(self, attrs):
        if attrs.get('auction_end_date'):
            attrs['auction_end_date'] = self._validate_auction_end_date(
                attrs['auction_end_date'])
        if attrs.get('initial_price'):
            attrs['initial_price'] = self._validate_initial_price(
                attrs['initial_price'])
        return super().validate(attrs)


class BidSerializer(serializers.ModelSerializer):
    creator = UserSerializer()

    class Meta:
        model = Bid
        fields = '__all__'


class AuctionSerializer(serializers.ModelSerializer):
    item_for_sale = AuctionItemSerializer(read_only=True)
    bids = BidSerializer(many=True, read_only=True)

    class Meta:
        model = Auction
        fields = ['id', 'item_for_sale', 'current_price', 'ongoing', 'bids']
        read_only_fields = '__all__'


class AuctionListSerializer(serializers.ModelSerializer):
    item_for_sale = AuctionItemSerializer(read_only=True)
    bid_count = serializers.SerializerMethodField()

    class Meta:
        model = Auction
        fields = ['id', 'item_for_sale',
                  'current_price', 'ongoing', 'bid_count']
        read_only_fields = '__all__'

    def get_bid_count(self, obj):
        return obj.bids.count()


class ClosedAuctionSerializer(serializers.ModelSerializer):
    item_for_sale = AuctionItemSerializer(read_only=True)

    class Meta:
        model = Auction
        fields = ['item_for_sale', 'current_price', 'winner']
        read_only_fields = '__all__'


class ClosedAuctionListSerializer(serializers.ModelSerializer):

    class Meta:
        model = Auction
        fields = ['item_for_sale', 'current_price', 'winner']
        read_only_fields = '__all__'
