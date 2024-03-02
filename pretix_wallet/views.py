from django.views.generic import ListView
from pretix.base.models import GiftCardTransaction
from pretix.presale.views.customer import CustomerRequiredMixin


class TransactionListView(CustomerRequiredMixin, ListView):
    model = GiftCardTransaction
    template_name = "pretix_wallet/transaction_list.html"

    def get_queryset(self):
        return self.request.customer.wallet.giftcard.transactions.order_by("-datetime")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['wallet'] = self.request.customer.wallet
        return ctx
