import datetime

from django.db import models
from pretix.base.models import Customer, GiftCard, MembershipType, Membership
from pretix.base.models.giftcards import gen_giftcard_secret

VERY_FAR_FUTURE = datetime.date(2099, 12, 12)


class CustomerWallet(models.Model):
    customer = models.OneToOneField(Customer, on_delete=models.CASCADE, related_name='wallet')
    giftcard = models.OneToOneField(GiftCard, on_delete=models.CASCADE, related_name='wallet')

    @staticmethod
    def create_if_non_existent(organizer, customer):
        try:
            _ = customer.wallet
        except CustomerWallet.DoesNotExist:
            giftcard = GiftCard.objects.create(
                issuer=organizer,
                currency="EUR",
                conditions=f"Wallet for {customer.name_cached} ({customer.email})",
                secret=f"{customer.email.split('@')[0]}-{gen_giftcard_secret(length=organizer.settings.giftcard_length)}")
            CustomerWallet.objects.create(customer=customer, giftcard=giftcard)
        create_membership_if_not_existant(organizer, customer)


def membership_type_name_for_organizer(organizer):
    return f"{organizer.name} Wallet"


def get_or_create_wallet_membership_type(organizer):
    membership_type = organizer.membership_types.filter(name=membership_type_name_for_organizer(organizer)).first()

    if membership_type is not None:
        return membership_type

    return MembershipType.objects.create(
        name=membership_type_name_for_organizer(organizer),
        organizer=organizer,
        allow_parallel_usage=True,
        transferable=False,
        max_usages=None,
    )


def create_membership_if_not_existant(organizer, customer):
    membership_type = get_or_create_wallet_membership_type(organizer)
    if not membership_type.memberships.filter(customer=customer).exists():
        Membership.objects.create(
            testmode=False,
            customer=customer,
            membership_type=membership_type,
            date_start=datetime.date.today(),
            date_end=VERY_FAR_FUTURE
        )
