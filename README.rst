Wallet
==========================

This is a plugin for `pretix`_. 

It realises a user-based wallet based. It uses pretix customer accounts and giftcards as a data model.

There are three components:

- A pretix payment provider (``pretix_wallet/payment.py``) that allows to pay with the wallet balance during the regular pretix checkout process.
- A frontend for the user to view their transactions and pair a NFC token to their wallet (``pretix_wallet/views.py``).
- A POS API for terminals (like coffee machines) to debit from the wallet (`see docs <API.md>`_).


Configuration
-------------

1. Install the plugin via pip and run the migrations or see `Development setup`_.

2. `Enable customer accounts <https://docs.pretix.eu/en/latest/user/customers/index.html#enabling-customer-accounts>`_

3. Enable the plugin in the 'plugins' tab in the settings of an event.

4. If you want to use the payment provider, you need to enable it in the 'payment' tab in the settings of an event.

5. If you want to use the POS API, you need to specify an API key in the settings of the payment provider.

The frontend views can be accessed at ``<ORGANIZER_URL>/account/wallet/`` and the base URL of the POS API is ``<PRETIX_URL>/api/v1/organizers/<ORGANIZER_SLUG>/events/<EVENT_SLUG>/wallet/``.


Development setup
-----------------

1. Make sure that you have a working `pretix development setup`_.

2. Clone this repository.

3. Activate the virtual environment you use for pretix development.

4. Execute ``python setup.py develop`` within this directory to register this application with pretix's plugin registry.

5. Execute ``python manage.py migrate`` from your pretix directory to create the database tables.

5. Execute ``make`` within this directory to compile translations.

6. Restart your local pretix server. You can now use the plugin from this repository for your events by enabling it in
   the 'plugins' tab in the settings.

This plugin has CI set up to enforce a few code style rules. To check locally, you need these packages installed::

    pip install flake8 isort black

To check your plugin for rule violations, run::

    black --check .
    isort -c .
    flake8 .

You can auto-fix some of these issues by running::

    isort .
    black .

To automatically check for these issues before you commit, you can run ``.install-hooks``.


License
-------

Released under the terms of the Apache License 2.0



.. _pretix: https://github.com/pretix/pretix
.. _pretix development setup: https://docs.pretix.eu/en/latest/development/setup.html
