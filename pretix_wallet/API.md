# PointOfSale API

## Authenticating
Authentication with the PointOfSale API is simple. Just include your terminal's `api_token` as a Bearer token inside an
`Authorization` HTTP header:

```````HTTP
Authorization: Bearer <API_TOKEN_GOES_HERE>
```````

Please note that your API token never automatically expires. However, it could be rolled manually.

## Wrapping
All returned entities are wrapped in a `data` key:

```JSON
{
  "data": {
    // actual data goes here
  }
}
```

## Resources
### Terminals

A terminal represents a single application instance that is permitted to access the PointOfSale API.  
Examples for terminals include:

- physical embedded devices (e.g. coffee machine, coin receptor)
- NFC-enabled smartphone apps (e.g. topping up manually in exchange for cash)
- entirely virtual services (e.g. topping up via PayPal)

```JSON
{
  "id": "coffee_machine",
  "friendly_name": "Kaffeemaschine",
  "permission": "debit",
  "products": [],
  "api_token": "<API KEY>"
}
```

The `friendly_name` appears in user-facing communication, while the unique `id` is used behind-the-scenes.  
It is important to note, that the `api_token` is only included immediately after token change
(e.g. after creating the terminal).

### Wallets and Transactions
A wallet is similar to a bank account. It is a place to store transactions and calculates its balance by summing
them up. They are typically associated with a token by its `token_id` (RFID tag hardware UUID).

Furthermore, wallets are associated to a pretix customer account, making them manageable through the web portal, facilitating wallet recovery upon loss of token, top-up, and much more.
  
When fetched individually, wallets contain a list of transactions, latest first:

```JSON
{
    "id": "wal_K6lIeaZ9H3UZPqxm",
    "token_id": "<TOKEN_HARDWARE_UUID>",
    "created_at": "2021-10-31T20:44:11.000000Z",
    "balance": 150,
    "paired_user": "sebastian.walker",
    "transactions": [
        {
            "id": "txn_LgIhM47W7UZAJcyZ",
            "amount": -50,
            "description": "Kaffee",
            "tag": "coffee",
            "terminal": {
                "id": "kaffeemaschine",
                "friendly_name": "Kaffeemaschine",
                "permission": "all"
            },
            "timestamp": {
                "raw": "2021-10-31T20:45:20.000000Z",
                "readable": "31.10.2021 08:45"
            }
        },
        {
            "id": "txn_jNJobwQL76kk8LJV",
            "amount": 200,
            "description": "Manuelle Aufladung durch FSR",
            "tag": null,
            "terminal": null,
            "timestamp": {
                "raw": "2021-10-31T20:44:56.000000Z",
                "readable": "31.10.2021 08:44"
            }
        }
    ]
}
```

### Currency and transactions
Currency is always represented as an integer in cents. Credit transactions carry a positive sign, debit transactions
carry a negative sign.

Thus, the example above shows the following transactions:
- First, 2€ were credited manually. Manual transactions have a `terminal` field of null.
- Next, 50ct were debited by the coffee machine. The transaction was also tagged with the "coffee" `tag`.

## Available Endpoints
### Fetching terminal metadata

Fetch information about the currently authenticated terminal, including the `friendly_name` or the `permission` level.

```HTTP
GET /pos/terminal
```

#### Request
_No request parameters_

#### Response
A [Terminal](../README.md#terminals) resource, wrapped in a data attribute.
```JSON
{
  "data": {
    "id": "coffee_machine",
    "friendly_name": "Kaffeemaschine",
    "permission": "debit",
    "products": [
      {
        "id": "espresso",
        "friendly_name": "Espresso",
        "price": 25
      },
      {
        "id": "cappuccino",
        "friendly_name": "Cappucino",
        "price": 50
      }
    ]
  }
}
```

#### Possible errors
- **401 Unauthenticated** - Check your API token.

### Retrieve wallet balance

Fetch the current balance of the wallet associated with the given `token_id`.
```HTTP
GET /pos/wallets/token/<TOKEN_ID>
```

#### Request
_No request parameters_

#### Response
A [Wallet](../README.md#wallets-and-transactions) resource, wrapped in a data attribute. Note that `transactions` are
not included on this endpoint.
```JSON
{
  "data": {
    "id": "wal_K6lIeaZ9H3UZPqxm",
    "token_id": "<TOKEN_HARDWARE_UUID>",
    "created_at": "2021-10-31T20:44:11.000000Z",
    "balance": 150,
    "paired_user": "max.mustermann"
  }
}
```

#### Possible errors
- **401 Unauthenticated** - Check your API token. [See how...](README.md#authenticating)
- **404 Not Found** - This token is not paired to a wallet.

### Executing transactions on a wallet

```HTTP
POST /pos/wallets/token/<TOKEN_ID>/transactions
```

#### Request

```JSON
{
  "products": ["espresso", "espresso", "cappuccino"],
  "description": "Your coffee order in H building",
  "tag": "coffee",
  "idempotency_key": "0QwKc2c9jUIxPyaHEjYQ"
}
```

| field | description |
|---|---|
|`products`| An array containing the purchased product's IDs. Multiple occurrences will result in multiple consideration. |
|`description`| Transaction description used in user-facing communication. |
|`tag`| Optional: A tag used for classifying the transaction later. |
|`idempotency_key`| Optional: A unique, random key consistent across attempts to execute this transaction. Consecutive attempts with identical idempotency keys will be ignored, returning a 202 Accepted. |

#### Response
A [Wallet](../README.md#wallets-and-transactions) resource, wrapped in a data attribute. Note that past `transactions`
are not included on this endpoint.

```JSON
{
  "data": {
    "id": "wal_K6lIeaZ9H3UZPqxm",
    "token_id": "<TOKEN_HARDWARE_UUID>",
    "created_at": "2021-10-31T20:44:11.000000Z",
    "balance": 150,
    "paired_user": null
  }
}
```

#### Possible errors
- **202 Accepted** - Another transaction with an identical `idempotency_key` has already been processed.
- **400 Unprocessable Entity** - Your request parameters are invalid. Details are available in the response body.
- **401 Unauthenticated** - Check your API token. [See how...](#authenticating)
- **403 Forbidden** - Check your terminal's [permission level](../README.md#terminals).
