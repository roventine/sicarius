import hashlib
import json
from binascii import b2a_base64, a2b_base64

import requests
from Crypto.Cipher import AES
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import algorithms

from util.logger import logger

requests.packages.urllib3.disable_warnings()

# 通讯方式采用https方式
# 报文格式：json
# 字符集：UTF-8编码
# 签名算法：SHA256
# 加密算法：AES（工作模式为ECB，填充模式PKCS7Padding）
# 测试环境加密密钥：12345678
# 测试环境签名密钥：88888888

enc_key = '12345678'
sign_key = '88888888'

# 对key做sha256然后当作aes的key
# 如果不看java源码我无从推断出这一点
# 也正是出于这一点我决定不提取一个工具Cipher类
#


url_to_notify = 'https://app.sh.abchina.com/qht/EtpsInfoRecv.do'
# url_to_notify = 'http://223.72.214.168/qht/EtpsInfoRecv.do'

headers = {
    'X-Requested-With': 'XMLHttpRequest',
    'Accept': 'application/json',
    'User-Agent': 'Mozilla/5.0 (Linux; Android 10; TAS-AN00 Build/HUAWEITAS-AN00; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/78.0.3904.108 Mobile Safari/537.36 Html5Plus/1.0',
    'Content-Type': 'application/json;charset=utf-8',
    'Host': 'app.gsxt.gov.cn',
    'Connection': 'Keep-Alive',
    'Accept-Encoding': 'gzip',
    'Content-Length': '155'
}


def pkcs7_padding(data):
    if not isinstance(data, bytes):
        data = data.encode()
    padder = padding.PKCS7(algorithms.AES.block_size).padder()
    padded_data = padder.update(data) + padder.finalize()
    return padded_data


def pkcs7_unpadding(padded_data):
    unpadder = padding.PKCS7(algorithms.AES.block_size).unpadder()
    data = unpadder.update(padded_data)
    try:
        uppadded_data = data + unpadder.finalize()
    except ValueError:
        raise Exception('invalid cipher data!')
    else:
        return uppadded_data


def encrypt(text):
    sha = hashlib.sha256()
    sha.update(enc_key.encode('utf-8'))
    cryptor = AES.new(sha.digest(), AES.MODE_ECB)
    text = text.encode('utf-8')
    text = pkcs7_padding(text)
    cipher_text = cryptor.encrypt(text)
    return b2a_base64(cipher_text).decode()


def decrypt(text):
    sha = hashlib.sha256()
    sha.update(enc_key.encode('utf-8'))
    cryptor = AES.new(sha.digest(), AES.MODE_ECB)
    plain_text = cryptor.decrypt(a2b_base64(text))
    plain_text = pkcs7_unpadding(plain_text)
    plain_text = plain_text.hex()
    return plain_text


def sign(cipher_text):
    sha = hashlib.sha256()
    packet = '{0}&key={1}'.format(cipher_text, sign_key)
    sha.update(packet.encode('utf-8'))
    return b2a_base64(sha.digest()).decode('utf-8').replace('\n', '')


def notify(msg):
    logger.info('packet -> {0}'.format(msg))
    cipher_packet = encrypt(msg)
    logger.info('encrypt -> {0}'.format(cipher_packet))
    signature = sign(cipher_packet)
    logger.info('sign -> {0}'.format(signature))
    notify_data = {
        'request': cipher_packet,
        'signature': signature
    }
    post_data = json.dumps(notify_data, ensure_ascii=False)
    logger.info('post data -> {0}'.format(post_data))
    r = requests.post(url_to_notify,
                      headers=headers,
                      data=post_data,
                      verify=False)
    if r.status_code == 200:
        return r.text
    else:
        return r.status_code
