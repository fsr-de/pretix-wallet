from django.urls import path
from pretix.api.urls import event_router, orga_router

from pretix_wallet.views import (
    CustomerCreateWalletViewSet,
    PairingView,
    ProductViewSet,
    RemovePairingView,
    TransactionListView,
    TransactionViewSet,
    WalletViewSet,
)

app_name = "pretix_wallet"

event_router.register(r"wallet/pos/terminal", ProductViewSet, basename="terminal")
event_router.register(
    r"wallet/pos/wallets/token", WalletViewSet, basename="user_wallet"
)
event_router.register(
    r"wallet/pos/wallets/token/(?P<token_id>[^/.]+)/transactions",
    TransactionViewSet,
    basename="transactions",
)

orga_router.register(
    r"wallet", CustomerCreateWalletViewSet, basename="customer-create-wallet"
)

organizer_patterns = [
    path("account/wallet/", TransactionListView.as_view(), name="transactions"),
    path("account/wallet/pair/<str:token_id>/", PairingView.as_view(), name="pair"),
    path("account/wallet/unpair/", RemovePairingView.as_view(), name="unpair"),
]
