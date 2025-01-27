import os

from apscheduler.schedulers.background import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from decouple import config

from venmo_auto_cashout import run_cli

HEARTBEAT_URL = config("HEARTBEAT_URL", default=None)

def handle_click_exit(func):
    def wrapper(*args, **kwargs):
        try:
            func(*args, **kwargs)
        except SystemExit as e:
            if e.code != 0:
                raise

    return wrapper


def job():
    handle_click_exit(run_cli)()

    if HEARTBEAT_URL:
        import requests
        
        try:
            requests.get(HEARTBEAT_URL)
        except requests.exceptions.RequestException:
            pass
        


def cron():
    schedule = os.environ.get("SCHEDULE", "0 6 * * *")
    print(f"Running on schedule: {schedule}")

    scheduler = BlockingScheduler()
    scheduler.add_job(job, CronTrigger.from_crontab(schedule))
    scheduler.start()


if __name__ == "__main__":
    cron()
