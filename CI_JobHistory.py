from bs4 import BeautifulSoup
import urllib3
import re
import json
from datetime import datetime
import monitor

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

with open('config.json') as config_file:
    config_data = json.load(config_file)


def get_date_input():
    date_str_1 = input("Enter start date (YYYY-MM-DD): ") #example  2023-11-14
    date_str_2 = input("Enter end date (YYYY-MM-DD): ")  #example  2023-11-13
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

def display_ci_links(config_data):
    j=0

    for ci_name in config_data["prow_ci_names"]:
        j=j+1
        print(j,'',ci_name)

    option = input("Select the required ci's serial number with a space ")
    selected_options = option.split()
    options_int_list = []
    selected_config_data = {}
    selected_ci_names = []
    selected_ci_links = []
    for ci in selected_options:
        try:
            ci_to_int = int(ci)
            if 0 < ci_to_int <= len(config_data["prow_ci_links"]):
                options_int_list.append(ci_to_int)
            else:
                return "Enter the options in range of 1 to 10"
        except ValueError:
            return "Enter valid options"

    for i in options_int_list:
        selected_ci_names.append(config_data["prow_ci_names"][i-1])
        selected_ci_links.append(config_data["prow_ci_links"][i-1])
        selected_config_data={"prow_ci_names": selected_ci_names, "prow_ci_links":selected_ci_links}
    
    print(selected_config_data)
    return selected_config_data


def temp_main(config_data):
    ci_list = display_ci_links(config_data)
    start_date,end_date = get_date_input()

    print(ci_list)
    print("Please select one of the option from Job History functionalities: ")
    print("1. Node Status")
    print("2. Brief Job information")
    option = input("Enter the option: ")
    
    if option == '1':
        j=0
        for ci in ci_list["prow_ci_links"]:
            print("-------------------------------------------------------------------------------------------------")
            print(ci_list["prow_ci_names"][j])
            spy_links = monitor.get_jobs_with_date(ci,start_date,end_date)
            check_for_node_crashes(spy_links)
            j=j+1
    if option == '2':
        j=0
        for i in ci_list["prow_ci_links"]:
            monitor.get_brief_job_info(ci_list["prow_ci_links"][j],ci_list["prow_ci_names"][j],start_date,end_date)
            monitor.final_job_list = []
            j=j+1

temp_main(config_data)
