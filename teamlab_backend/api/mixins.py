from rest_framework.response import Response


class PaginatedActionMixin:
    def get_paginated_action_response(
        self,
        queryset,
        serializer_class=None,
    ):
        page = self.paginate_queryset(queryset)
        objects = page if page is not None else queryset

        if serializer_class is None:
            serializer = self.get_serializer(objects, many=True)
        else:
            serializer = serializer_class(
                objects,
                many=True,
                context=self.get_serializer_context(),
            )

        if page is not None:
            return self.get_paginated_response(serializer.data)

        return Response(serializer.data)
