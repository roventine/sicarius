import requests, re, urllib, os, time


class NetDiskShareSavior:
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36',
        'Referer': 'pan.baidu.com'}

    universal_error_code = {'2': '参数错误。检查必填字段；get/post 参数位置',
                            '-6': '身份验证失败。access_token 是否有效；部分接口需要申请对应的网盘权限',
                            '31034': '命中接口频控。核对频控规则;稍后再试;申请单独频控规则',
                            '42000': '访问过于频繁',
                            '42001': 'rand校验失败',
                            '42999': '功能下线',
                            '9100': '一级封禁',
                            '9200': '二级封禁',
                            '9300': '三级封禁',
                            '9400': '四级封禁',
                            '9500': '五级封禁'}

    def __init__(self, api_key, secret_key, share_link, password, dir):
        print(os.path.abspath(__file__))
        self.api_key = api_key
        self.secret_key = secret_key
        self.share_link = share_link
        self.password = password
        self.dir = dir
        self.access_token = ''
        self.refresh_token = ''

        if self.init_token() and self.get_surl() and self.get_sekey() and self.get_shareid_and_uk_and_fsidlist():
            self.file_transfer()

    def apply_for_token(self):
        '''
        获取应用授权的流程：
        先获取授权码code，再通过code得到token(access_token和refresh_token)
        详情参见：https://pan.baidu.com/union/document/entrance#3%E8%8E%B7%E5%8F%96%E6%8E%88%E6%9D%83
        '''

        '''
        获取code
        参数：
        response_type       固定值，值为'code'
        client_id           自己应用的API key
        redirect_uri        授权回调地址。对于无server的应用，可将其值设为'oob'，回调后会返回一个平台提供默认回调地址
        scope               访问权限，即用户的实际授权列表，值为'basic', 'netdisk'二选一，含义分别为基础权限（访问您的个人资料等基础信息），百度网盘访问权限（在您的百度网盘创建文件夹并读写数据）
        display             授权页的展示方式，默认为'page'
        '''
        get_code_url = 'https://openapi.baidu.com/oauth/2.0/authorize?response_type=code&client_id={}&redirect_uri=oob&scope=netdisk'.format(
            self.api_key)
        code = input('请访问下面的链接：\n%s\n登录百度账号，并将授权码粘贴至此处，然后回车，完成授权：\n' % get_code_url)

        '''
        通过code，获取token
        参数：
        grant_type          固定值，值为'authorization_code'
        code                上一步得到的授权码
        client_id           应用的API KEY
        client_secret       应用的SECRET KEY
        redirect_uri        和上一步的redirect_uri相同
        '''
        get_token_url = 'https://openapi.baidu.com/oauth/2.0/token?grant_type=authorization_code'
        params = {'code': code, 'client_id': api_key, 'client_secret': secret_key, 'redirect_uri': 'oob'}
        res = requests.get(get_token_url, headers=self.headers, params=params)

        try:
            res_json = res.json()
        except Exception as e:
            print('请检查网络是否连通：%s' % e)
            return False

        if 'error' in res_json:
            error = res_json['error']
            print('获取token失败：%s' % error)
            return False
        elif 'access_token' in res_json and 'refresh_token' in res_json:
            self.access_token = res_json['access_token']
            self.refresh_token = res_json['refresh_token']
            return True

    def regain_token(self):
        '''
        使用refresh_token，刷新token。
        '''
        refresh_token = 'https://openapi.baidu.com/oauth/2.0/token?grant_type=refresh_token'
        # params = {'code': code, 'client_id': api_key, 'client_secret': secret_key, 'redirect_uri': 'oob'}
        params = {'refresh_token': self.refresh_token, 'client_id': self.api_key, 'client_secret': self.secret_key}
        res = requests.get(refresh_token, headers=self.headers, params=params)

        try:
            res_json = res.json()
        except Exception as e:
            print('请检查网络是否连通：%s' % e)
            return False

        if 'error' in res_json:
            error = res_json['error']
            print('刷新token失败：%s' % error)
            return False
        elif 'access_token' in res_json and 'refresh_token' in res_json:
            self.access_token = res_json['access_token']
            self.refresh_token = res_json['refresh_token']
            return True

    def init_token(self):
        '''
        如果存在配置文件且token存在时间少于27天，则直接从配置文件中读入token；
        如果存在配置文件且token存在时间超过10个平年，则重新申请token；
        如果存在配置文件且token存在时间大于27天，少于10个平年，则刷新token；
        如果不存在配置文件，则申请token。
        access_token的有效期是一个月，refresh_token的有效期是十年，access_token过期后，使用refresh_token刷新token即可
        '''
        work_dir = os.path.dirname(os.path.abspath(__file__))
        conf = os.path.join(work_dir, 'netdisk.conf')

        if os.path.exists(conf):  # 存在配置文件
            with open(conf, 'r')as f:
                token = f.read()
            lines = token.split('\n')
            update_time = int(lines[5])
            now_time = int(time.time())

            if now_time - update_time < 27 * 24 * 60 * 60:  # token存在时间少于27天，则直接从配置文件中读入token
                self.access_token = lines[1]
                self.refresh_token = lines[3]
                print('已从配置文件中读入token')
                return True
            elif now_time - update_time > 31536000 * 10:  # token存在时间超过10个平年，则重新申请token（10年后百度网盘还能不能用都不好说）
                self.apply_for_token()
                token = '[access_token]\n{}\n[refresh_token]\n{}\n[update_time]\n{}'.format(self.access_token,
                                                                                            self.refresh_token,
                                                                                            int(time.time()))
                with open(conf, 'w')as f:
                    f.write(token)
                print('已重新申请token并将token写入配置文件中')
            else:  # token存在时间大于27天，少于10个平年，则刷新token
                self.refresh_token = lines[3]
                self.regain_token()
                token = '[access_token]\n{}\n[refresh_token]\n{}\n[update_time]\n{}'.format(self.access_token,
                                                                                            self.refresh_token,
                                                                                            int(time.time()))
                with open(conf, 'w')as f:
                    f.write(token)
                print('已刷新token并将token写入配置文件中')
                return True
        else:  # 未找到配置文件
            self.apply_for_token()
            token = '[access_token]\n{}\n[refresh_token]\n{}\n[update_time]\n{}'.format(self.access_token,
                                                                                        self.refresh_token,
                                                                                        int(time.time()))
            with open(conf, 'w')as f:
                f.write(token)
            print('已申请token并将token写入配置文件中')

        print('asscee_token:', self.access_token)
        print('refresh_token:', self.refresh_token)
        return True

    def get_surl(self):
        '''
        获取surl。举个例子：
        short_link: https://pan.baidu.com/s/1LGDt_UQfdyQ9ga04bsnLKg
        long_link: https://pan.baidu.com/share/init?surl=LGDt_UQfdyQ9ga04bsnLKg
        surl: LGDt_UQfdyQ9ga04bsnLKg
        '''
        res = re.search(r'https://pan\.baidu\.com/share/init\?surl=([0-9a-zA-Z].+?)$', self.share_link)
        if res:
            print('long_link:', self.share_link)

            self.surl = res.group(1)
            print('surl:', self.surl)
            return True
        else:
            print('short_link:', self.share_link)

            res = requests.get(self.share_link, headers=self.headers)
            reditList = res.history
            if(len(reditList)>0):
                link = reditList[len(reditList) - 1].headers["location"]  # 302跳转的最后一跳的url
                print('long_link:', link)
            else:
                print('获取long_link失败')
                return False

            res = re.search(r'https://pan\.baidu\.com/share/init\?surl=([0-9a-zA-Z].+?)$', link)
            if res:
                self.surl = res.group(1)
                print('surl:', self.surl)
                return True
            else:
                print('获取surl失败')
                return False

    def get_sekey(self):
        '''
        验证提取码是否正确，如果正确，得到一个与提取码有关的密钥串randsk(即后面获取文件目录信息和转存文件时需要用到的sekey)
        详情参见：https://pan.baidu.com/union/document/openLink#%E9%99%84%E4%BB%B6%E5%AF%86%E7%A0%81%E9%AA%8C%E8%AF%81
        '''
        url = 'https://pan.baidu.com/rest/2.0/xpan/share?method=verify'
        params = {'surl': self.surl}
        data = {'pwd': self.password}
        res = requests.post(url, headers=self.headers, params=params, data=data)

        res_json = res.json()
        errno = res_json['errno']
        if errno == 0:
            randsk = res_json['randsk']
            self.sekey = urllib.parse.unquote(randsk, encoding='utf-8',
                                              errors='replace')  # 需要urldecode一下，不然%25会再次编码成%2525
            print('sekey:', self.sekey)
            return True
        else:
            error = {'105': '链接地址错误',
                     '-12': '非会员用户达到转存文件数目上限',
                     '-9': 'pwd错误',
                     '2': '参数错误,或者判断是否有referer'}
            error.update(self.universal_error_code)

            if str(errno) in error:
                print('获取sekey失败，错误码：{}，错误：{}'.format(errno, error[str(errno)]))
            else:
                print(
                    '获取sekey失败，错误码：{}，错误未知，请尝试查询https://pan.baidu.com/union/document/error#%E9%94%99%E8%AF%AF%E7%A0%81%E5%88%97%E8%A1%A8'.format(
                        errno))

            return False

            # 提取码不是4位的时候，返回的errno是-12，含义是非会员用户达到转存文件数目上限，这是百度网盘的后端代码逻辑不正确，我也没办法。不过你闲的没事输入长度不是4位的提取码干嘛？

    def get_shareid_and_uk_and_fsidlist(self):
        '''
        获取附件中的文件id列表，同时也会含有shareid和uk(userkey)
        详情参见：https://pan.baidu.com/union/document/openLink#%E8%8E%B7%E5%8F%96%E9%99%84%E4%BB%B6%E4%B8%AD%E7%9A%84%E6%96%87%E4%BB%B6%E5%88%97%E8%A1%A8
        shareid+uk和shorturl这两组参数只需要选择一组传入即可，这里我们不知道shareid和uk，所以传入shorturl，来获取文件列表信息和shareid和uk。
        参数：
        shareid             分享链接id
        uk                  分享用户id（userkey）
        shorturl            分享链接地址（就是前面提取出来的surl，如9PsW5sWFLdbR7eHZbnHelw，不是整个的绝对路径）
        page                数据量大时，需分页
        num                 每页个数，默认100
        root                为1时，表示显示链接根目录下所有文件
        fid                 文件夹ID，表示显示文件夹下的所有文件
        sekey               附件链接密钥串，对应verify接口返回的randsk
        '''
        url = 'https://pan.baidu.com/rest/2.0/xpan/share?method=list'
        params = {"shorturl": self.surl, "page": "1", "num": "100", "root": "1", "fid": "0", "sekey": self.sekey}
        res = requests.get(url, headers=self.headers, params=params)

        res_json = res.json()
        errno = res_json['errno']
        if errno == 0:
            self.shareid = res_json['share_id']
            print('shareid:', self.shareid)

            self.uk = res_json['uk']
            print('uk:', self.uk)

            fsidlist = res_json['list']
            self.fsid_list = []
            for fs in fsidlist:
                self.fsid_list.append(int(fs['fs_id']))
            print('fsidlist:', self.fsid_list)

            return True
        else:
            error = {'110': '有其他转存任务在进行',
                     '105': '非会员用户达到转存文件数目上限',
                     '-7': '达到高级会员转存上限'}
            error.update(self.universal_error_code)

            if str(errno) in error:
                print('获取shareid, uk, fsidlist失败，错误码：{}，错误：{}'.format(errno, error[str(errno)]))
            else:
                print(
                    '获取shareid, uk, fsidlist失败，错误码：{}，错误未知，请尝试查询https://pan.baidu.com/union/document/error#%E9%94%99%E8%AF%AF%E7%A0%81%E5%88%97%E8%A1%A8'.format(
                        errno))

            return False

    def file_transfer(self):
        '''
        附件文件转存
        详情参见：https://pan.baidu.com/union/document/openLink#%E9%99%84%E4%BB%B6%E6%96%87%E4%BB%B6%E8%BD%AC%E5%AD%98
        不过上面链接中的参数信息好像有些不太对，里面的示例的用法是对的。
        GET参数：
        access_token        前面拿到的access_token
        shareid             分享链接id
        from                分享用户id（userkey）
        POST参数：
        sekey               附件链接密钥串，对应verify接口返回的randsk
        fsidlist            文件id列表，形如[557084550688759]，[557084550688759, 557084550688788]
        path                转存路径
        '''
        url = 'http://pan.baidu.com/rest/2.0/xpan/share?method=transfer'
        params = {'access_token': self.access_token, 'shareid': self.shareid, 'from': self.uk, }
        data = {'sekey': self.sekey, 'fsidlist': str(self.fsid_list), 'path': self.dir}
        res = requests.post(url, headers=self.headers, params=params, data=data)

        res_json = res.json()
        errno = res_json['errno']
        if errno == 0:
            print('文件转存成功')
            return True
        else:
            error = {'111': '有其他转存任务在进行',
                     '120': '非会员用户达到转存文件数目上限',
                     '130': '达到高级会员转存上限',
                     '-33': '达到转存文件数目上限',
                     '12': '批量操作失败',
                     '-3': '转存文件不存在',
                     '-9': '密码错误',
                     '5': '分享文件夹等禁止文件'}
            error.update(self.universal_error_code)

            if str(errno) in error:
                print('文件转存失败，错误码：{}，错误：{}\n返回JSON：{}'.format(errno, error[str(errno)], res_json))
            else:
                print(
                    '文件转存失败，错误码：{}，错误未知，请尝试查询https://pan.baidu.com/union/document/error#%E9%94%99%E8%AF%AF%E7%A0%81%E5%88%97%E8%A1%A8\n返回JSON：{}'.format(
                        errno, res_json))

            return False

        # 转存路径不存在时返回errno=2, 参数错误，如：{"errno":2,"request_id":5234720642281834903}
        # 自己转存自己分享的文件时返回errno=12，批量操作失败，如：{"errno":12,"task_id":0,"info":[{"path":"\/asm","errno":4,"fsid":95531336671296}]}
        # 转存成功后再次转存到同一文件夹下时返回errno=12，批量操作失败，如：{"errno":12,"task_id":0,"info":[{"path":"\/doax","errno":-30,"fsid":557084550688759}]}


if __name__ == '__main__':
    api_key = 'ldERCi3W8reD1m18tuI8iaQPxc2ybD64'  # 按照https://pan.baidu.com/union/document/entrance#%E7%AE%80%E4%BB%8B 的指引，申请api_key和secret_key。
    secret_key = 'fYHo0G6ctK6KEnnfgE4WIu107zkqVgpK'  # 这里默认是我申请的api_key和secret_key，代号sicarius
    share_link = 'https://pan.baidu.com/s/1LGDt_UQfdyQ9ga04bsnLKg'  # 分享链接
    # share_link = 'https://pan.baidu.com/share/init?surl=9PsW5sWFLdbR7eHZbnHelw'    # 分享链接，以上两种形式的链接都可以
    password = 'w1yd'  # 分享提取码
    dir = '/sample'  # 转存路径，根路径为/，记得提前在百度网盘内创建好目标转存目录
    NetDiskShareSavior(api_key, secret_key, share_link, password, dir)
