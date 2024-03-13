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
    CustomerWallet.create_if_non_existent(sender.organizer, order.customer)
    try:
        _wallet_transaction(sender, order.payments.last(), order.customer.wallet.giftcard, sign=1)
    except PaymentException as e:
        raise e