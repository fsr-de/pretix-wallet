from django.core.exceptions import ImproperlyConfigured
from django.dispatch import receiver
from django.http import Http404
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _

from pretix.base.payment import PaymentException
from pretix.base.signals import register_payment_providers, order_paid
from pretix.helpers.http import redirect_to_url
from pretix.presale.checkoutflow import BaseCheckoutFlowStep, CartMixin, TemplateFlowStep
from pretix.presale.signals import checkout_flow_steps
from pretix.presale.views.cart import cart_session
from pretix_wallet.models import CustomerWallet

from pretix_wallet.payment import WalletPaymentProvider, _wallet_transaction


@receiver(register_payment_providers, dispatch_uid="payment_wallet")
def register_payment_provider(sender, **kwargs):
    return [WalletPaymentProvider]


@receiver(checkout_flow_steps, dispatch_uid="checkout_flow_steps_wallet")
def wallet_checkout_flow_steps(sender, **kwargs):
    return MembershipGrantingCheckoutFlowStep


@receiver(order_paid, dispatch_uid="payment_wallet_order_paid")
def wallet_order_paid(sender, order, **kwargs):
    top_up_positions = list(filter(lambda pos: position_is_top_up_product(sender, pos), order.positions.all()))
    if top_up_positions:
        CustomerWallet.create_if_non_existent(sender.organizer, order.customer)
        try:
            top_up_value = sum(map(lambda pos: pos.price, top_up_positions))
            _wallet_transaction(sender, order.payments.last(), order.customer.wallet.giftcard, sign=1,
                                amount=top_up_value)
        except PaymentException as e:
            raise e


class MembershipGrantingCheckoutFlowStep(CartMixin, BaseCheckoutFlowStep):
    icon = 'user-plus'
    identifier = 'wallet-membership-granting'

    def label(self):
        return _('Creating Wallet')

    @cached_property
    def priority(self):
        # One less than MembershipStep
        return 46

    def get(self, request):
        if request.event.organizer and request.customer:
            CustomerWallet.create_if_non_existent(request.event.organizer, request.customer)
            return redirect_to_url(self.get_next_url(request))
        else:
            raise ImproperlyConfigured('User reached the wallet creation step without signing in.'
                                       'Have you created customer accounts and required membership'
                                       'for the top-up product?')

    def is_completed(self, request, warn=False):
        if self.request.customer.wallet:
            return True
        return False

    def is_applicable(self, request):
        self.request = request
        if not request.event.settings.get("payment_wallet_top_up_products"):
            return False
        return any(map(lambda pos: position_is_top_up_product(request.event, pos), self.positions))


def position_is_top_up_product(event, position):
    if not event.settings.get("payment_wallet_top_up_products"):
        return False
    top_up_products = event.settings.get("payment_wallet_top_up_products").lower().split(',')
    product_name = position.item.name.localize('en').lower()
    return product_name in top_up_products
