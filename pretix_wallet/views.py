from django.views.generic import ListView
from pretix.base.models import GiftCardTransaction, Item
from pretix.presale.utils import _detect_event
from pretix.presale.views.customer import CustomerRequiredMixin
from rest_framework.mixins import RetrieveModelMixin, CreateModelMixin
from rest_framework.response import Response
from rest_framework.status import HTTP_201_CREATED
from rest_framework.viewsets import ReadOnlyModelViewSet, GenericViewSet

from pretix_wallet.models import CustomerWallet
from pretix_wallet.pagination import CustomPagination, TerminalMetadataPagination
from pretix_wallet.serializers import ProductSerializer, WalletSerializer, TransactionSerializer


class TransactionListView(CustomerRequiredMixin, ListView):
    model = GiftCardTransaction
    template_name = "pretix_wallet/transaction_list.html"

    def get_queryset(self):
        return self.request.customer.wallet.giftcard.transactions.order_by("-datetime")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['wallet'] = self.request.customer.wallet
        return ctx


class ProductViewSet(ReadOnlyModelViewSet):
    serializer_class = ProductSerializer
    pagination_class = TerminalMetadataPagination

    def get_queryset(self):
        return Item.objects.all()


class WalletViewSet(RetrieveModelMixin, GenericViewSet):
    serializer_class = WalletSerializer
    pagination_class = CustomPagination
    lookup_url_kwarg = 'token_id'

    def get_queryset(self):
        return CustomerWallet.objects.all()

    def get_object(self):
        return CustomerWallet.objects.get(giftcard__linked_media__identifier=self.kwargs['token_id'])


class TransactionViewSet(CreateModelMixin, GenericViewSet):
    serializer_class = TransactionSerializer

    def get_serializer_context(self):
        _detect_event(self.request)
        context = super().get_serializer_context()
        self.wallet = CustomerWallet.objects.get(giftcard__linked_media__identifier=self.kwargs['token_id'])
        context['wallet'] = self.wallet
        context['event'] = self.request.event
        return context

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(WalletSerializer(self.wallet).data, status=HTTP_201_CREATED)
