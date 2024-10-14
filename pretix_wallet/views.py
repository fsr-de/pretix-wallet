from django.contrib import messages
from django.http import Http404
from django.shortcuts import redirect
from django.utils.translation import gettext_lazy as _
from django.views import View
from django.views.generic import ListView, TemplateView
from pretix.base.models import GiftCardTransaction
from pretix.multidomain.urlreverse import build_absolute_uri
from pretix.presale.utils import _detect_event
from pretix.presale.views.customer import CustomerRequiredMixin
from rest_framework.mixins import CreateModelMixin, RetrieveModelMixin
from rest_framework.response import Response
from rest_framework.status import HTTP_201_CREATED
from rest_framework.viewsets import GenericViewSet, ReadOnlyModelViewSet

from pretix_wallet.auth import TerminalAuthentication, TerminalPermission
from pretix_wallet.models import CustomerWallet
from pretix_wallet.pagination import CustomPagination, ProductPagination
from pretix_wallet.serializers import (
    CustomerWalletSerializer,
    ProductSerializer,
    TransactionSerializer,
    WalletSerializer,
)
from pretix_wallet.utils import (
    create_customerwallet_if_not_exists,
    email_address_to_user_slug,
    link_token_to_wallet,
)


class TerminalAuthMixin:
    authentication_classes = [TerminalAuthentication]
    permission_classes = [TerminalPermission]


class WalletRequiredMixin:
    def dispatch(self, request, *args, **kwargs):
        create_customerwallet_if_not_exists(request.organizer, request.customer)
        return super().dispatch(request, *args, **kwargs)


class TransactionListView(CustomerRequiredMixin, WalletRequiredMixin, ListView):
    model = GiftCardTransaction
    template_name = "pretix_wallet/transaction_list.html"

    def get_queryset(self):
        return self.request.customer.wallet.giftcard.transactions.order_by("-datetime")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["wallet"] = self.request.customer.wallet
        ctx["transponder_paired"] = (
            self.request.customer.wallet.giftcard.linked_media.exists()
        )
        ctx["user_slug"] = email_address_to_user_slug(self.request.customer.email)
        return ctx


class PairingView(CustomerRequiredMixin, WalletRequiredMixin, TemplateView):
    template_name = "pretix_wallet/pairing.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["already_paired"] = (
            self.request.customer.wallet.giftcard.linked_media.exists()
        )
        return ctx

    def post(self, request, *args, **kwargs):
        link_token_to_wallet(
            self.request.organizer, self.request.customer, self.kwargs["token_id"]
        )
        messages.success(request, _("Your transponder has been paired succesfully."))
        return redirect(
            build_absolute_uri(
                self.request.organizer, "plugins:pretix_wallet:transactions"
            )
        )


class RemovePairingView(CustomerRequiredMixin, WalletRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        self.request.customer.wallet.giftcard.linked_media.clear()
        messages.success(request, _("Your transponder has been unpaired succesfully."))
        return redirect(
            build_absolute_uri(
                self.request.organizer, "plugins:pretix_wallet:transactions"
            )
        )


class ProductViewSet(TerminalAuthMixin, ReadOnlyModelViewSet):
    serializer_class = ProductSerializer
    pagination_class = ProductPagination

    def get_queryset(self):
        _detect_event(self.request)
        return self.request.event.items.all()


class WalletViewSet(TerminalAuthMixin, RetrieveModelMixin, GenericViewSet):
    serializer_class = WalletSerializer
    pagination_class = CustomPagination
    lookup_url_kwarg = "token_id"

    def get_queryset(self):
        return CustomerWallet.objects.all()

    def get_object(self):
        try:
            return CustomerWallet.objects.get(
                giftcard__linked_media__identifier=self.kwargs["token_id"]
            )
        except CustomerWallet.DoesNotExist:
            raise Http404


class TransactionViewSet(TerminalAuthMixin, CreateModelMixin, GenericViewSet):
    serializer_class = TransactionSerializer

    def get_serializer_context(self):
        _detect_event(self.request)
        context = super().get_serializer_context()
        self.wallet = CustomerWallet.objects.get(
            giftcard__linked_media__identifier=self.kwargs["token_id"]
        )
        context["wallet"] = self.wallet
        context["event"] = self.request.event
        return context

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(WalletSerializer(self.wallet).data, status=HTTP_201_CREATED)


class CustomerCreateWalletViewSet(CreateModelMixin, GenericViewSet):
    serializer_class = CustomerWalletSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["organizer"] = self.request.organizer
        return context
