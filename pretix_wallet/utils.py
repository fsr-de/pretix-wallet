from pretix.base.media import NfcUidMediaType
from pretix.base.models import ReusableMedium, GiftCard
from pretix.base.models.giftcards import gen_giftcard_secret

from pretix_wallet.models import CustomerWallet


def link_token_to_wallet(organizer, customer, token_id):
    medium, created = ReusableMedium.objects.get_or_create(identifier=token_id,
                                                           organizer=organizer,
                                                           type=NfcUidMediaType.identifier)
    customer.wallet.giftcard.linked_media.set([medium])
    medium.save()


def create_customerwallet_if_not_exists(organizer, customer):
    try:
        created = False
        wallet = customer.wallet
    except CustomerWallet.DoesNotExist:
        giftcard = GiftCard.objects.create(
            issuer=organizer,
            currency="EUR",
            conditions=f"Wallet for {customer.name_cached} ({customer.email})",
            secret=f"{customer.email.split('@')[0]}-{gen_giftcard_secret(length=organizer.settings.giftcard_length)}")
        wallet = CustomerWallet.objects.create(customer=customer, giftcard=giftcard)
        created = True
    return wallet, created
