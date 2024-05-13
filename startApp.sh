#!/bin/bash

screen -S resumechat

#gunicorn --workers 3 --threads 4 --config gunicorn_settings.py --worker-class gevent resumechat:app 2>> '/home/wolframdonat/chat_log.txt'

gunicorn --workers 2 --config gunicorn_settings.py --worker-class gevent resumechat:app 2>> '/home/wolframdonat/chat_log.txt'

