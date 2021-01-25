import binascii
import hashlib
import requests

APP_NAME = 'SICARIUS'
APP_KEY = binascii.b2a_base64(APP_NAME.encode())
URL_CHANNEL = 'https://dapp.sh.abchina.com/nullius/api/v1/datachannel/file'
MEM = 'On the word of no one'
SIGN = hashlib.sha256('{0}{1}'.format(MEM, APP_KEY).encode()).hexdigest()


def transmit(f):
    print('{0} -> {1}'.format(URL_CHANNEL, f))
    file = {'file': open(f, 'rb')}
    data = {
        'sign': SIGN
    }
    r = requests.post(URL_CHANNEL, files=file, data=data)
    print('{0} -> {1} -> {2}'.format( URL_CHANNEL, f, r.status_code))
