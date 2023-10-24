import json
import re
from bs4 import BeautifulSoup
import urllib3
import requests
from datetime import datetime


urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

with open('config.json') as config_file:
    config_data = json.load(config_file)

def get_current_date():
    return datetime.now().date()

def parse_job_date(da):
    parse_date=datetime.strptime(da,"%Y-%m-%dT%H:%M:%SZ")
    job_run_date=parse_date.date()
    return job_run_date

def get_jobs(s):
    
    # print("----------------------------------------------------------------------------------------------")
    response = requests.get(s, verify=False)
    # print(response.text)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        script_elements = soup.find_all('script')
        selected_script_element = None

        for script_element in script_elements:
            script_content = script_element.string
            if script_content:
                if 'allBuilds' in script_content:
                    selected_script_element = script_content
                    break
        
        if selected_script_element:
            var_name = 'allBuilds'
            pattern = rf'{var_name}\s*=\s*(.*?);'

            match = re.search(pattern, selected_script_element)
            if match:
                all_jobs=match.group(1)
                # print(all_builds)
                try:
                    all_jobs_parsed=json.loads(all_jobs)
                    current_date=get_current_date()
                    jobs_run_today = []
                    for ele in all_jobs_parsed:
                        job_time=parse_job_date(ele["Started"])
                        if job_time == current_date and ele["Result"] != "PENDING":
                            job_id = ele["ID"]
                            job_log_path = ele["SpyglassLink"]
                            job_dict = {"ID": job_id, "SpyglassLink": job_log_path}
                            jobs_run_today.append(job_dict)
                    return jobs_run_today
                except json.JSONDecodeError as e:
                    print("convert failed")
    else:
        print("response failed")
    
    #work on removing the unwanted code used to select the script
    #improve code to do better error handling

def cluster_deploy_status(spy_link):
    job_type,job_platform = job_classifier(spy_link)
    job_log_url = 'https://gcsweb-ci.apps.ci.l2s4.p1.openshiftapps.com/gcs' + spy_link[8:] + '/artifacts/' + job_type + '/ipi-install-' + job_platform +'-install/finished.json'
    #print(job_log_url)
    response = requests.get(job_log_url, verify=False)
    cluster_status = json.loads(response.text)
    return cluster_status["result"]

def job_classifier(spy_link):

    pattern = r'ocp.*?/'
    match = re.search(pattern,spy_link)

    if match:
        job_type = match.group(0)
        job_type = job_type.rstrip('/')
        # print(job_type)
    else:
        print("not found")

    if spy_link.find("powervs") != -1:
        job_platform = "powervs"
        return job_type,job_platform
    elif spy_link.find("libvirt") != -1:
        job_platform = "libvirt"
        return job_type,job_platform
    else:
        return 1

def get_failed_e2e_testcases(spy_link,job_type):

    test_log_junit_dir_url = "https://gcsweb-ci.apps.ci.l2s4.p1.openshiftapps.com/gcs" + spy_link[8:] + "/artifacts/" + job_type + "/openshift-e2e-libvirt-test/artifacts/junit/"

    response = requests.get(test_log_junit_dir_url, verify=False)
    if response.status_code == 200:
        test_failure_summary_filename_re = re.compile('(test-failures-summary_2[^.]*\.json)')
        test_failure_summary_filename_match = test_failure_summary_filename_re.search(response.text, re.MULTILINE|re.DOTALL)
        if test_failure_summary_filename_match is not None:
            test_failure_summary_filename_str = test_failure_summary_filename_match.group(1)
            test_log_url="https://gcsweb-ci.apps.ci.l2s4.p1.openshiftapps.com/gcs" + spy_link[8:] + "/artifacts/" + job_type + "/openshift-e2e-libvirt-test/artifacts/junit/" + test_failure_summary_filename_str
            response_2 = requests.get(test_log_url,verify=False)
            if response_2.status_code == 200:
                data = response_2.json()
                e2e_failure_list = data['Tests']
                return e2e_failure_list
            else:
                print("error parsing data")
        else:
            print("ERROR: Could not find test-failures-summary_*.json?")
    else:
        print("error")


def temporary_main_function(prow_ci_data):

    j=0
    for url in prow_ci_data["prow_ci_links"]:
        print(prow_ci_data["prow_ci_names"][j])
        j=j+1
        job_list = get_jobs(url)
        i=0
        print("-------------------------------------------------------------------------------------------------")

        for job in job_list:
            
            cluster_status=cluster_deploy_status(job["SpyglassLink"])
            i=i+1
            if cluster_status == 'SUCCESS':
                job_type,_ = job_classifier(job["SpyglassLink"])
                e2e_failures = get_failed_e2e_testcases(job["SpyglassLink"],job_type)
                print(i,". Job ID: ",job["ID"],"Cluster Creation Success")
                if not e2e_failures:
                    print("All test cases passed")
                else:
                    print("Failed testcases: ")
                    for e in e2e_failures:
                        print(e["Test"]["Name"])
            else:
                print(i,". Job ID: ",job["ID"],"Cluster Creation Failed")
            print("\n")
                #write function analyze cluster installation failures
        print("--------------------------------------------------------------------------------------------------")

temporary_main_function(config_data)
