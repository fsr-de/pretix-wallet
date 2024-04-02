import csv
import json

import requests

API_BASE = "http://localhost:8000/api/v1/organizers/test"
API_TOKEN = "dt5g5zn0jh97w352vh4zny79os131k8ksrtivrz26rj9v8m9b7xri0otwhludpqf"


def create_customer(uuid, name, email):
    response = requests.post(f"{API_BASE}/customers/", data={"external_identifier": uuid, "name_parts": json.dumps({"full_name": name}), "email": email, "is_active": True, "is_verified": True}, headers={"Authorization": f"Token {API_TOKEN}"})
    response.raise_for_status()
    return response.json()


def create_wallet(customer, balance, token):
    data = {
        "customer": customer,
        "initial_balance": balance,
    }
    if token:
        data["token_id"] = token
    response = requests.post(f"{API_BASE}/wallet/", data=data, headers={"Authorization": f"Token {API_TOKEN}"})
    response.raise_for_status()


def migrate():
    with open('wallet_migration.csv', encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file, delimiter=';')
        for row in reader:
            try:
                customer = create_customer(row["uuid"], row['name'], row['email'])
                create_wallet(customer["identifier"], row['balance'], row['token_id'])
            except Exception as e:
                print(f"Failed to migrate {row['name']}: {e}")


if __name__ == "__main__":
    migrate()
