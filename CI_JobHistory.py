from bs4 import BeautifulSoup
import urllib3
import re
from datetime import datetime
import monitor

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def get_date_input():
    date_str_1 = input("Enter start date (YYYY-MM-DD): ")
    date_str_2 = input("Enter end date (YYYY-MM-DD): ")
    try:
        start_date = datetime.strptime(date_str_1,"%Y-%m-%d")
        end_date = datetime.strptime(date_str_2,"%Y-%m-%d")
        start_date = start_date.date()
        end_date = end_date.date()
        return start_date,end_date
    except ValueError:
        print("Invalid date format")
        return None


def check_for_node_crashes(job_list):
    pattern = r'/(\d+)'
    
    for url in job_list:
        match = re.search(pattern, url)
        job_id = match.group(1)
        cluster_deploy_status = monitor.cluster_deploy_status(url)
        if cluster_deploy_status == 'SUCCESS':
            node_status = monitor.get_node_status(url)
            print(job_id,node_status)
        monitor.check_node_crash(url)


def temp_main():
    ci = input("Enter prow ci url: ")
    start_date,end_date = get_date_input()

    print("Please select one of the option from Job History functionalities: ")
    print("1. Node Status")
    
    option = input("Enter the option: ")

    job_list = monitor.get_jobs_with_date(ci,start_date,end_date)

    if not job_list:
        print("No Jobs run in the given date range")
        return 0
    
    if option == '1':
        check_for_node_crashes(job_list)

temp_main()
