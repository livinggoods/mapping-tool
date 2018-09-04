import rq
import time


def example_task(seconds = 2000):
    job = rq.get_current_job()
    print('Starting task')
    for i in range(seconds):
        job.meta['progress'] = 100.0 * i / seconds
        job.save_meta()
        print i
        time.sleep(1)
    job.meta['progress'] = 100
    job.save_meta()
    print('Task completed')