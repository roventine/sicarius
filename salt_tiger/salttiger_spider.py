import requests, os, re
from lxml import etree
from baidu_netdisk.open_api import NetDiskShareSavior


class SaltTigerSpider():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36',
        'Referer': 'https://salttiger.com/'
    }

    url_base = 'https://salttiger.com/'

    conf = r'salt_tiger.conf'

    def __init__(self):
        self.last_page_count = 0
        self.last_archive = ''
        self.current_page_count = 0
        self.current_start_archive = ''

        self.init_conf()

    def init_conf(self):
        with open(self.conf, 'r')as f:
            token = f.read()
        lines = token.split('\n')
        self.last_page_count = int(lines[0])
        self.last_archive = lines[1]
        return self

    def init_task_list(self):
        r = requests.get(url=self.url_base, headers=self.headers)
        h = etree.HTML(r.text)
        a = h.xpath('//*[@id="nav-below"]/div/a[3]/@href')[0]
        b = h.xpath('//*[@class="entry-title"]/a/text()')
        n = re.search(r'https://salttiger\.com/page/([0-9].+?)/', a)
        if n:
            self.current_page_count = n.group(1)
        if b:
            self.current_start_archive = b[0]
        return self

    def save_conf(self):
        with open(self.conf, 'w')as f:
            f.write(str(self.current_page_count) + '\n')
            f.write(self.current_start_archive + '\n')

    def to_archives(self, i: int):
        url_archives = 'https://salttiger.com/page/{0}/'.format(str(i))
        r = requests.get(url=url_archives, headers=self.headers)
        h = etree.HTML(r.text)
        part_list = h.xpath('//div[@class="entry-content"]/p/strong')
        archives = {}
        for part in part_list:
            a = ','.join(part.xpath('a/@href'))
            t = ','.join(part.xpath('text()'))

            m = re.search(r'https://pan\.baidu\.com/s/(.+?)$', a, re.M | re.I)
            if m:
                url = m.group(0)
                m = re.search(r'^(提取码).*(：\w{4})\b', t, re.M | re.I)
                if m:
                    code = m.group().split('：').pop().strip()
                else:
                    code = ''
                archives[url] = code
        return archives

    def do_task_list(self):
        dir = '/sample/salt_tiger'
        api_key = 'ldERCi3W8reD1m18tuI8iaQPxc2ybD64'
        secret_key = 'fYHo0G6ctK6KEnnfgE4WIu107zkqVgpK'

        page_count = int(self.current_page_count) - self.last_page_count
        for i in range(page_count + 1):
            archives = SaltTigerSpider().to_archives(i)
            for k, v in archives.items():
                NetDiskShareSavior(api_key, secret_key, k, v, dir)
        return self


if __name__ == '__main__':
    SaltTigerSpider().init_conf()\
        .init_task_list()\
        .do_task_list()\
        .save_conf()
