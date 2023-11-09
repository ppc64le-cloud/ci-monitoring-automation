import json
from bs4 import BeautifulSoup
import urllib3
import monitor
import subprocess

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

with open('config.json') as config_file:
    config_data = json.load(config_file)


def new_main(config_data):
    if config_data["info_type"] == "True":
        monitor.get_brief_job_info(config_data)
    elif config_data["info_type"] == False:
        print("Need to develop functions to get detailed information")

new_main(config_data)
