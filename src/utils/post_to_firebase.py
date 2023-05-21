import requests
from utils.utils import CONFIG
from dotenv import dotenv_values

env = dotenv_values('.env')


def post_to_firebase(data):
    POST_URL = f"{CONFIG.base_url}/api/appResult"
    return requests.post(POST_URL, data, headers={
        'Authorization': env['FIREBASE_HOST_POST_ENDPOINT_SECRET']
    })