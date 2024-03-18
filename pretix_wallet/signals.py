from django.dispatch import receiver

from pretix.base.payment import PaymentException
from pretix.base.signals import register_payment_providers, order_paid
from pretix_wallet.models import CustomerWallet

from pretix_wallet.payment import WalletPaymentProvider, _wallet_transaction


@receiver(register_payment_providers, dispatch_uid="payment_wallet")
def register_payment_provider(sender, **kwargs):
    return [WalletPaymentProvider]


@receiver(order_paid, dispatch_uid="payment_wallet_order_paid")
def wallet_order_paid(sender, order, **kwargs):
    top_up_positions = list(filter(lambda pos: position_is_top_up_product(pos), order.positions))
    if top_up_positions:
        CustomerWallet.create_if_non_existent(sender.organizer, order.customer)
        try:
            top_up_value = sum(lambda pos: pos.price, top_up_positions)
            _wallet_transaction(sender, order.payments.last(), order.customer.wallet.giftcard, sign=1,
                                amount=top_up_value)
        except PaymentException as e:
            raise e


def position_is_top_up_product(event, position):
    top_up_products = event.settings.get("payment_wallet_top_up_products").lower().split(',')
    product_name = position.item.name.localize('en').lower()
    return product_name in top_up_products
