from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import algorithms
from Crypto.Cipher import AES
from binascii import b2a_hex, a2b_hex, b2a_base64, a2b_base64
import hashlib
import requests
from util.logger import logger
import json
import base64

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
    # return b2a_hex(cipher_text).decode().upper()
    return b2a_base64(cipher_text).decode()


def decrypt(text):
    sha = hashlib.sha256()
    sha.update(enc_key.encode('utf-8'))
    cryptor = AES.new(sha.digest(), AES.MODE_ECB)
    plain_text = cryptor.decrypt(a2b_base64(text))
    # plain_text = cryptor.decrypt(a2b_hex(text))
    plain_text = pkcs7_unpadding(plain_text)
    plain_text = plain_text.hex()
    return plain_text


def sign(cipher_text):
    sha = hashlib.sha256()
    packet = '{0}&key={1}'.format(cipher_text, sign_key)
    sha.update(packet.encode('utf-8'))
    # return sha.hexdigest().upper()
    return b2a_base64(sha.digest()).decode('utf-8').replace('\n', '')


def notify(msg):
    # packet = json.dumps(msg, ensure_ascii=False)
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

# enc = encrypt('中文')
# print(enc)
# print(sign('中文'))
# sha = hashlib.sha256()
# sha.update('中文'.encode())
# print(b2a_base64(sha.digest()).decode('utf-8'))

# print()

# print(encrypt('{\'success\': True, \'msg\': \'by all means , it shall be done -- by zzz, solo in dark\', \'license\': {\'eGrpName\': None, \'eGrpShform\': None, \'ePubGroup\': \'unshow\', \'elnfyreturnbuild\': \'unshow\', \'isPublicPeriod\': None, \'simpleCanrea\': None, \'noticeFrom\': None, \'noticeTo\': None, \'pripId\': \'111337FF1F0EFE0DD222EA23FC0CD845846007600760A14522C62297F097F097FC97F09BFC18FC18731473B20790-1608533071261\', \'regNo\': \'310118004070437\', \'uniscId\': \'91310118MA1JP08462\', \'regState\': \'1\', \'regState_CN\': \'存续（在营、开业、在册）\', \'entType\': \'7\', \'name\': \'徐鸣\', \'industryPhy\': \'E\', \'entTypeForQuery\': 7, \'entTypeForAnnualReport\': 3, \'linkmanName\': \'\', \'linkmanCerNo\': \'\', \'linkmanPhone\': \'\', \'busExceptCount\': 0, \'illCount\': 0, \'nodeNum\': \'310000\', \'entName\': \'上海丽淇电力设备安装工程中心\', \'entType_CN\': \'个人独资企业\', \'regCap\': 10.0, \'regCapStr\': None, \'dom\': \'上海市青浦区赵巷镇沪青平公路3398号1幢1层\', \'opFrom\': \'2020-11-12\', \'opTo\': None, \'opScope\': \'许可项目：各类工程建设活动；建筑劳务分包（依法须经批准的项目，经相关部门批准后方可开展经营活动，具体经营项目以相关部门批准文件或许可证件为准）一般项目：电力设备领域内的技术咨询、技术转让、技术服务、技术开发，销售电线电缆、机械设备、五金交电、文教用品、办公用品、家居用品、机电产品、电子产品、金属材料及制品、建筑装潢材料、消防器材、电子电器、机电设备、园艺设备及配件、通信设备、污水处理设备、自动化控制系统及控制元件、管道及管道配件、食用农产品。（除依法须经批准的项目外，凭营业执照依法自主开展经营活动）。\', \'regOrg_CN\': \'青浦区市场监督管理局 \', \'regOrg\': \'310118\', \'estDate\': \'2020-11-12\', \'apprDate\': \'2020-11-12\', \'revDate\': None, \'regCapCur_CN\': \'人民币              \', \'shareholder\': [{\'inv\': \'徐鸣\', \'invType_CN\': \'自然人股东\', \'sConForm_CN\': \'以个人财产出资\'}]}}'))
