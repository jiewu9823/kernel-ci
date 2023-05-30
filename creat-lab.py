import json
import requests

BACKEND_URL = "http://192.168.1.100:8081"
AUTHORIZATION_TOKEN = "47db837b-8e2c-45b0-846f-44345a076f7f"


def create_lab():
    headers = {
        "Authorization": AUTHORIZATION_TOKEN,
        "Content-Type": "application/json"
    }

    payload = {
        "name": "lab-01-nantong",
        "contact": {
            "name": "jean",
            "surname": "wu",
            "email": "wujie22@iscas.ac.cn"
        }
    }

    url = BACKEND_URL + '/lab'
    response = requests.post(url, data=json.dumps(payload), headers=headers)

    print (response.content)


if __name__ == "__main__":
    create_lab()
