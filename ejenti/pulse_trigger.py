#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
Usage:
  pulse_trigger.py [--config=<str>] [--cmd-config=<str>] [--clean] [--skip-first-query]
  pulse_trigger.py (-h | --help)

Options:
  -h --help                       Show this screen.
  --config=<str>                  Specify the trigger_config.json file path. [default: configs/ejenti/trigger_config.json]
  --cmd-config=<str>              Specify the cmd_config.json file path. [default: configs/ejenti/cmd_config.json]
  --clean                         Clean Pulse Queue on Pulse service. [default: False]
  --skip-first-query              Skip first time query of Perfherder/Archive server. [default: False]
"""

import os
import time
import logging
from docopt import docopt
from apscheduler.schedulers.background import BackgroundScheduler

from lib.common.commonUtil import CommonUtil
from pulse_modules.tasksTrigger import TasksTrigger
from jobs.status_json_creator import status_json_creator


class LogFilter(logging.Filter):
    def filter(self, record):
        return ''


def main():
    """
    Demo of pushing MetaTask to Pulse.
    It will load Pulse config from `--config`, please create the config json file before run this demo.

    The timestamp file of each job will be stored into "ejenti/pulse_modules/.md5/<JOB_NAME>".

    ex:
    {
        "pulse_username": "<PULSE_USERNAME>",
        "pulse_password": "<PULSE_PASSWORD>"
    }

    Also, you can monitor the Pulse Message Queue from https://pulseguardian.mozilla.org/ website.
    """
    default_log_format = '%(asctime)s %(levelname)s [%(name)s.%(funcName)s] %(message)s'
    default_datefmt = '%Y-%m-%d %H:%M'
    logging.basicConfig(level=logging.INFO, format=default_log_format, datefmt=default_datefmt)

    # loading docopt
    arguments = docopt(__doc__)

    # loading config
    config_arg = arguments['--config']
    config_file = os.path.abspath(config_arg)
    config = CommonUtil.load_json_file(config_file)
    if not config:
        logging.error('There is not trigger config. (Loaded from {})'.format(config_file))
        exit(1)

    # filter the logger
    log_filter = LogFilter()
    for disabled_logger in config.get('log_filter', []):
        logging.getLogger(disabled_logger).addFilter(log_filter)

    # loading cmd_config
    cmd_config_arg = arguments['--cmd-config']
    cmd_config_file = os.path.abspath(cmd_config_arg)
    command_config = CommonUtil.load_json_file(cmd_config_file)
    if not command_config:
        logging.error('There is not command config. (Loaded from {})'.format(cmd_config_file))
        exit(1)

    clean_flag = arguments['--clean']
    skip_first_query_flag = arguments['--skip-first-query']

    try:
        trigger = TasksTrigger(config=config, cmd_config_obj=command_config, clean_at_begin=clean_flag)
        trigger.run(skip_first_query=skip_first_query_flag)

        # The `status_json_creator()` method under `ejenti.jobs` package, so `TaskTrigger` is really hard to call it.
        outside_scheduler = BackgroundScheduler()
        outside_scheduler.start()

        # create Status B2 upload job
        KEY_CONFIG_B2_ACCOUNT_ID = 'b2_account_id'
        KEY_CONFIG_B2_ACCOUNT_KEY = 'b2_account_key'
        KEY_CONFIG_B2_BUCKET_NAME = 'b2_upload_bucket_name'
        INTERVAL_MINUTES = 30
        b2_account_id = config.get(KEY_CONFIG_B2_ACCOUNT_ID)
        b2_account_key = config.get(KEY_CONFIG_B2_ACCOUNT_KEY)
        b2_upload_bucket_name = config.get(KEY_CONFIG_B2_BUCKET_NAME)
        if b2_account_id and b2_account_key and b2_upload_bucket_name:
            b2_upload_config = {
                'configs': {
                    'b2_account_id': b2_account_id,
                    'b2_account_key': b2_account_key,
                    'b2_upload_bucket_name': b2_upload_bucket_name
                }
            }
            outside_scheduler.add_job(func=status_json_creator,
                                      trigger='interval',
                                      id='status_b2_uploader',
                                      max_instances=1,
                                      minutes=INTERVAL_MINUTES,
                                      args=[],
                                      kwargs=b2_upload_config)
            logging.info('Enable Status JSON Creator and B2 Uploader.')
        else:
            logging.warn('Please config your B2 Account ID, Key, and Bucket Name to enable Status JSON Creator and B2 Uploader.')

        while True:
            time.sleep(10)
    except Exception as e:
        logging.error(e)
        exit(1)


if __name__ == '__main__':
    main()
