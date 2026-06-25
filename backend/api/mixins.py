from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response


class AddMixin:
    """Mixin для добавления объектов."""

    def add_instance(self, serializer_class, data, response_data):
        serializer = serializer_class(
            data=data,
            context=self.get_serializer_context()
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(response_data, status=status.HTTP_201_CREATED)


class DeleteMixin:
    """Mixin для удаления объектов."""

    def delete_instance(self, queryset, error_message):
        deleted, _ = queryset.delete()
        if not deleted:
            raise ValidationError(error_message)
        return Response(status=status.HTTP_204_NO_CONTENT)
