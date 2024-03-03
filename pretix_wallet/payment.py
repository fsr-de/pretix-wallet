from _decimal import Decimal
from typing import Dict, Any, Union

from django.contrib import messages
from django.db import transaction
from django.http import HttpRequest
from django.utils.crypto import get_random_string
from django.utils.translation import gettext_lazy as _
from pretix.base.customersso.oidc import oidc_authorize_url
from pretix.base.models import Order, OrderPayment, GiftCard
from pretix.base.models.customers import CustomerSSOProvider
from pretix.base.payment import PaymentException, GiftCardPayment
from pretix.base.services.cart import add_payment_to_cart
from pretix.helpers import OF_SELF
from pretix.multidomain.urlreverse import build_absolute_uri
from pretix.presale.views.cart import cart_session

from pretix_wallet.models import CustomerWallet


class WalletPaymentProvider(GiftCardPayment):
    identifier = "wallet"
    verbose_name = _("Wallet")
    public_name = _("Wallet")

    def payment_form_render(self, request: HttpRequest, total: Decimal, order: Order=None) -> str:
        return "Wallet payment form"

    def checkout_confirm_render(self, request, order: Order=None, info_data: dict=None) -> str:
        return "Wallet confirm"

    def checkout_prepare(self, request: HttpRequest, cart: Dict[str, Any]) -> Union[bool, str]:
        if request.customer:
            if not request.customer.wallet:
                messages.error(request, _("You do not have a wallet."))
                return False
            if request.customer.wallet.giftcard.value < 0:
                messages.error(request, _("Your wallet has a negative balance. Please top it up or use another payment method."))
                return False
            cart_session(request)
            add_payment_to_cart(
                request,
                self,
                max_value=request.customer.wallet.giftcard.value,
                info_data=self._get_payment_info_data(request.customer.wallet),
            )
            return True
        return self._redirect_user(request, build_absolute_uri(request.event, "presale:event.checkout", kwargs={"step": "payment"}))

    def _redirect_user(self, request: HttpRequest, next_url: str):
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

    def _get_payment_info_data(self, wallet: CustomerWallet):
        return {
            'gift_card': wallet.giftcard.pk,
            'gift_card_secret': wallet.giftcard.secret,
            'user': wallet.customer.name_cached,
            'user_id': wallet.customer.external_identifier,
            'retry': True
        }

    def execute_payment(self, request: HttpRequest, payment: OrderPayment, is_early_special_case=False) -> str:
        # re-implemented as the original method does not allow for giftcards to have negative balance

        gcpk = payment.info_data.get('gift_card')
        if not gcpk:
            raise PaymentException("Invalid state, should never occur.")
        try:
            with transaction.atomic():
                try:
                    gc = GiftCard.objects.select_for_update(of=OF_SELF).get(pk=gcpk)
                except GiftCard.DoesNotExist:
                    raise PaymentException(_("This gift card does not support this currency."))
                if gc.currency != self.event.currency:  # noqa - just a safeguard
                    raise PaymentException(_("This gift card does not support this currency."))
                if not gc.accepted_by(self.event.organizer):
                    raise PaymentException(_("This gift card is not accepted by this event organizer."))

                trans = gc.transactions.create(
                    value=-1 * payment.amount,
                    order=payment.order,
                    payment=payment,
                    acceptor=self.event.organizer,
                )
                payment.info_data['transaction_id'] = trans.pk
                payment.confirm(send_mail=not is_early_special_case, generate_invoice=not is_early_special_case)
        except PaymentException as e:
            payment.fail(info={'error': str(e)})
            raise e

    def payment_prepare(self, request: HttpRequest, payment: OrderPayment) -> Union[bool, str, None]:
        if request.customer:
            if not request.customer.wallet:
                messages.error(request, _("You do not have a wallet."))
                return False
            if request.customer.wallet.giftcard.value < 0:
                messages.error(request, _("Your wallet has a negative balance. Please top it up or use another payment method."))
                return False
            gc = request.customer.wallet.giftcard
            if gc not in self.event.organizer.accepted_gift_cards:
                raise PaymentException(_("Wallet payments cannot be accepted for this event."))
            payment.amount = min(payment.amount, max(gc.value, 0))
            payment.info_data = self._get_payment_info_data(request.customer.wallet)
            payment.save()
            return True
        return self._redirect_user(request, request.path)
