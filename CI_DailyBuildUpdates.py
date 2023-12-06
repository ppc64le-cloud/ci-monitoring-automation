from bs4 import BeautifulSoup
import urllib3
from tabulate import tabulate
import monitor
import argparse


urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def main():
    parser = argparse.ArgumentParser(description='Load JSON configuration file and specifies if user needs brief/detailed job information')
    parser.add_argument('--info_type', default='brief', help='specify the job info type')
    parser.add_argument('--ci_arch', default='p', choices=['p','z'], help='Specify the CI architecture type (p or z), default is p')
    args = parser.parse_args()
    if args.ci_arch == 'p':
        config_file = 'p_config.json'
    elif args.ci_arch == 'z':
        config_file = 'z_config.json'
    else:
        print("Invalid argument. Please use p or z")
        return
    config_data = monitor.load_config(config_file)
    if args.info_type == "brief":
        summary_list = []
        for ci_name,ci_link in config_data.items():
            summary_list.extend(monitor.get_brief_job_info(ci_name,ci_link))
        print(tabulate(summary_list, headers='keys', tablefmt="pipe", stralign='left'))
    elif args.info_type == "detailed":
        for ci_name,ci_link in config_data.items():
            monitor.get_detailed_job_info(ci_name,ci_link)

if __name__ == "__main__":
    main()
