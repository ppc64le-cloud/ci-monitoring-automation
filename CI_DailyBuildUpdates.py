import json
from bs4 import BeautifulSoup
import urllib3
import monitor
import argparse

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

with open('config.json') as config_file:
    config_data = json.load(config_file)


def new_main(config_data):
    parser = argparse.ArgumentParser(description='Specifies if user needs brief/detailed job information')
    parser.add_argument('--info_type', default='brief', help='specify the job info type')
    args = parser.parse_args()
    if args.info_type == "brief":
        for ci_name,ci_link in config_data.items():
            monitor.get_brief_job_info(ci_name,ci_link)
    elif args.info_type == "detailed":
        for ci_name,ci_link in config_data.items():
            monitor.get_detailed_job_info(ci_name,ci_link)

new_main(config_data)
