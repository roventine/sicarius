import binascii
import hashlib
import requests

from constant import APP_NAME
from util.logger import logger

APP_KEY = binascii.b2a_base64(APP_NAME.encode())
URL_DATA_CHANNEL = 'https://dapp.sh.abchina.com/nullius/api/v1/datachannel/'
MEM = 'On the word of no one'
SIGNATURE = hashlib.sha256('{0}{1}'.format(MEM, APP_KEY).encode()).hexdigest()


def ship(f):
    """
    传输一个文件至内网
    :param f: 文件路径 e.g. /opt/09-SICARIUS-TAKE_OR_LEAVE-20771231.gz
    :return: {'success': True/False,'message':'错误原因'}
    """
    result = {
        'success': False,
        'message': ''
    }
    try:
        url_file = URL_DATA_CHANNEL + 'file'
        logger.info('{0} -> {1}'.format(url_file, f))
        file = {'file': open(f, 'rb')}
        data = {
            'sign': SIGNATURE
        }
        r = requests.post(url_file, files=file, data=data)
        logger.info('{0} -> {1} -> {2}'.format(url_file, f, r.status_code))
        if r.status_code == 200:
            result['success'] = True

    except Exception as e:
        logger.error(e)
        result['message'] = str(e)

    return result


def sms(mobile, short_message):
    """
    发送短信
    :param mobile: 手机号 e.g. 135********
    :param short_message: 短信内容 e.g. Meet you under the star light of Arctic)
    :return: {'success': True/False,'message':'错误原因'}
    """
    result = {
        'success': False,
        'message': ''
    }
    try:
        url_sms = URL_DATA_CHANNEL + 'sms'
        logger.info('{0} -> {1}:{2}'.format(url_sms,
                                            mobile,
                                            short_message))
        data = {
            'mobile': mobile,
            'message': short_message,
            'sign': SIGNATURE
        }
        r = requests.post(url_sms, data=data)
        logger.info('{0} -> {1}:{2} -> {3}'.format(url_sms,
                                                   mobile,
                                                   short_message,
                                                   r.status_code))
        if r.status_code == 200:
            result['success'] = True

    except Exception as e:
        logger.error(e)
        result['message'] = str(e)

    return result


def notes(mail_to,
          mail_from,
          carbon_copy,
          blind_carbon_copy,
          title,
          context,
          attachment):

    """
    发送notes
    :param mail_to: 收件人列表 e.g. [aaa@abchina.com,zzz@abchina.com]
    :param mail_from: 发件人 e.g. do-not-reply@abchina.com
    :param carbon_copy: 抄送人列表 e.g. [aaa@abchina.com,zzz@abchina.com]
    :param blind_carbon_copy: 密送人列表 e.g. [aaa@abchina.com,zzz@abchina.com]
    :param title: 邮件标题 e.g. You won't miss this
    :param context: 邮件内容 e.g. You failed me yet again,star-scream
    :param attachment: 附件 e.g. /opt/1.zip
    :return: {'success': True/False,'message':'错误原因'}
    """
    result = {
        'success': False,
        'message': ''
    }
    try:
        url_notes = URL_DATA_CHANNEL + 'notes'
        logger.info('{0} -> {1}'.format(url_notes, mail_to, title))
        data = {
            'mailTo': mail_to,
            'mailFrom': mail_from,
            'carbonCopy': carbon_copy,
            'blindCarbonCopy': blind_carbon_copy,
            'title': title,
            'context': context
        }
        if attachment is not None and attachment != '':
            file = {'file': open(attachment, 'rb')}
            r = requests.post(url_notes, data=data, files=file)
        else:
            r = requests.post(url_notes, data=data)

        logger.info('{0} -> {1}:{2} -> {3}'.format(url_notes, mail_to, title, r.status_code))
        if r.status_code == 200:
            result['success'] = True

    except Exception as e:
        logger.error(e)
        result['message'] = str(e)

    return result
