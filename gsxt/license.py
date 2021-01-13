import requests
import time
from random import Random
from util.logger import logger

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


def to_inv(d: dict):
    return {'inv': d['inv'], 'invType_CN': d['invType_CN'], 'sConForm_CN': d['sConForm_CN']}


def to_inv_list(l: list):
    inv_list = []
    for i in l:
        inv_list.append(to_inv(i))
    return inv_list


def is_exist_corp(id_uni: str):
    count_retry = 10
    i = 0
    rand = Random()
    result = {'success': False, 'object': ''}
    url = 'http://app.gsxt.gov.cn/gsxt/cn/gov/saic/web/controller/PrimaryInfoIndexAppController/search?page=1'
    data = {'searchword': id_uni,
            'conditions': {'excep_tab': '0', 'ill_tab': '0', 'area': '0', 'cStatus': '0', 'xzxk': '0', 'xzcf': '0',
                           'dydj': '0'}, 'sourceType': 'A'}
    while i < count_retry:
        try:
            r = requests.post(url, headers=headers, json=data, timeout=30)
            if r.status_code == 200:
                data = r.json()['data']['result']['data']
                result['success'] = True
                result['object'] = data
                return result
            else:
                i = i + 1
                t = rand.randint(1, 10)
                logger.info('phase 1, retry count {0}, sleep {1} seconds', str(i), str(t))
                time.sleep(t)
                continue

        except Exception as e:
            logger.error(e)
            i = i + 1
            t = rand.randint(1, 10)
            logger.info('phase 1, retry count {0}, sleep {1} seconds', str(i), str(t))
            continue

    msg = 'phase 1 - > retry count reach max limit'.format(id_uni)
    logger.info(msg)
    result['object'] = msg

    return result


def to_lic_base_info(pripid,
                     entType,
                     nodeNum):
    count_retry = 10
    i = 0
    rand = Random()
    result = {'success': False, 'object': ''}
    url_ent_info = f'http://app.gsxt.gov.cn/gsxt/corp-query-entprise-info-primaryinfoapp-entbaseInfo-{pripid}.html?nodeNum={nodeNum}&entType={entType}&sourceType=A'
    while i < count_retry:
        try:
            r = requests.post(url_ent_info, headers=headers, json={})
            if r.status_code == 200:
                data = r.json()['result']
                result['success'] = True
                result['object'] = data
                return result
            else:
                i = i + 1
                t = rand.randint(1, 10)
                logger.info('phase 2, retry count {0}, sleep {1} seconds', str(i), str(t))
                time.sleep(t)
                continue

        except Exception as e:
            logger.error(e)
            i = i + 1
            t = rand.randint(1, 10)
            logger.info('phase 2, retry count {0}, sleep {1} seconds', str(i), str(t))
            continue

    msg = 'phase 2 -> retry count reach max limit'
    logger.info(msg)
    result['object'] = msg

    return result


def to_shareholder_list(pripid,
                        nodeNum):
    count_retry = 10
    i = 0
    rand = Random()
    result = {'success': False, 'object': ''}
    url_shareholder = f'http://app.gsxt.gov.cn/gsxt/corp-query-entprise-info-shareholder-{pripid}.html?nodeNum={nodeNum}&entType=1&start=0&sourceType=A'
    while i < count_retry:
        try:
            r = requests.post(url_shareholder, headers=headers, json={})
            if r.status_code == 200:
                data = r.json()['data']
                result['success'] = True
                result['object'] = data
                return result
            else:
                i = i + 1
                t = rand.randint(1, 10)
                logger.info('phase 3, retry count {0}, sleep {1} seconds', str(i), str(t))
                time.sleep(t)
                continue

        except Exception as e:
            logger.error(e)
            i = i + 1
            t = rand.randint(1, 10)
            logger.info('phase 3, retry count {0}, sleep {1} seconds', str(i), str(t))
            continue

    msg = 'phase 3 -> retry count reach max limit'
    logger.info(msg)
    result['object'] = msg

    return result


def to_license_info(id_uni: str):
    result = {'success': False, 'id_uni': id_uni, 'msg': ''}
    query_result = is_exist_corp(id_uni)
    if query_result['success']:
        data = query_result['object']
        if len(data) > 0:

            logger.info('{0} -> {1}'.format(id_uni, data[0]))

            pripid = data[0]['pripid']
            entType = data[0]['entType']
            nodeNum = data[0]['nodeNum']

            base_info_result = to_lic_base_info(pripid,
                                                entType,
                                                nodeNum)
            if base_info_result['success']:
                lic = base_info_result['object']
                shareholder_result = to_shareholder_list(pripid,
                                                         nodeNum)
                if shareholder_result['success']:
                    lic['shareholder'] = to_inv_list(shareholder_result['object'])
                    result['license'] = lic
                    result['msg'] = 'by all means , it shall be done -- by zzz, solo in dark'
                    result['success'] = True
                    return result
                else:
                    result['msg'] = shareholder_result['object']
            else:
                result['msg'] = base_info_result['object']
        else:
            msg = '{0} -> 没有获取到对应信息'.format(id_uni)
            result['msg'] = msg
    else:
        result['msg'] = query_result['object']

    return result

# l = to_license_info('91310118MA1JP08462')
# print(l)
