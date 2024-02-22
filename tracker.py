import urllib3
import monitor
import argparse
import re
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def filter_latest_ci_lv1(config_data,n_build):
    updated_ci_dict = {}
    for ci_name,ci_link in config_data.items():
        tc_failure_jobs = []
        huge_tc_failure_jobs = []
        job_list = monitor.get_n_recent_jobs(ci_link,n_build)
        for job in job_list:
            cluster_status=monitor.cluster_deploy_status(job)
            job_type,_=monitor.job_classifier(job)
            if cluster_status == 'SUCCESS':
                _ , failed_tc_count = monitor.get_all_failed_tc(job,job_type)
                if failed_tc_count < 20 and failed_tc_count > 0:
                    tc_failure_jobs.append(job)
                elif failed_tc_count > 20:
                    huge_tc_failure_jobs.append(job)
            final_tc_failure_jobs = [tc_failure_jobs,huge_tc_failure_jobs]
        updated_ci_dict[ci_name] = final_tc_failure_jobs
    return updated_ci_dict

def get_tc_frequency(tc_list,frequency):
    li=monitor.get_testcase_frequency(tc_list)
    filtered_dict = {key: value for key, value in li.items() if value >=frequency }
    return filtered_dict

def main():
    parser = argparse.ArgumentParser(description='Get the daily buid updates')
    parser.add_argument('--ci_arch', default='p', choices=['p','z'], help='Specify the CI architecture type (p or z), default is p')
    parser.add_argument('--latest_build', type=int, default=10, help='Value in range of 3 to 20')
    parser.add_argument('--frequency', type=int, default=3, help='Value in range of 3 to 10')
    args = parser.parse_args()
    if not 3 <= args.latest_build <= 20:
        parser.error("Value in range of 3 to 20")
    else:
        n_build = args.latest_build
    
    if not 2 <= args.frequency <= 10:
        parser.error("Value in range of 2 to 10")
    else:
        frequency1 = args.frequency

    if args.ci_arch == 'p':
        config_file = 'p_config.json'
    elif args.ci_arch == 'z':
        config_file = 'z_config.json'
    else:
        print("Invalid argument. Please use p or z")
        return 1
    config_data = monitor.load_config(config_file)
    updated_ci_dict = filter_latest_ci_lv1(config_data,n_build)
    for ci_name,tc_list in updated_ci_dict.items():
        pattern_job_id =  r'/(\d+)'
        flag1=False
        flag2=False
        if len(tc_list[0]) > 0:
            frequency_tc_list = get_tc_frequency(tc_list[0],frequency1)
            if len(frequency_tc_list) > 0:
                flag1=True

        if len(tc_list[1]) > 0:
            flag2=True
        
        if flag1 and flag2:
            i=0
            print(ci_name)
            print("---------------------------------------------------------------------------")
            for testcase,fail_freq in frequency_tc_list.items():
                i=i+1
                print(i,". ",testcase)
                print("Failed in {}/{} builds".format(fail_freq, n_build))
            for i in range(0,len(tc_list[1])):
                match = re.search(pattern_job_id, i)
                job_id = match.group(1)
                print(job_id, "this job has a huge testcase failures please check it")
            print("---------------------------------------------------------------------------")
        elif flag1 and (not flag2):
            i=0
            print(ci_name)
            print("---------------------------------------------------------------------------")
            for testcase,fail_freq in frequency_tc_list.items():
                i=i+1
                print(i,". ",testcase)
                print("Failed in {}/{} builds".format(fail_freq, n_build))
            print("---------------------------------------------------------------------------")
        elif (not flag1) and flag2:
            print(ci_name)
            print("---------------------------------------------------------------------------")
            for i in range(0,len(tc_list[1])):
                match = re.search(pattern_job_id, i)
                job_id = match.group(1)
                print(job_id, "this job has a huge testcase failures please check it")
            print("---------------------------------------------------------------------------")
            
if __name__ == "__main__":
    main()
