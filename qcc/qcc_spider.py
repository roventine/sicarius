import os
import random
import time

import requests

import util.datachannel_client as channel_api
import util.datetimes as dt
import util.files as files
import util.progress_bar as bar
from constant import APP_NAME
from util.logger import logger

QCC_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
QCC_DATA_DIR = os.path.join(QCC_BASE_DIR, 'data')


class QCCSpider:
    headers = {
        "authority": "www.qcc.com",
        "scheme": "https",
        "path": "/api/elib/getNewCompany?flag=&industry=&isSortAsc=false&pageSize=20&province=SH&sortField=startdate&startDateBegin=&startDateEnd=",
        "accept": "application/json, text/plain, */*",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36",
        "x-requested-with": "XMLHttpRequest",
        "sec-fetch-site": "same-origin",
        "sec-fetch-mode": "cors",
        "sec-fetch-dest": "empty",
        "referer": "https://www.qcc.com/web/elib/newcompany",
        "accept-encoding": "gzip, deflate, br",
        "accept-language": "zh-CN,zh;q=0.9",
        "cookie": "",
    }

    url_base = 'https://www.qcc.com/'

    conf = QCC_BASE_DIR + '/qcc.conf'

    def __init__(self):
        self.username = ''
        self.password = ''
        self.session = requests.session()
        self.result_list = []
        self.gz = ''
        self.success = False

    def init_conf(self):
        with open(self.conf, 'r')as f:
            token = f.read()
        lines = token.split('\n')
        self.username = lines[1]
        self.password = lines[3]
        self.headers['cookie'] = lines[5]
        return self

    @staticmethod
    def to_date(s):
        return dt.to_string(dt.of_seconds(s / 1000), '%Y-%m-%d')

    @staticmethod
    def to_essential_result(corp: dict):
        return {
            'Name': corp['Name'],
            'No': corp['No'],
            'CreditCode': corp['CreditCode'],
            'OperName': corp['OperName'],
            'Status': corp['Status'],
            'StartDate': QCCSpider.to_date(corp['StartDate']),
            'Address': corp['Address'],
            'RegistCapi': corp['RegistCapi'],
            'ContactNumber': corp['ContactNumber'],
            'EconKind': corp['EconKind'],
            'OrgNo': corp['OrgNo'],
            'CountyDesc': corp['CountyDesc'],
            'Industry': corp['Industry']['Industry']
        }

    def to_last_day_established_corp_list(self):
        rand = random.Random()
        url = 'https://www.qcc.com/api/elib/getNewCompany'
        params = {
            'flag': '',
            'industry': '',
            'isSortAsc': 'false',
            'pageIndex': '1',
            'pageSize': '20',
            'province': 'SH',
            'sortField': 'startdate',
            'startDateBegin': '',
            'startDateEnd': ''
        }
        r = requests.get(url=url, headers=self.headers, params=params)
        if r.status_code == 200:
            # print(r.json()['Paging'])
            if r.json()['Status'] == 200:
                total = r.json()['Paging']['TotalRecords']
            else:
                return self
        else:
            return self

        page_count = total // 20 + 1

        for i in range(page_count + 1)[1:]:
            bar.show(i / page_count)
            params['pageIndex'] = str(i)
            r = requests.get(url=url, headers=self.headers, params=params)
            if r.status_code == 200:
                corp_list = r.json()['Result']
                for corp in corp_list:
                    self.result_list.append(QCCSpider.to_essential_result(corp))
                time.sleep(rand.randint(1, 3))

        return self

    def serialize(self):
        yesterday = dt.to_string(dt.to_yesterday(), "%Y%m%d")
        data_file_name = files.to_data_file(APP_NAME, 'CORP_INFO', '1G', yesterday)
        data_file_path = files.to_data_path(dir, data_file_name)
        gz, _ = files.ready_to_ship(data_file_path, self.result_list)
        self.gz = gz
        return self

    def ship_to_intranet(self):
        channel_api.transmit(self.gz)
        return self

    def invoke(self):
        try:
            self.init_conf() \
                .to_last_day_established_corp_list() \
                .serialize() \
                .ship_to_intranet()
            return True
        except Exception as e:
            print(str(e))
            return False

    def invoke_util_success(self):
        count = 1
        while True:
            logger.info('do routine work {0} times'.format(str(count)))
            if self.invoke():
                break
            else:
                time.sleep(60)
                count = count + 1
                if count >= 5 :
                    channel_api.sms()
                self.invoke()
