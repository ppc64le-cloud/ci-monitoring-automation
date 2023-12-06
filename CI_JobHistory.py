from bs4 import BeautifulSoup
import urllib3
from tabulate import tabulate
import re
from datetime import datetime
import monitor
import argparse

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def get_date_input():
    date_str_1 = input("Enter Before date (YYYY-MM-DD): ") #example  2023-11-14
    date_str_2 = input("Enter After date (YYYY-MM-DD): ")  #example  2023-11-13
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

def get_failed_testcases(spylinks):
    pattern = r'/(\d+)'
    j=0
    for spylink in spylinks:
        match = re.search(pattern, spylink)
        job_id = match.group(1)
        job_type,_ = monitor.job_classifier(spylink)
        cluster_status=monitor.cluster_deploy_status(spylink)
        if cluster_status == 'SUCCESS' and "4.15" not in spylink:
            j=j+1
            print(str(j)+".",job_id)
            monitor.print_e2e_testcase_failures(spylink,job_type)
            print("\n")
        elif cluster_status == 'SUCCESS' and "4.15" in spylink:
            j=j+1
            print(str(j)+".",job_id)
            monitor.print_e2e_testcase_failures(spylink,job_type)
            monitor.print_monitor_testcase_failures(spylink,job_type)
    print("--------------------------------------------------------------------------------------------------")
    print("\n")

def display_ci_links(config_data):
    j=0

    ci_name_list = []

    for ci_name in config_data.keys():
        j=j+1
        ci_name_list.append(ci_name)
        print(j,'',ci_name)

    option = input("Select the required ci's serial number with a space ")
    selected_options = option.split()
    options_int_list = []
    selected_config_data = {}
   
    for ci in selected_options:
        try:
            ci_to_int = int(ci)
            if 0 < ci_to_int <= len(config_data):
                options_int_list.append(ci_to_int)
            else:
                return_value = "Enter the options in range of 1 to " + str(len(config_data))
                print(return_value)
                return "ERROR"
        except ValueError:
            return "Enter valid options"

    for i in options_int_list:
        config_temp_data = {ci_name_list[i-1]: config_data[ci_name_list[i-1]]}
        selected_config_data.update(config_temp_data)
        config_temp_data = {}
    
    return selected_config_data


def main():

    parser = argparse.ArgumentParser(description='Load JSON configuration file based on command line arguement')
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
    ci_list = display_ci_links(config_data)


    if isinstance(ci_list,dict):
        start_date,end_date = get_date_input()
        
        if start_date != None and end_date != None:
            print("Please select one of the option from Job History functionalities: ")
            print("1. Node Status")
            print("2. Brief Job information")
            print("3. Detailed Job information")
            print("4. Failed testcases")

            option = input("Enter the option: ")

            print("Checking runs from",end_date,"to",start_date)
    
            if option == '1':
                for ci_name,ci_link in ci_list.items():
                    print("-------------------------------------------------------------------------------------------------")
                    print(ci_name)
                    spy_links = monitor.get_jobs_with_date(ci_link,start_date,end_date)
                    check_for_node_crashes(spy_links)
                    monitor.final_job_list = []
            
            if option == '2':
                summary_list = []
                for ci_name,ci_link in ci_list.items():
                    summary_list.extend(monitor.get_brief_job_info(ci_name,ci_link,start_date,end_date))
                    monitor.final_job_list = []
                print(tabulate(summary_list, headers='keys', tablefmt="pipe", stralign='left'))
            
            if option == '3':
                for ci_name,ci_link in ci_list.items():
                    monitor.get_detailed_job_info(ci_name,ci_link,start_date,end_date)
                    monitor.final_job_list = []
            
            if option == '4':
                for ci_name,ci_link in ci_list.items():
                    print("-------------------------------------------------------------------------------------------------")
                    print(ci_name)
                    spy_links = monitor.get_jobs_with_date(ci_link,start_date,end_date)
                    get_failed_testcases(spy_links)
                    monitor.final_job_list = []

if __name__ == "__main__":
    main()
