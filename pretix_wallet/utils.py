from django_scopes import scope
from pretix.base.media import NfcUidMediaType
from pretix.base.models import Customer, GiftCard, ReusableMedium
from pretix.base.models.giftcards import gen_giftcard_secret
from rest_framework.relations import SlugRelatedField

from pretix_wallet.models import CustomerWallet


def link_token_to_wallet(organizer, customer, token_id):
    medium, created = ReusableMedium.objects.get_or_create(
        identifier=token_id, organizer=organizer, type=NfcUidMediaType.identifier
    )
    customer.wallet.giftcard.linked_media.set([medium])
    medium.save()


def email_address_to_user_slug(email):
    return email.split("@")[0]


def create_customerwallet_if_not_exists(organizer, customer):
    try:
        created = False
        wallet = customer.wallet
    except CustomerWallet.DoesNotExist:
        giftcard = GiftCard.objects.create(
            issuer=organizer,
            currency="EUR",
            conditions=f"Wallet for {customer.name_cached} ({customer.email})",
            secret=f"{email_address_to_user_slug(customer.email)}-{gen_giftcard_secret(length=organizer.settings.giftcard_length)}",
        )
        wallet = CustomerWallet.objects.create(customer=customer, giftcard=giftcard)
        created = True
    return wallet, created


class CustomerRelatedField(SlugRelatedField):
    def get_queryset(self):
        with scope(organizer=self.context["organizer"]):
            return Customer.objects.all()
