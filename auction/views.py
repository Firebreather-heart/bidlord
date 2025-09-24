import logging

from django.db import transaction
from django.db.models import Prefetch, Sum, F
from django.shortcuts import get_object_or_404
from django.contrib.postgres.search import SearchQuery, SearchRank

from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.throttling import UserRateThrottle, AnonRateThrottle
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.exceptions import ValidationError


from utils.responses import CustomResponse
from utils.permissions import IsCreatorOrReadOnly
from utils.paginators import PaginationMixin


from .docs import *

from .models import (
    Auction,
    AuctionItem,
    AuctionItemImage,
    Bid
)

from .serializers import (
    AuctionItemImageCreateSerializer,
    AuctionItemImageSerializer,
    AuctionItemCreateSerializer,
    AuctionSerializer,
    ClosedAuctionSerializer,
    AuctionItemSerializer,
    AuctionItemSearchSerializer,
    AuctionItemCreateSerializer,
    BidSerializer,
    AuctionItemUpdateSerializer,
    ClosedAuctionListSerializer,
    AuctionListSerializer,
)

from .tasks import process_bid

logger = logging.getLogger('auction')

# Create your views here.


class AuctionItemListAPIView(PaginationMixin, APIView):
    permission_classes = [AllowAny]
    throttle_classes = [AnonRateThrottle, UserRateThrottle]

    @auction_item_list_doc()
    def get(self, request, *args, **kwargs):
        auction_items = AuctionItem.available_items.all().select_related('creator').prefetch_related(
            Prefetch('images', queryset=AuctionItemImage.available_images.all())
        ).order_by('-created_at')
        page, paginator = self.paginate_queryset(
            auction_items, request)
        if page is not None:
            auction_item_serializer = AuctionItemSerializer(page, many=True)
            paginated_data = self.get_paginated_response(
                data=auction_item_serializer.data,
                paginator=paginator
            )
            return CustomResponse.success(
                data=paginated_data
            )
        auction_item_serializer = AuctionItemSerializer(
            auction_items, many=True)
        return CustomResponse.success(
            data=auction_item_serializer.data[:10],
        )


class MasterSearchAPIView(PaginationMixin, APIView):
    permission_classes = [AllowAny]
    throttle_classes = [AnonRateThrottle, UserRateThrottle]

    @master_search_doc()
    def get(self, request, *args, **kwargs):
        query_param = request.query_params.get('q', None)

        if not query_param:
            return CustomResponse.bad_request("Search query parameter 'q' is required.")

        search_query = SearchQuery(
            query_param, search_type='websearch', config='english')

        search_results = AuctionItem.available_items.filter(
            search_vector=search_query
        ).annotate(
            rank=SearchRank(F('search_vector'), search_query),
        ).order_by('-rank', '-created_at')

        page, paginator = self.paginate_queryset(search_results, request)
        if page is not None:
            serializer = AuctionItemSearchSerializer(
                page, many=True, context={'request': request})
            paginated_data = self.get_paginated_response(
                data=serializer.data,
                paginator=paginator
            )
            return CustomResponse.success(data=paginated_data)

        serializer = AuctionItemSearchSerializer(
            search_results, many=True, context={'request': request})
        return CustomResponse.success(data=serializer.data)


class AuctionItemDetailAPIView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [AnonRateThrottle, UserRateThrottle]

    @auction_item_detail_doc()
    def get(self, request, item_id):
        try:
            item_instance = AuctionItem.available_items.select_related('creator').prefetch_related(
                'images').get(id=item_id)
        except AuctionItem.DoesNotExist:
            return CustomResponse.not_found()
        else:
            item_serializer = AuctionItemSerializer(item_instance)
            return CustomResponse.success(
                data=item_serializer.data,
            )


class AuctionItemCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [AnonRateThrottle, UserRateThrottle]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    @auction_item_create_doc()
    def post(self, request):
        serializer = AuctionItemCreateSerializer(data=request.data)
        if serializer.is_valid():
            with transaction.atomic():
                auction_item = serializer.save(creator=request.user)
                logger.info(
                    f'{request.user} added auction item {auction_item}')
            return CustomResponse.created(data=AuctionItemSerializer(auction_item).data)
        else:
            return CustomResponse.bad_request(errors=serializer.errors)


class AuctionItemUpdateDeleteAPIView(APIView):
    permission_classes = [IsAuthenticated, IsCreatorOrReadOnly]
    throttle_classes = [AnonRateThrottle, UserRateThrottle]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    @auction_item_edit_doc()
    def put(self, request, item_id):
        item_instance = get_object_or_404(AuctionItem, id=item_id)
        item_serializer = AuctionItemUpdateSerializer(
            item_instance, data=request.data, partial=True)
        if item_serializer.is_valid():
            item_serializer.save()
            return CustomResponse.success(
                data=item_serializer.data,
                message="Auction item updated successfully."
            )
        return CustomResponse.bad_request(
            errors=item_serializer.errors,
            message="Failed to update auction item."
        )

    @auction_item_delete_doc()
    def delete(self, request, item_id):
        item_instance = get_object_or_404(AuctionItem, id=item_id)
        if timezone.now() < item_instance.auction_end_date and timezone.now() > item_instance.auction_start_date:
            return CustomResponse.bad_request("Cannot delete an ongoing auction")
        with transaction.atomic():
            item_instance.delete()
            for item in item_instance.images.all():
                item.delete()
        return CustomResponse.no_content()


class AuctionItemImagesAPIView(APIView):
    """This endpoint allows a user to manage the images of an item by adding and deleting"""
    permission_classes = [IsAuthenticated, IsCreatorOrReadOnly]
    throttle_classes = [AnonRateThrottle, UserRateThrottle]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def validate_images(self, images: list, prev_image_count: int, prev_image_size: int):
        """Call this method before uploading any images"""
        if len(images) + prev_image_count > 10:
            raise ValidationError("Maximum allowed images is 10")

        total_size = sum(img.size for img in images) + prev_image_size
        if total_size > (50 * 1024 * 1024):
            raise ValidationError("Total image upload size cannot exceed 50mb")
        return images

    @auction_item_image_list_doc()
    def get(self, request, auction_id):
        auction_item = get_object_or_404(AuctionItem, id=auction_id)
        images = auction_item.images.all()
        return CustomResponse.success(
            data=AuctionItemImageSerializer(images, many=True).data
        )

    @auction_item_image_create_doc()
    def post(self, request, auction_id):
        try:
            images = request.FILES.getlist('images')
            auction_item: AuctionItem = AuctionItem.available_items.get(
                id=auction_id)
            prev_image_count = auction_item.images.count()
            prev_image_size = auction_item.images.aggregate(Sum('size'))[
                'size___sum'] or 0
            self.validate_images(images, prev_image_count, prev_image_size)
        except AuctionItem.DoesNotExist:
            return CustomResponse.not_found(f"Auction with id {auction_id} not found")
        except ValidationError as verror:
            logger.error(f"Error adding images: {verror}")
            return CustomResponse.bad_request(errors=verror)
        else:
            created_images = []
            with transaction.atomic():
                for image_file in images:
                    image = AuctionItemImage.objects.create(
                        image=image_file,
                        creator=request.user
                    )
                    auction_item.images.add(image)
                    created_images.append(image)

            serializer = AuctionItemImageSerializer(created_images, many=True)
            logger.info(
                f"{request.user} added {len(images)} to the auction item {auction_item}")
            return CustomResponse.created(
                data=serializer.data
            )

    @auction_item_image_delete_doc()
    def delete(self, request, auction_id):
        try:
            image_list = request.data.get('images')
            auction_item: AuctionItem = AuctionItem.available_items.get(
                id=auction_id)
            no_of_items_deleted, _ = auction_item.images.filter(
                id__in=image_list).delete()
            return CustomResponse.success(
                message=f"deleted {no_of_items_deleted} images"
            )
        except AuctionItem.DoesNotExist:
            return CustomResponse.not_found(
                f"Auction with id {auction_id} not found"
            )
        except Exception as e:
            logger.error(
                f"An error occured when trying to delete images: {e}"
            )
            return CustomResponse.internal_server_error("An unexpected error has occurred")


class AuctionAPIView(PaginationMixin, APIView):
    """This endpoint provides you a view of current and past auctions"""
    permission_classes = [AllowAny]
    throttle_classes = [AnonRateThrottle]

    @auction_list_and_detail_doc()
    def get(self, request,):
        live = request.GET.get('live', 'true').lower(
        ) == 'true'  # defaults to `true`
        auction_id = request.GET.get('auction_id')
        if auction_id and live:
            auction = get_object_or_404(Auction, id=auction_id)
            serializer = AuctionSerializer(auction)
            return CustomResponse.success(
                serializer.data
            )
        elif auction_id and not live:
            auction = get_object_or_404(Auction, id=auction_id)
            serializer = ClosedAuctionSerializer(auction)
            return CustomResponse.success(
                serializer.data
            )
        elif not auction_id and live:
            auctions = Auction.active_auctions.all()
            page, paginator = self.paginate_queryset(
                auctions, request
            )
            if page is not None:
                auctions_serializer = AuctionListSerializer(page, many=True)
                paginated_data = self.get_paginated_response(
                    data=auctions_serializer.data,
                    paginator=paginator
                )
                return CustomResponse.success(
                    paginated_data
                )
            return CustomResponse.success(
                AuctionListSerializer(auctions[:10], many=True).data
            )
        elif not auction_id and not live:
            auctions = Auction.objects.filter(
                ongoing=False).order_by('-created_at')
            page, paginator = self.paginate_queryset(
                auctions, request
            )
            if page is not None:
                auctions_serializer = ClosedAuctionListSerializer(
                    page, many=True)
                paginated_data = self.get_paginated_response(
                    data=auctions_serializer.data,
                    paginator=paginator
                )
                return CustomResponse.success(
                    paginated_data
                )
            return CustomResponse.success(
                ClosedAuctionListSerializer(auctions[:10], many=True).data
            )
        return CustomResponse.bad_request()


class PlaceBidAPIView(APIView):
    """
    Accepts a bid from an authenticated user and queues it for processing
    """
    permission_classes = [IsAuthenticated]
    throttle_classes = [UserRateThrottle]

    @place_bid_doc()
    def post(self, request, auction_id):
        try:
            amount = request.data.get('amount')
            if not isinstance(amount, (int, float)) or amount <= 0:
                return CustomResponse.bad_request("A valid bid amount is required")

            process_bid.delay(
                user_id=str(request.user.id),
                auction_id=str(auction_id),
                amount=float(amount)
            )  # type: ignore
            return CustomResponse.success(
                message="Your bid has been received and is being processed",
                status_code=202
            )
        except Exception as e:
            logger.error(
                f'Error queueing bid for auction {auction_id}: {e}', exc_info=True)
            return CustomResponse.internal_server_error("An error occured while placing your bid")
