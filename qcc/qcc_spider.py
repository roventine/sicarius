import binascii
import hashlib
import os
import sys
import time

import random
import requests

import util.files as files
import util.datetimes as dt
import util.data_channel_api as channel_api

APP_NAME = 'SICARIUS'
dir = os.path.dirname(os.path.abspath(__file__)) + '/data/'


def show_progress_bar(percent):
    percent_str = "%.2f%%" % (percent * 100)
    n = round(percent * 50)
    s = ('#' * n).ljust(50, '-')
    f = sys.stdout
    f.write(percent_str.ljust(8, ' ') + '[' + s + ']')
    f.flush()
    f.write('\r')


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

    conf = os.path.dirname(__file__) + '/qcc.conf'

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

    def keep_me_alive(self):
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
        while True:
            r = requests.get(url=url, headers=self.headers, params=params)
            if r.status_code == 200:
                if r.text.find('Paging') > 0:
                    sleep_secs = rand.randint(1, 10) * 10 * 60
                    print('still alive , sleep {0} seconds'.format(str(sleep_secs)))
                    time.sleep(sleep_secs)
                else:
                    break
            else:
                print(' keep-me-alive error - > {0}'.format(r.status_code))
                break

    @staticmethod
    def to_date(secs):
        return time.strftime('%Y-%m-%d', time.localtime(secs))

    @staticmethod
    def to_essential_result(corp: dict):
        return {
            'Name': corp['Name'],
            'No': corp['No'],
            'CreditCode': corp['CreditCode'],
            'OperName': corp['OperName'],
            'Status': corp['Status'],
            'StartDate': QCCSpider.to_date(corp['StartDate'] / 1000),
            'Address': corp['Address'],
            'RegistCapi': corp['RegistCapi'],
            'ContactNumber': corp['ContactNumber'],
            'EconKind': corp['EconKind'],
            'OrgNo': corp['OrgNo'],
            'CountyDesc': corp['CountyDesc'],
            'Industry': corp['Industry']['Industry']
        }

    def to_last_day_establish_corp_list(self):
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
            show_progress_bar(i / page_count)
            params['pageIndex'] = str(i)
            r = requests.get(url=url, headers=self.headers, params=params)
            if r.status_code == 200:
                corp_list = r.json()['Result']
                for corp in corp_list:
                    self.result_list.append(QCCSpider.to_essential_result(corp))
                time.sleep(rand.randint(1, 3))

        return self

    def get_ready_to_ship(self):
        yesterday = dt.to_string(dt.to_yesterday(), "%Y%m%d")
        data_file_name = files.to_data_file(APP_NAME, 'CORP_INFO', '1G', yesterday)
        data_file_path = files.to_data_path(dir, data_file_name)
        gz, _ = files.ready_to_ship(data_file_path, self.result_list)
        self.gz = gz
        return self

    def ship_to_intranet(self):
        channel_api.transmit(self.gz)
        return self

    def work_once(self):
        try:
            self.init_conf() \
                .to_last_day_establish_corp_list() \
                .get_ready_to_ship() \
                .ship_to_intranet()
            return True
        except Exception as e:
            print(str(e))
            return False

    def routine_work(self):
        count = 1
        while True:
            print('do routine work {0} times'.format(str(count)))
            if self.work_once():
                break
            else:
                time.sleep(60)
                count = count + 1
                self.work_once()



