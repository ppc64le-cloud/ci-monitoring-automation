from tabulate import tabulate
import re
from datetime import datetime
import monitor
import configparser
import argparse

config_vars = configparser.ConfigParser()
config_vars.read('config.ini')

JENKINS = config_vars.get('Settings', 'JENKINS')

def get_nightly_name():
    if JENKINS == "False":
        nightly = input("Enter the name of nightly image: ")
        return nightly
    elif JENKINS == "True":
        nightly = config_vars.get('Settings', 'nightly')
        return nightly

def get_job_name():

    '''
    Gets selected CI input.

    Returns:
        dict: Dictionary of selected job name and job link 
    '''

    parser = argparse.ArgumentParser(description='Get the job history')
    parser.add_argument('--job_type', default='p', choices=['p','z','pa'], help= 'Specify the CI job type (Power(p) or s390x(z) or Power Auxillary(pa)), default is p')

    args = parser.parse_args()

    if args.job_type == 'p':
        config_file = 'p_periodic.json'
    elif args.job_type == 'z':
        config_file = 'z_periodic.json'
    elif args.job_type == 'pa':
        config_file = 'p_auxillary.json'
    
    monitor.PROW_URL = monitor.set_prow_url(args.job_type)
    config_data = monitor.load_config(config_file)

    j=0
    ci_name_list = []
    options_int_list = []
    selected_config_data = {}

    if JENKINS == "False":
        for ci_name in config_data.keys():
            j=j+1
            ci_name_list.append(ci_name)
            print(j,'',ci_name)
        option = input("Select the required ci's serial number with a space ")
        selected_options = option.split()
        for ci in selected_options:
            try:
                ci_to_int = int(ci)
                if 0 < ci_to_int <= len(config_data):
                    options_int_list.append(ci_to_int)
                else:
                    return_value = "Enter the options in range of 1 to " + str(len(config_data)+1)
                    print(return_value)
                    return "ERROR"
            except ValueError:
                return "Enter valid options"
    elif JENKINS == "True":
        for ci_name in config_data.keys():
            j=j+1
            ci_name_list.append(ci_name)
   
        selected_ci = config_vars.get('Settings', 'selected_ci')
        options_int_list = [int(value) for value in selected_ci.split(',')]

    for i in options_int_list:
        config_temp_data = {ci_name_list[i-1]: config_data[ci_name_list[i-1]]}
        selected_config_data.update(config_temp_data)
        config_temp_data = {}

    return selected_config_data


def get_builds_with_same_nightly(job_name,nightly_image):
    builds=[]
    agg_builds = []
    pattern = r'\d{4}-\d{2}-\d{2}'
    match = re.search(pattern,nightly_image)
    
    if match != None:
        date_str = match.group()
        nightly_date = datetime.strptime(date_str,"%Y-%m-%d").date()
        current_date = datetime.now().date()
        builds=monitor.get_jobs_with_date(job_name,current_date,nightly_date)
        for spylink in reversed(builds):
            ng = ""
            _, ng = monitor.get_quota_and_nightly(spylink)
            pattern_1 = r'\d{4}-\d{2}-\d{2}'
            match_1 = re.search(pattern_1,ng)
            if match_1 != None:
                date_str_1 = match_1.group()
                ng_date = datetime.strptime(date_str_1,"%Y-%m-%d").date()
                if ng_date > nightly_date:
                    break
                else:
                    if nightly_image in ng:
                        agg_builds.append(spylink)
            else:
                continue
        return agg_builds

def main():
    nightly_image = get_nightly_name()
    selected_jobs = get_job_name()
    print("****************************************")
    print("Payload: ",nightly_image)
    print("****************************************")
    for job_name,job_link in selected_jobs.items():
        build_list = []
        build_list = get_builds_with_same_nightly(job_link,nightly_image)
        monitor.get_detailed_job_info(build_list,job_name)

if __name__ == "__main__":
    main()
