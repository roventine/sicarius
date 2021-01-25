import requests
import os, json, math, sys, time, re
from multiprocessing import Pool
from lxml import etree
import util.files as files
import util.texts as texts
import util.datetimes as dt
import util.data_channel_api as data_channel

path_base = os.path.dirname(os.path.abspath(__file__))
file_config = 'config.yaml'
path_config = os.path.join(path_base, file_config)
path_data = os.path.join(path_base, 'data')
url_base = 'http://www.zfcg.sh.gov.cn'

headers = {
    'Host': 'www.zfcg.sh.gov.cn',
    'Connection': 'keep-alive',
    'Accept': 'application/json, text/javascript, */*; q=0.01',
    'X-Requested-With': 'XMLHttpRequest',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36',
    'Content-Type': 'application/json',
    'Referer': 'http://www.zfcg.sh.gov.cn/shCategory19/index.html?utm=sites_group_front.5b1ba037.0.0.b9565e50509011ebbf96fb4f33f450c5',
    'Accept-Encoding': 'gzip, deflate',
    'Accept-Language': 'en-US,en;q=0.9,zh;q=0.8,zh-TW;q=0.7,zh-CN;q=0.6',
    'Cookie': '_zcy_log_client_uuid=9a640150-5090-11eb-a145-f1efc841b18d'
}

url_ref = {
    'detail': '/api/core/remote/supplierDetail',
    'company': '/api/core/remote/supplierCompany',
    'legal': '/api/core/remote/supplierLegal',
    'certificates': '/api/core/remote/supplierCertificates'
}


def show_progress_bar(p):
    p_s = "%.2f%%" % (p * 100)
    n = round(p * 50)
    s = ('#' * n).ljust(50, '-')
    f = sys.stdout
    f.write(p_s.ljust(8, ' ') + '[' + s + ']')
    f.flush()
    f.write('\r')


# 政府采购爬虫
class ZFCGSpider():

    def __init__(self):
        self.config = files.of_yaml(path_config)
        self.last_supplier_id = self.config['last_supplier_id']
        self.last_biding_result_notice_id = str(self.config['last_biding_result_notice_id'])
        self.supplier_id_list = []
        self.supplier_info_list = []
        self.biding_result_notice_id_list = []
        self.biding_result_notice_info_list = []
        self.data_files = []

    def to_supplier_id_list(self):
        url = '{0}{1}'.format(url_base, '/api/core/remote/supplierList')
        params = {
            'pageNo': '1',
            'pageSize': '1',
            'district': '310000',
            'hangupStatus': '0',
            'regDistName': '%E6%AD%A3%E5%B8%B8',
            'status': 'OFFICIAL',
            '_t': '1609987528360'
        }
        r = requests.get(url=url, headers=headers, params=params)
        if r.status_code == 200:
            total = r.json()['total']
            current_supplier_id = r.json()['data'][0]['supplierId']
            self.config['last_supplier_id'] = current_supplier_id

        page_size = 15
        params['pageSize'] = page_size
        page_count = math.ceil(total / page_size)
        for i in range(page_count + 1)[1:]:
            params['pageNo'] = i
            r = requests.get(url=url, headers=headers, params=params)
            if r.status_code == 200:
                supplier_slice = r.json()['data']
                for supplier in supplier_slice:
                    if supplier['supplierId'] == self.last_supplier_id:
                        print('reached last supplier id,return from here')
                        return self
                    else:
                        self.supplier_id_list.append(supplier)
        return self

    @staticmethod
    def to_supplier_info(supplier: dict):
        try:
            for k, v in url_ref.items():
                url = '{0}{1}'.format(url_base, v)
                params = {
                    'supplierId': supplier['supplierId']
                }
                r = requests.get(url=url, headers=headers, params=params)
                if r.status_code == 200:
                    supplier[k] = r.json()
        except Exception as ignored:
            print(ignored)
            pass
        return supplier

    def to_supplier_info_list_in_concurrent(self):

        result = []
        total = len(self.supplier_id_list)
        pool = Pool(os.cpu_count())

        for i, supplier in enumerate(self.supplier_id_list):
            result.append(pool.apply_async(func=self.to_supplier_info, args=(supplier,)))
            show_progress_bar((i + 1) / total)

        pool.close()
        pool.join()

        for i, res in enumerate(result):
            self.supplier_info_list.append(res.get())
            show_progress_bar((i + 1) / total)

        return self

    def to_supplier_info_list(self):
        total = len(self.supplier_id_list)
        for i, supplier in enumerate(self.supplier_id_list):
            self.supplier_info_list.append(self.to_supplier_info(supplier))
            show_progress_bar((i + 1) / total)
        return self

    @staticmethod
    def to_biding_result_notice_id_partial(page_index):
        url = '{0}{1}'.format(url_base, '/front/search/category')
        result = {
            'success': False,
            'index': page_index,
            'data': []
        }
        data = {
            'categoryCode': 'ZcyAnnouncement3004',
            'districtCode': ['319900'],
            'pageNo': page_index,
            'pageSize': 100,
            'utm': 'sites_group_front.2ef5001f.0.0.c859a140534811ebb1dffda6076cb49f'
        }
        r = requests.post(url, json=data, headers=headers)
        if r.status_code == 200:
            result['success'] = True
            result['data'] = r.json()['hits']['hits']
        return result

    def to_biding_result_list_in_concurrent(self):

        result_list = []
        future_list = []
        total = 9900
        page_size = 100
        page_count = math.ceil(total / page_size) + 1

        pool = Pool(os.cpu_count())
        for page_index in range(page_count + 1)[1:]:
            future_list.append(pool.apply_async(func=self.to_biding_result_notice_id_partial, args=(page_index,)))
            show_progress_bar(page_index / page_count)

        pool.close()
        pool.join()

        for i, res in enumerate(future_list):
            result = res.get()
            if not result['success']:
                print(result['index'])
                pass
            else:
                result_list = result_list + result['data']
            show_progress_bar((i + 1) / page_count)

        return result_list

    def to_biding_result_notice_id_list(self):
        url = '{0}{1}'.format(url_base, '/front/search/category')
        data = {
            'categoryCode': 'ZcyAnnouncement3004',
            'districtCode': ['319900'],
            'pageNo': 1,
            'pageSize': 1,
            'utm': 'sites_group_front.2ef5001f.0.0.c859a140534811ebb1dffda6076cb49f'
        }
        r = requests.post(url, json=data, headers=headers)
        if r.status_code == 200:
            current_biding_result_notice_id = r.json()['hits']['hits'][0]['_id']
            self.config['last_biding_result_notice_id'] = current_biding_result_notice_id

        total = 9900
        page_size = 100
        data['pageSize'] = page_size
        page_count = math.ceil(total / page_size)
        for i in range(page_count + 1)[1:]:
            show_progress_bar(i / page_count)
            data['pageNo'] = i
            r = requests.post(url=url, json=data, headers=headers)
            if r.status_code == 200:
                result_slice = r.json()['hits']['hits']
                for result in result_slice:
                    if result['_id'] == self.last_biding_result_notice_id:
                        print('reached last biding result notice id,return from here')

                        return self
                    else:
                        self.biding_result_notice_id_list.append(result)

        return self

    # 中标公告正文
    def to_biding_result_notice_info_list(self):

        total = len(self.biding_result_notice_id_list)
        for i, bid_result in enumerate(self.biding_result_notice_id_list):
            show_progress_bar((i + 1) / total)
            result_info = bid_result['_source']
            url_suffix = result_info['url']
            url = '{0}{1}'.format(url_base, url_suffix)
            r = requests.get(url, headers=headers)
            if r.status_code == 200:
                r.encoding = r.apparent_encoding
                html = etree.HTML(r.text)
                content = html.xpath('//*[@name="articleDetail"]/@value')[0]
                j = json.loads(content)
                result_info['content'] = texts.to_text(j['content'])
                self.biding_result_notice_info_list.append(result_info)
        return self

    def serialize(self):
        today = dt.to_string(dt.to_now(), "%Y%m%d")

        n = files.to_data_file('ZFCG', 'SUPPLIER_INFO', '1G', today)
        p = files.to_data_path(path_data, n)
        files.to_json(p, self.supplier_info_list)
        gz = files.to_gz(p)
        self.data_files.append(gz)

        n = files.to_data_file('ZFCG', 'BIDING_RESULT_NOTICE_INFO', '1G', today)
        p = files.to_data_path(path_data, n)
        files.to_json(p, self.biding_result_notice_info_list)
        gz = files.to_gz(p)
        self.data_files.append(gz)

        # files.to_yaml(path_config, self.config)

        return self

    def transmit(self):
        for gz in self.data_files:
            data_channel.transmit(gz)
        return self

    def wipe(self):
        for gz in self.data_files:
            files.delete_file(gz)
        return self


if __name__ == '__main__':
    ZFCGSpider().to_supplier_id_list() \
        .to_supplier_info_list() \
        .to_biding_result_notice_id_list() \
        .to_biding_result_notice_info_list() \
        .serialize()\
        .transmit()\
        .wipe()
