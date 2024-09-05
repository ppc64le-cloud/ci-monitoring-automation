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
        print(job_list)
        if isinstance(job_list, str):
            print(job_list + " for ", ci_name)
            return updated_ci_dict
        for job in job_list:
            cluster_status=monitor.cluster_deploy_status(job)
            job_type,_=monitor.job_classifier(job)
            if cluster_status == 'SUCCESS':
                _ , failed_tc_count, error_object = monitor.get_all_failed_tc(job,job_type)
                if all(value == None for value in error_object.values()):
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
    parser.add_argument('--builds', type=int, default=10, help='Number of recent builds to check for test failure occurrence. Please provide any value in the range of 2 to 20')
    parser.add_argument('--frequency', type=int, default=3, help='Minimum count of test failure occurrence. Please provide any value in the range of 2 to 20')
    parser.add_argument('--job_type', default='p', choices=['p','z','pa'], help='Specify the CI job type (Power(p) or s390x(z) or Power Auxillary(pa)), default is p')
    args = parser.parse_args()

    if not 2 <= args.builds <= 20:
        parser.error("Number of recent builds to check for testcase failure occurrence must be in the range of 2 to 20")
    else:
        n_build = args.builds
    
    if not 2 <= args.frequency <= 10:
        parser.error("Minimum count of testcase failure occurrence must be in range of 2 to 10")
    else:
        frequency1 = args.frequency
    
    if args.job_type == 'p':
        config_file = 'p_periodic.json'
    elif args.job_type == 'z':
        config_file = 'z_periodic.json'
    elif args.job_type == 'pa':
        config_file = 'p_auxillary.json'
    
    monitor.PROW_URL = monitor.set_prow_url(args.job_type)
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
                print("\n")
            for i in tc_list[1]:
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
                print("\n")
            print("---------------------------------------------------------------------------")
        elif (not flag1) and flag2:
            print(ci_name)
            print("---------------------------------------------------------------------------")
            for i in tc_list[1]:
                match = re.search(pattern_job_id, i)
                job_id = match.group(1)
                print(job_id,"this job has a huge testcase failures please check it")                
            print("---------------------------------------------------------------------------")
            
if __name__ == "__main__":
    main()
