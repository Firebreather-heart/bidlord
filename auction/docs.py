from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, OpenApiExample,OpenApiRequest, extend_schema
from drf_spectacular.types import OpenApiTypes
from rest_framework import status
from .serializers import (
    AuctionItemImageCreateSerializer,
    AuctionItemSerializer,
    AuctionItemImageSerializer
)


def auction_item_create_doc():
    return extend_schema(
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
        tags=['Auction Items']
    )


def auction_item_detail_doc():
    return extend_schema(
        summary="Get auction item details",
        description="Retrieve detailed information about a specific auction item including images and bid history.",
        responses={
            200: AuctionItemSerializer,
            404: OpenApiResponse(description="Auction item not found")
        },
        tags=['Auction Items']
    )


def auction_item_list_doc():
    return extend_schema(
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
        tags=['Auction Items']
    )


def auction_item_edit_doc():
    return extend_schema(
        summary="edit the details of an auction item",
        description="This endpoint allows you to change the details of an auction item",
        request=AuctionItemSerializer,
        responses={
            200: OpenApiResponse(
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
        }
    )


def auction_item_delete_doc():
    return extend_schema(
        summary="Delete an auction item",
        description="This endpoint allows you to delete an auction item along with any related data",
        parameters=[OpenApiParameter(
            name='item_id', type=OpenApiTypes.UUID, description="item id"
        )],
        responses={
            204: OpenApiResponse(
                response=status.HTTP_204_NO_CONTENT
            ),
            401: OpenApiResponse(description="Unauthenticated"),
            403: OpenApiResponse(description="You can't delete an item you didn't create")
        }
    )


def auction_item_image_list_doc():
    return extend_schema(
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
        }
    )


def auction_item_image_create_doc():
    return extend_schema(
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
        }
    )


def auction_item_image_delete_doc():
    return extend_schema(
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
            201: OpenApiResponse(
                response=AuctionItemImageSerializer,
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
        }
    )


__all__ = ['auction_item_create_doc', 'auction_item_detail_doc',
           'auction_item_list_doc', 'auction_item_edit_doc', 'auction_item_delete_doc', 'auction_item_image_create_doc', 'auction_item_image_list_doc', 'auction_item_image_delete_doc']
