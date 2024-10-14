from django.db import models
from pretix.base.models import Customer, GiftCard


class CustomerWallet(models.Model):
    customer = models.OneToOneField(
        Customer, on_delete=models.CASCADE, related_name="wallet"
    )
    giftcard = models.OneToOneField(
        GiftCard, on_delete=models.CASCADE, related_name="wallet"
    )
