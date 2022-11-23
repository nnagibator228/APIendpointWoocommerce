import requests
import urllib3
from secret_utils import read_secret
import json


def check_url_validity(img_url):
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    try:
        r = requests.head(img_url, verify=False, timeout=5)  # it is faster to only request the header
        return int(r.status_code)

    except:
        return -1


def send_webhook(img_url):
    image_url = img_url

    webhook_url = "http://wconverter:5000/webhook"
    webhook_headers = {'Content-Type': 'application/json'}
    webhook_token = read_secret("ctoken")

    data = {
        "token": webhook_token,
        "url": image_url
    }

    print(requests.post(webhook_url, data=json.dumps(data), headers=webhook_headers))


def send_init_webhook():
    webhook_url = "http://wconverter:5000/webhook"
    webhook_headers = {'Content-Type': 'application/json'}
    webhook_token = read_secret("ctoken")

    data = {
        "token": webhook_token,
        "bulk": True
    }

    return requests.post(webhook_url, data=json.dumps(data), headers=webhook_headers).content
