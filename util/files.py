import gzip
import util.datetimes as dt
import os


def to_data_file(a, f, t,d):
    return '{}-{}-{}-{}-{}'.format('09',
                                   a,
                                   f,
                                   t,
                                   d)


def to_data_path(p, f):
    return '{0}/{1}'.format(p, f)


def to_ctl_path(gz):
    return '{0}.{1}'.format(gz, 'ctl')


def touch_ctl(gz):
    ctl = to_ctl_path(gz)
    with open(ctl, mode='wb'):
        return ctl


def to_gz_path(data):
    return '{0}.{1}'.format(data, 'gz')


def to_gz(data):
    g = to_gz_path(data)
    with gzip.GzipFile(filename='', mode='wb', compresslevel=9, fileobj=open(g, 'wb')) as gz:
        gz.write(open(data, encoding='utf-8').read().encode())
    return g


def to_line(json):
    line = []
    if isinstance(json, dict):
        for key in json:
            line.append(str(json[key]).strip())
    return '|!'.join(line)


def to_data(f, jsons):
    with open(f, mode='wb') as d:
        for j in jsons:
            d.write(to_line(j).encode())
            d.write('\n'.encode())
    return f


def ready_to_ship(f, jsons):
    data = to_data(f, jsons)
    gz = to_gz(data)
    ctl = touch_ctl(gz)
    return [gz, ctl]


def to_data_date(f):
    return dt.to_date(str(f).split('-')[3],'%Y%m%d')


def to_matched_list(days):
    matched_files = []
    files = os.listdir('data')
    for file in files:
        data_date = to_data_date(file)
        if dt.to_days_diff(data_date,dt.to_now())>=days:
            matched_files.append(file)


def delete_file(f):
    return os.remove(f)