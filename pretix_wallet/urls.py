from django.urls import path
from pretix.api.urls import event_router

from pretix_wallet.views import TransactionListView, ProductViewSet, WalletViewSet, TransactionViewSet

event_router.register(r'wallet/pos/terminal', ProductViewSet, basename='terminal')
event_router.register(r'wallet/pos/wallets/token', WalletViewSet, basename='user_wallet')
event_router.register(r'wallet/pos/wallets/token/(?P<token_id>[^/.]+)/transactions', TransactionViewSet, basename='transactions')

organizer_patterns = [
    path('account/wallet/', TransactionListView.as_view(), name='wallet'),
]
