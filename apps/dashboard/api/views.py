from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.stores.models.store import Store, StoreStatus

from .permissions import IsSellerOwner
from .serializers import DashboardOverviewSerializer
from ..selectors.overview import DashboardOverviewSelector


class DashboardOverviewAPIView(APIView):
    permission_classes = [IsSellerOwner]

    def get(self, request):
        store = (
            Store.objects
            .filter(
                owner=request.user,
                status=StoreStatus.ACTIVE,
                is_verified=True,
            )
            .first()
        )

        if store is None:
            raise NotFound(
                "No active and verified store was found for this account."
            )

        data = DashboardOverviewSelector.get_overview(
            store=store
        )

        serializer = DashboardOverviewSerializer(data)

        return Response(serializer.data)