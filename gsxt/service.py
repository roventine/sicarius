import time
import json
from multiprocessing import Process
from multiprocessing import Queue
from random import Random

from util.logger import logger
from gsxt import license
from gsxt import notifier


class Stalker(object):

    def __init__(self, id_uni: str):
        self.id_uni = id_uni
        self.result = {}

    def invoke(self):
        result = license.to_license_info(self.id_uni)
        self.result = result
        return self

    def notify(self):
        logger.info(self.result)
        notify_resp = notifier.notify(json.dumps(self.result, ensure_ascii=True))
        logger.info('{0} -> {1}'.format(self.id_uni, notify_resp))


class TaskConsumer(Process):

    def __init__(self,
                 name: str,
                 queue: Queue):
        Process.__init__(self)
        logger.info('{0} started'.format(name))
        self.name = name
        self.queue = queue

    def run(self):
        rand = Random()
        while 1:
            task = self.queue.get()
            if task:
                logger.info('{0} --> {1}'.format(self.name, task))
                Stalker(task).invoke().notify()
                time.sleep(rand.randint(1, 10))


queue = Queue()
workers = []


def invoke():
    name = 'TaskConsumer'
    workers.append(TaskConsumer(name, queue))

    for worker in workers:
        worker.start()

    # for worker in workers:
    #     worker.join()


def offer(id_uni: str):
    result = {'success': False, 'msg': ''}
    try:
        queue.put(id_uni, block=True, timeout=5)
        result['success'] = True
    except Exception as e:
        logger.error(e)
        result['msg'] = e
    return result
