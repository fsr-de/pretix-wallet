from datetime import datetime

from django.db import transaction
from pretix.base.models import Item, Order, OrderPosition
from rest_framework.exceptions import ValidationError
from rest_framework.fields import SerializerMethodField, CharField, ListField, DateTimeField
from rest_framework.serializers import Serializer, ModelSerializer

from pretix_wallet.models import CustomerWallet


class ProductSerializer(ModelSerializer):
    friendly_name = CharField(source='name')
    price = SerializerMethodField()

    class Meta:
        model = Item
        fields = ['id', 'friendly_name', 'price']

    def get_price(self, obj):
        return int(obj.default_price * 100)


class WalletSerializer(ModelSerializer):
    token_id = CharField(source='customer.wallet.giftcard.linked_media.first.identifier')
    paired_user = CharField(source='customer.name_cached')
    balance = SerializerMethodField()
    created_at = DateTimeField(source='customer.wallet.giftcard.issuance')

    class Meta:
        model = CustomerWallet
        fields = ['id', 'token_id', 'created_at', 'balance', 'paired_user']

    def get_created_at(self, obj):
        return datetime.now()

    def get_balance(self, obj):
        return int(obj.giftcard.value * 100)


class TransactionSerializer(Serializer):
    products = ListField()
    description = CharField(required=False)
    tag = CharField(required=False)
    idempotency_key = CharField(required=False)

    def validate_products(self, value):
        items = []
        for item_id in value:
            try:
                item = Item.objects.get(pk=item_id)
                items.append(item)
            except (Item.DoesNotExist, ValueError):
                raise ValidationError("Item with id {} does not exist".format(item_id))
        return items

    def create(self, validated_data):
        with transaction.atomic():
            wallet = self.context["wallet"]
            order = Order(event=self.context["event"], customer=wallet.customer)
            positions = []
            for item in validated_data["products"]:
                positions.append(OrderPosition(order=order, item=item, price=item.default_price))
            order.total = sum([p.price for p in positions])
            order.save()
            for p in positions:
                p.save()
            payment = order.payments.create(provider="wallet", amount=order.total, info_data={
                'gift_card': wallet.giftcard.pk,
                'gift_card_secret': wallet.giftcard.secret,
                'user': wallet.customer.name_cached,
                'user_id': wallet.customer.external_identifier,
                'retry': True
            })
            payment.payment_provider.execute_payment(None, payment)
            order.create_transactions()
            return order
