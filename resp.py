import requests

response = requests.post(
    'https://iam.api.cloud.yandex.net/iam/v1/tokens',
    json={'yandexPassportOauthToken': 'y0__xD-q-OqBBjB3RMg0r6SphShm4pCN0xI2CrjYj2fFbsWjII3qg'}
)

print(response.json())