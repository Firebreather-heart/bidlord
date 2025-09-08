from rest_framework import status
from rest_framework.response import Response


class CustomResponse:

    @staticmethod
    def success(data=None, message="Success", status=200):
        """Return 200 OK or another specified code"""
        response_data = {"message": message}
        if data is not None:
            response_data["data"] = data
        return Response(response_data, status=status.HTTP_200_OK)

    @staticmethod
    def created(data=None, message="Created successfully"):
        """Returns 201 Created"""
        response_data = {"message": message}
        if data is not None:
            response_data["data"] = data
        return Response(response_data, status=status.HTTP_201_CREATED)

    @staticmethod
    def no_content():
        """Returns 204 No Content"""
        return Response(status=status.HTTP_204_NO_CONTENT)

    @staticmethod
    def bad_request(message="Bad request", errors=None):
        """Returns 400 Bad Request"""
        response_data = {"message": message}
        if errors:
            response_data["errors"] = errors
        return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

    @staticmethod
    def unauthorized(message="Unauthorized access"):
        """Returns 401 Unauthorized"""
        return Response({"message": message}, status=status.HTTP_401_UNAUTHORIZED)

    @staticmethod
    def forbidden(message="Access forbidden"):
        """Returns 403 Forbidden"""
        return Response({"message": message}, status=status.HTTP_403_FORBIDDEN)

    @staticmethod
    def not_found(message="Resource not found"):
        """Returns 404 Not Found"""
        return Response({"message": message}, status=status.HTTP_404_NOT_FOUND)

    @staticmethod
    def conflict(message="Conflict occurred"):
        """Returns 409 Conflict"""
        return Response({"message": message}, status=status.HTTP_409_CONFLICT)

    @staticmethod
    def internal_server_error(message="Internal server error"):
        """Returns 500 Internal Server Error"""
        return Response({"message": message}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
