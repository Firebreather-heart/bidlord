from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, OpenApiExample, OpenApiRequest, extend_schema
from drf_spectacular.types import OpenApiTypes
from rest_framework import status
from .serializers import (
    AuctionItemImageCreateSerializer,
    AuctionItemSerializer,
    AuctionItemImageSerializer,
    AuctionItemUpdateSerializer,
    AuctionItemSearchSerializer
)


def auction_item_create_doc():
    return extend_schema(
        operation_id="create_auction_item",
        summary="Create auction item",
        description="Create a new auction item with images. Supports multipart form data for file uploads.",
        request={
            'multipart/form-data': {
                'type': 'object',
                'properties': {
                    'item_name': {'type': 'string', 'example': 'Vintage Rolex Watch'},
                    'details': {'type': 'string', 'example': 'Beautiful 1960s Submariner in excellent condition'},
                        'initial_price': {'type': 'number', 'example': 5000.00},
                        'price_currency': {'type': 'string', 'enum': ['Dollars', 'Pounds', 'Naira', 'Euro']},
                        'auction_start_date': {'type': 'string', 'format': 'date-time'},
                        'auction_end_date': {'type': 'string', 'format': 'date-time'},
                        'images': {
                            'type': 'array',
                            'items': {'type': 'string', 'format': 'binary'},
                            'description': 'Upload up to 10 images (5MB each)'
                    }
                },
                'required': ['item_name', 'details', 'initial_price', 'auction_start_date', 'auction_end_date']
            }
        },
        responses={
            201: OpenApiResponse(
                response=AuctionItemSerializer,
                description="Auction item created successfully"
            ),
            400: OpenApiResponse(
                description="Validation error",
                examples=[
                    OpenApiExample(
                        'Validation error',
                        value={
                            "success": False,
                            "message": "Validation failed",
                            "errors": {
                                "item_name": ["This field is required."],
                                "initial_price": ["Ensure this value is greater than 0."],
                                "images": ["Maximum 10 images allowed"]
                            }
                        }
                    )
                ]
            ),
            401: OpenApiResponse(description="Authentication required")
        },
        tags=['Auctions']
    )


def auction_item_detail_doc():
    return extend_schema(
        operation_id="get_auction_item_detail",
        summary="Get auction item details",
        description="Retrieve detailed information about a specific auction item including images and bid history.",
        responses={
            200: AuctionItemSerializer,
            404: OpenApiResponse(description="Auction item not found")
        },
        tags=['Auctions']
    )


def auction_item_list_doc():
    return extend_schema(
        operation_id="list_auction_items",
        summary="List auction items",
        description="Get a list of all auction items",
        responses={
            200: OpenApiResponse(
                response=AuctionItemSerializer(many=True),
                description="Successfully retrieved auction items",
                examples=[
                    OpenApiExample(
                        'Success response',
                        value={
                            "success": True,
                            "message": "Success",
                            "pagination": {
                                "count": 150,
                                "next": "http://localhost:8000/api/auction-items/?page=2",
                                "previous": None,
                                "page_size": 20,
                                "total_pages": 8,
                                "current_page": 1
                            },
                            "data": [
                                {
                                    "id": "123e4567-e89b-12d3-a456-426614174000",
                                    "item_name": "Vintage Rolex Watch",
                                    "details": "Rare 1960s Submariner",
                                    "initial_price": "5000.00",
                                    "price_currency": "Dollars",
                                    "auction_start_date": "2024-01-01T10:00:00Z",
                                    "auction_end_date": "2024-01-08T10:00:00Z",
                                    "images": [],
                                    "creator": {
                                        "id": "456as-dhfy6-dbfj9",
                                        "username": "collector123"
                                    }
                                }
                            ]
                        }
                    )
                ]
            )
        },
        tags=['Auctions']
    )


def auction_item_edit_doc():
    return extend_schema(
        operation_id="edit_auction_item",
        summary="edit the details of an auction item",
        description="This endpoint allows you to change the details of an auction item",
        request=AuctionItemUpdateSerializer,
        responses={
            200: OpenApiResponse(
                response=AuctionItemUpdateSerializer,
                description="Auction item edited successfully"
            ),
            400: OpenApiResponse(
                description="Validation error",
                examples=[
                    OpenApiExample(
                        'Validation error',
                        value={
                            "success": False,
                            "message": "Validation failed",
                            "errors": {
                                "item_name": ["This field is required."],
                                "initial_price": ["Ensure this value is greater than 0."],
                            }
                        }
                    )
                ]
            ),
            401: OpenApiResponse(description="Authentication required")
        },
        tags=['Auctions']
    )


def auction_item_delete_doc():
    return extend_schema(
        operation_id="delete_auction_item",
        summary="Delete an auction item",
        description="This endpoint allows you to delete an auction item along with any related data",
        parameters=[OpenApiParameter(
            name='item_id', type=OpenApiTypes.UUID, description="item id"
        )],
        responses={
            204: OpenApiResponse(
                description="No Content, item deleted successfully"
            ),
            401: OpenApiResponse(description="Unauthenticated"),
            403: OpenApiResponse(description="You can't delete an item you didn't create")
        },
        tags=['Auctions']
    )


def auction_item_image_list_doc():
    return extend_schema(
        operation_id="list_auction_item_images",
        summary="Get a list of the images associated with the specified auction ",
        parameters=[
            OpenApiParameter(
                name="auction_id",
                location=OpenApiParameter.PATH,
                required=True
            ),
        ],
        responses={
            200: OpenApiResponse(
                response=AuctionItemImageSerializer
            ),
            404: OpenApiResponse(
                description="Auction item not found"
            )
        },
        tags=['Auctions']
    )


def auction_item_image_create_doc():
    return extend_schema(
        operation_id="add_auction_item_image",
        summary="Add an image to an auction item, the only ways to manage the images are to add or delete them",
        parameters=[
            OpenApiParameter(
                name="auction_id",
                location=OpenApiParameter.PATH,
                required=True
            ),
        ],
        request=AuctionItemImageCreateSerializer,
        responses={
            201: OpenApiResponse(
                response=AuctionItemImageSerializer,
                description=" created successfully"
            ),
            400: OpenApiResponse(
                description="Validation Error"
            ),
            401: OpenApiResponse(
                description='Authentication required'
            ),
            404: OpenApiResponse(
                description="Auction item not found"
            )
        },
        tags=['Auctions']
    )


def auction_item_image_delete_doc():
    return extend_schema(
        operation_id="delete_auction_item_image",
        summary="Delete an image(s) associated with the specified auction item",
        parameters=[
            OpenApiParameter(
                name="auction_id",
                location=OpenApiParameter.PATH,
                required=True
            ),
        ],
        request=OpenApiRequest(
            {
                "images": [OpenApiTypes.STR]
            }
        ),
        responses={
            200: OpenApiResponse(
                description=" Deleted <no of images> images"
            ),
            400: OpenApiResponse(
                description="Validation Error"
            ),
            401: OpenApiResponse(
                description='Authentication required'
            ),
            404: OpenApiResponse(
                description="Auction item not found"
            )
        },
        tags=['Auctions']
    )


def auction_list_and_detail_doc():
    return extend_schema(
        operation_id="list_or_get_auctions",
        summary="List or get live/closed auctions",
        description="Retrieve a list of auctions or a single auction. Use query parameters to filter results.",
        parameters=[
            OpenApiParameter(
                name='live', type=OpenApiTypes.BOOL,
                description="Set to 'true' for live auctions (default), 'false' for closed auctions.",
                required=False, location=OpenApiParameter.QUERY
            ),
            OpenApiParameter(
                name='auction_id', type=OpenApiTypes.UUID,
                description="Provide an ID to fetch a single auction.",
                required=False, location=OpenApiParameter.QUERY
            ),
        ],
        responses={
            200: OpenApiResponse(description="Successfully retrieved auction(s)."),
            404: OpenApiResponse(description="Auction not found.")
        },
        tags=['Auctions']
    )


def place_bid_doc():
    return extend_schema(
        operation_id="place_bid_on_auction",
        summary="Place a bid on an auction",
        description="Submits a bid for an active auction. The request is queued and processed asynchronously.",
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'amount': {'type': 'number', 'example': 6500.50}
                },
                'required': ['amount']
            }
        },
        responses={
            202: OpenApiResponse(description="Bid received and is being processed."),
            400: OpenApiResponse(description="Invalid bid amount."),
            401: OpenApiResponse(description="Authentication required."),
            404: OpenApiResponse(description="Auction not found or not active.")
        },
        tags=['Bids']
    )


def master_search_doc():
    return extend_schema(
        operation_id="master_search",
        summary="Search for auction items",
        description="Performs a full-text search across item names and descriptions.",
        parameters=[
            OpenApiParameter(
                name='q',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='The search term.',
                required=True,
            ),
        ],
        responses={200: AuctionItemSearchSerializer(many=True)},
        tags=['Search']
    )


__all__ = ['auction_item_create_doc', 'auction_item_detail_doc',
           'auction_item_list_doc', 'auction_item_edit_doc', 'auction_item_delete_doc', 'auction_item_image_create_doc', 'auction_item_image_list_doc', 'auction_item_image_delete_doc',
           'auction_list_and_detail_doc', 'place_bid_doc','master_search_doc'
           ]
