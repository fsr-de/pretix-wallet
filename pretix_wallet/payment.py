from _decimal import Decimal
from typing import Dict, Any, Union
from urllib.parse import quote

from django.http import HttpRequest
from django.utils.crypto import get_random_string
from django.utils.translation import gettext_lazy as _
from django_scopes import scope
from pretix.base.customersso.oidc import oidc_authorize_url
from pretix.base.models import Order, OrderPayment, GiftCard
from pretix.base.models.customers import CustomerSSOClient, CustomerSSOProvider
from pretix.base.payment import BasePaymentProvider, PaymentException, GiftCardPayment
from pretix.base.services.cart import add_payment_to_cart
from pretix.multidomain.urlreverse import build_absolute_uri
from pretix.presale.views.cart import cart_session
from pretix.presale.views.customer import SSOLoginView


class WalletPaymentProvider(GiftCardPayment):
    identifier = "wallet"
    verbose_name = _("Wallet")
    public_name = _("Wallet")
    execute_payment_needs_user = True
    multi_use_supported = False

    def payment_form_render(self, request: HttpRequest, total: Decimal, order: Order=None) -> str:
        return "Wallet payment form"

    def checkout_confirm_render(self, request, order: Order=None, info_data: dict=None) -> str:
        return "Wallet confirm"

    def checkout_prepare(self, request: HttpRequest, cart: Dict[str, Any]) -> Union[bool, str]:
        if request.customer:
            if not request.customer.wallet:
                raise PaymentException(_("You do not have a wallet."))
            return True
        next_url = build_absolute_uri(request.event, "presale:event.checkout", kwargs={"step": "confirm"})
        provider = CustomerSSOProvider.objects.last()

        # taken from pretix.presale.views.customer.SSOLoginView as it does not allow for a custom next_url
        nonce = get_random_string(32)
        request.session[f'pretix_customerauth_{provider.pk}_nonce'] = nonce
        request.session[f'pretix_customerauth_{provider.pk}_popup_origin'] = None
        request.session[f'pretix_customerauth_{provider.pk}_cross_domain_requested'] = request.GET.get(
            "request_cross_domain_customer_auth") == "true"
        redirect_uri = build_absolute_uri(request.organizer, 'presale:organizer.customer.login.return', kwargs={
            'provider': provider.pk
        })

        return oidc_authorize_url(provider, f'{nonce}%{next_url}', redirect_uri)

    def payment_is_valid_session(self, request: HttpRequest) -> bool:
        return request.customer is not None

    def _set_payment_info_data(self, request: HttpRequest, payment: OrderPayment, gc: GiftCard):
        payment.info_data = {
            'gift_card': gc.pk,
            'gift_card_secret': gc.secret,
            'user': request.customer.name_cached,
            'user_id': request.customer.external_identifier,
            'retry': True
        }
        payment.save()

    def execute_payment(self, request: HttpRequest, payment: OrderPayment, is_early_special_case=False) -> str:
        gc = request.customer.wallet.giftcard
        if gc not in self.event.organizer.accepted_gift_cards:
            raise PaymentException(_("Wallet payments cannot be accepted for this event."))
        if gc.value < payment.amount:
            raise PaymentException(_("Your wallet does not have enough credit to pay for this order."))
        self._set_payment_info_data(request, payment, gc)
        return super().execute_payment(request, payment, is_early_special_case)

    def payment_prepare(self, request: HttpRequest, payment: OrderPayment) -> Union[bool, str, None]:
        gc = request.customer.wallet.giftcard
        if gc not in self.event.organizer.accepted_gift_cards:
            raise PaymentException(_("Wallet payments cannot be accepted for this event."))
        if gc.value < payment.amount:
            raise PaymentException(_("Your wallet does not have enough credit to pay for this order."))
        self._set_payment_info_data(request, payment, gc)
        return True
