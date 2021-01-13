import schedule
import time
import threading
from qcc.qcc_spider import QCCSpider


class RoutineWorker(threading.Thread):

    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        print('start RoutineWorker')
        schedule.default_scheduler.every() \
            .day \
            .at("10:33:50") \
            .do(QCCSpider().routine_work)

        while True:
            schedule.run_pending()
            time.sleep(1)


class KeepAliveWorker(threading.Thread):

    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        print('start KeepAliveWorker')
        QCCSpider().keep_me_alive()


routine_worker = RoutineWorker()
keep_alive_worker = KeepAliveWorker()
routine_worker.start()
keep_alive_worker.start()
