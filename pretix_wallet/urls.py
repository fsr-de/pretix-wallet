from django.urls import path

from pretix_wallet.views import CustomerLoginReturnView

organizer_patterns = [
    path("wallet/return/", CustomerLoginReturnView.as_view(), name="customer_login_return"),
]
