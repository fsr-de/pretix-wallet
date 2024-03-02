from django.urls import path, re_path

from pretix_wallet.views import TransactionListView

organizer_patterns = [
    #re_path(r'^api/organizers/(?P<organizer>[^/]+)/snippets/', TransactionListView.as_view()),
    path('account/wallet/', TransactionListView.as_view(), name='wallet'),
]

