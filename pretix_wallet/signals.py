from django.dispatch import receiver
from pretix.base.signals import register_payment_providers

from pretix_wallet.payment import WalletPaymentProvider


@receiver(register_payment_providers, dispatch_uid="payment_wallet")
def register_payment_provider(sender, **kwargs):
    return [WalletPaymentProvider]
