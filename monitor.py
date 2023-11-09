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
    
    response = requests.get(s, verify=False, timeout=15)
    
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
                #print(all_jobs)
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
                    return "Failed to extract the spy-links from spylink please check the UI!"
                    
    else:
        return "Failed to get the prowCI response"
    

def cluster_deploy_status(spy_link):
    job_type,job_platform = job_classifier(spy_link)
    job_log_url = 'https://gcsweb-ci.apps.ci.l2s4.p1.openshiftapps.com/gcs' + spy_link[8:] + '/artifacts/' + job_type + '/ipi-install-' + job_platform +'-install/finished.json'

    response = requests.get(job_log_url, verify=False, timeout=15)
    if response.status_code == 200:
        try:
            cluster_status = json.loads(response.text)
            return cluster_status["result"]
        except json.JSONDecodeError as e:
            return 'ERROR'
    else:
        return 'ERROR'
    
def get_node_status(spy_link):
    '''Function to fetch the node status and determine if all nodes are up and running'''
    job_type,job_platform = job_classifier(spy_link)
    if job_platform == "powervs":
        job_type += "/gather-extra"
    else:
        job_type += "/gather-libvirt"
    
    node_log_url = "https://gcsweb-ci.apps.ci.l2s4.p1.openshiftapps.com/gcs" + spy_link[8:] + \
        "/artifacts/" + job_type +"/artifacts/oc_cmds/nodes"
    node_log_response = requests.get(node_log_url, verify=False, timeout=15)
    if "NAME" in node_log_response.text:
        response_str=node_log_response.text
        if "NotReady" in response_str:
            return "Some Nodes are in NotReady state"
        elif response_str.count("master-") != 3:
            return "Not all master nodes are up and running"
        elif response_str.count("worker-") != 2:
            return "Not all worker nodes are up and running"
    else:
        return "Node details not found"
    return "All nodes are in Ready state"

def check_node_crash(spy_link):
    job_type,_ = job_classifier(spy_link)
    crash_log_url = "https://gcsweb-ci.apps.ci.l2s4.p1.openshiftapps.com/gcs" + spy_link[8:] + "/artifacts/" +job_type + "/ipi-conf-debug-kdump-gather-logs/artifacts/"
    crash_log_response = requests.get(crash_log_url, verify=False, timeout=15)
    if "kdump.tar" in crash_log_response.text:
        print("*********************************")
        print ("ERROR- Crash observed in the job")
        print("*********************************")
    else:
        print("No crash observed")
        
def get_quota_and_nightly(spy_link):
    _,job_platform = job_classifier(spy_link)

    build_log_url = "https://gcsweb-ci.apps.ci.l2s4.p1.openshiftapps.com/gcs" + spy_link[8:] + "/build-log.txt"
    if job_platform == "libvirt":
        job_platform+="-ppc64le"
    elif job_platform == "powervs":
        job_platform+="-[1-9]"

    zone_log_re = re.compile('(Acquired 1 lease\(s\) for {}-quota-slice: \[)([^]]+)(\])'.format(job_platform), re.MULTILINE|re.DOTALL)
    build_log_response = requests.get(build_log_url, verify=False, timeout=15)
    zone_log_match = zone_log_re.search(build_log_response.text)
    if zone_log_match is None:
        print("Failed to fetch lease information")
    else:
        print("Lease Quota-",zone_log_match.group(2))
    # Fetch the nightly information for non-upgrade jobs
    if "upgrade" not in build_log_url:
        nightly_log_re = re.compile('(Resolved release ppc64le-latest to (\S+))', re.MULTILINE|re.DOTALL)
        nightly_log_match = nightly_log_re.search(build_log_response.text)
        if nightly_log_match is None:
            rc_nightly_log_re = re.compile('(Using explicitly provided pull-spec for release ppc64le-latest \((\S+)\))', re.MULTILINE|re.DOTALL)
            rc_nightly_log_match = rc_nightly_log_re.search(build_log_response.text)
            if rc_nightly_log_match is None:
                print ("Unable to fetch nightly information- No match found")
            else:
                print(rc_nightly_log_match.group(2))
        else:
            print("ppc64le-latest-",nightly_log_match.group(2))
    # Fetch nightly information for upgrade jobs- fetch both ppc64le-initial and ppc64le-latest
    else:
        nightly_initial_log_re = re.compile('(Resolved release ppc64le-initial to (\S+))', re.MULTILINE|re.DOTALL)
        nightly_initial_log_match = nightly_initial_log_re.search(build_log_response.text)
        if nightly_initial_log_match is None:
            print ("Unable to fetch nightly ppc64le-initial information- No match found")
        else:
            print("ppc64le-initial-",nightly_initial_log_match.group(2))
        nightly_latest_log_re = re.compile('(Resolved release ppc64le-latest to (\S+))', re.MULTILINE|re.DOTALL)
        nightly_latest_log_match = nightly_latest_log_re.search(build_log_response.text)
        if nightly_latest_log_match is None:
            print ("Unable to fetch nightly ppc64le-latest information- No match found")
        else:
            print("ppc64le-latest-",nightly_latest_log_match.group(2))

def job_classifier(spy_link):

    pattern = r'ocp.*?/'
    match = re.search(pattern,spy_link)

    if match:
        job_type = match.group(0)
        job_type = job_type.rstrip('/')

    if spy_link.find("powervs") != -1:
        job_platform = "powervs"
        return job_type,job_platform
    elif spy_link.find("libvirt") != -1:
        job_platform = "libvirt"
        return job_type,job_platform


def get_failed_monitor_testcases(spy_link,job_type):
    test_log_junit_dir_url = "https://gcsweb-ci.apps.ci.l2s4.p1.openshiftapps.com/gcs" + spy_link[8:] + "/artifacts/" + job_type + "/openshift-e2e-libvirt-test/artifacts/junit/"

    response = requests.get(test_log_junit_dir_url, verify=False, timeout=15)

    if response.status_code == 200:
        monitor_test_failure_summary_filename_re = re.compile('(test-failures-summary_monitor_2[^.]*\.json)')
        monitor_test_failure_summary_filename_match = monitor_test_failure_summary_filename_re.search(response.text, re.MULTILINE|re.DOTALL)
        
        if monitor_test_failure_summary_filename_match is not None:
            monitor_test_failure_summary_filename_str = monitor_test_failure_summary_filename_match.group(1)
            test_log_url="https://gcsweb-ci.apps.ci.l2s4.p1.openshiftapps.com/gcs" + spy_link[8:] + "/artifacts/" + job_type + "/openshift-e2e-libvirt-test/artifacts/junit/" + monitor_test_failure_summary_filename_str
            response_2 = requests.get(test_log_url,verify=False, timeout=15)
            if response_2.status_code == 200:
                try:
                    data = response_2.json()
                    e2e_failure_list = data['Tests']
                    return e2e_failure_list
                except json.JSONDecodeError as e:
                    return "Failed to parse the data from e2e-test log file!"
            else:
                return "Failed to get response from e2e-test log file url!"
        else:
            return "Test summary file not found"
    else:
        return "Failed to get response from e2e-test directory url"


def get_failed_e2e_testcases(spy_link,job_type):

    test_log_junit_dir_url = "https://gcsweb-ci.apps.ci.l2s4.p1.openshiftapps.com/gcs" + spy_link[8:] + "/artifacts/" + job_type + "/openshift-e2e-libvirt-test/artifacts/junit/"

    response = requests.get(test_log_junit_dir_url, verify=False, timeout=15)

    if response.status_code == 200:
        test_failure_summary_filename_re = re.compile('(test-failures-summary_2[^.]*\.json)')
        test_failure_summary_filename_match = test_failure_summary_filename_re.search(response.text, re.MULTILINE|re.DOTALL)
        
        if test_failure_summary_filename_match is not None:
            test_failure_summary_filename_str = test_failure_summary_filename_match.group(1)
            test_log_url="https://gcsweb-ci.apps.ci.l2s4.p1.openshiftapps.com/gcs" + spy_link[8:] + "/artifacts/" + job_type + "/openshift-e2e-libvirt-test/artifacts/junit/" + test_failure_summary_filename_str
            response_2 = requests.get(test_log_url,verify=False, timeout=15)
            if response_2.status_code == 200:
                try:
                    data = response_2.json()
                    e2e_failure_list = data['Tests']
                    return e2e_failure_list
                except json.JSONDecodeError as e:
                    return "Failed to parse the data from e2e-test log file!"
            else:
                return "Failed to get response from e2e-test log file url!"
        else:
            return "Test summary file not found"
    else:
        return "Failed to get response from e2e-test directory url" 

def print_e2e_testcase_failures(spylink,jobtype):
    e2e_result = False
    e2e_failures = get_failed_e2e_testcases(spylink,jobtype)
    if isinstance(e2e_failures,list):
        if not e2e_failures:
            print("All e2e conformance test cases passed")
            e2e_result = True
        else:
            print("Failed conformance testcases: ")
            for e in e2e_failures:
                print(e["Test"]["Name"])
    elif isinstance(e2e_failures,str):
        print(e2e_failures)
    return e2e_result

def print_monitor_testcase_failures(spylink,jobtype):
    e2e_result = False
    monitor_e2e_failures = get_failed_monitor_testcases(spylink,jobtype)
    if isinstance(monitor_e2e_failures,list):
        if not monitor_e2e_failures:
            print("All monitor test cases passed")
            e2e_result = True
        else:
            print("Failed monitor testcases: ")
            for e in monitor_e2e_failures:
                print(e["Test"]["Name"])
    elif isinstance(monitor_e2e_failures,str):
        print(monitor_e2e_failures)
    return e2e_result


final_job_list=[]


#fetches all the job spylinks in the given date range

def get_jobs_with_date(prowci_url,start_date,end_date):
    
    response = requests.get(prowci_url, verify=False, timeout=15)

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')

        td_element = soup.find_all('td')
        td_element2 = str(td_element)
        next_link_pattern = r'/job[^>"]*'
        next_link_match = re.search(next_link_pattern,td_element2)
        next_link = next_link_match.group()

        script_elements = soup.find_all('script')
        selected_script_element = None

        # print(script_elements) prints the list of scripts elements

        for script_element in script_elements:
            script_content = script_element.string
            if script_content:
                if 'allBuilds' in script_content:
                    selected_script_element = script_content
                    break
        
        # print(type(selected_script_element)) ##prints script element with a var name

        if selected_script_element:
            var_name = 'allBuilds'
            pattern = rf'{var_name}\s*=\s*(.*?);'

            match = re.search(pattern, selected_script_element)
            
            if match:
                all_jobs=match.group(1)
                try:
                    all_jobs_parsed=json.loads(all_jobs)
                    for ele in all_jobs_parsed:
                        job_time=parse_job_date(ele["Started"])
                        
                        if end_date <= job_time <= start_date and ele["Result"] != "PENDING" :
                            job_log_path = ele["SpyglassLink"]
                            final_job_list.append(job_log_path)

                    next_page_link = 'https://prow.ci.openshift.org'+next_link
                    
                    check=get_next_page_first_build_date(next_page_link,end_date)
                    
                    if check == True:
                        get_jobs_with_date(next_page_link,start_date,end_date)
                    elif check == 'ERROR':
                        print("Error")
                    return final_job_list
                except json.JSONDecodeError as e:
                    print("Failed to extract data from the script tag")
                    return "ERROR"
    else:
        print("Failed to get response from the prowCI link")
        return 'ERROR'


#Checks if the jobs next page are in the given date range
 
def get_next_page_first_build_date(spylink,end_date):

    response = requests.get(spylink, verify=False, timeout=15)
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
                
                try:
                    all_jobs_parsed=json.loads(all_jobs)
                    job_date=all_jobs_parsed[0]["Started"]
                    parsed_job_date = parse_job_date(job_date)
                    if end_date <= parsed_job_date:
                        return True
                    elif end_date > parsed_job_date:
                        return False
                except json.JSONDecodeError as e:
                    print("Failed to extract the spy-links from spylink please check the UI!")
                    return "ERROR"
    else:
        print("Failed to get the prowCI response")
        return 'ERROR'


def get_brief_job_info(prow_ci_data):
    j=0

    for url in prow_ci_data["prow_ci_links"]:
        url = "https://prow.ci.openshift.org/job-history/gs/origin-ci-test/logs/" + url

        print(prow_ci_data["prow_ci_names"][j])
        job_list = get_jobs(url)
        i=0
        print("-------------------------------------------------------------------------------------------------")

        #check for get_jobs() function and prints the error message if any
        if isinstance(job_list,str):
            print(job_list)
            return 1
        
        if len(job_list) == 0:
            print ("No job runs on {} today".format(prow_ci_data["prow_ci_names"][j]))
        
        j=j+1
        deploy_count = 0
        e2e_count = 0

        for job in job_list:
            e2e_test_result = e2e_monitor_result = False
            cluster_status=cluster_deploy_status(job["SpyglassLink"])
            i=i+1
            print(i,".Job ID: ",job["ID"])
            print(" Job link: ",url.replace("job-history", "view")+"/"+job["ID"])
            get_quota_and_nightly(job["SpyglassLink"])
            check_node_crash(job["SpyglassLink"])
            node_status = get_node_status(job["SpyglassLink"])
            print(node_status)

            if cluster_status == 'SUCCESS' and "4.15" not in url:
                deploy_count += 1
                job_type,_ = job_classifier(job["SpyglassLink"])
                e2e_test_result = get_failed_e2e_testcases(job["SpyglassLink"],job_type)
                if isinstance(e2e_test_result,list):
                    if len(e2e_test_result) == 0:
                        e2e_count += 1
                        print("All e2e testcases passed")
                    elif len(e2e_test_result) != 0:
                        print(len(e2e_test_result),"testcases failed")
                elif isinstance(e2e_test_result,str):
                    print(e2e_test_result)

            elif cluster_status == 'SUCCESS' and "4.15" in url:
                deploy_count += 1
                job_type,_ = job_classifier(job["SpyglassLink"])
                e2e_test_result = get_failed_e2e_testcases(job["SpyglassLink"],job_type)
                e2e_monitor_result = get_failed_monitor_testcases(job["SpyglassLink"],job_type)
                if isinstance(e2e_test_result,list) and isinstance(e2e_monitor_result,list):
                    
                    total_e2e_failure = len(e2e_test_result)+len(e2e_monitor_result)
                    if total_e2e_failure != 0:
                        print(len(total_e2e_failure),"testcases failed")
                    elif total_e2e_failure == 0:
                        e2e_count += 1
                        print("All e2e testcases passed")
                elif isinstance(e2e_test_result,list) and isinstance(e2e_monitor_result,str):
                    print(e2e_monitor_result) #prints the error message recived while fetching monitor testcase results
                    if len(e2e_test_result) !=0:
                        print(len(e2e_test_result), "conformance testcases failed")
                    elif len(e2e_test_result) == 0:
                        print("All conformance e2e testcases passed")
                elif isinstance(e2e_test_result,str) and isinstance(e2e_monitor_result,list):
                    print(e2e_test_result) #prints the error message recived while fetching conformance testcase results
                    if len(e2e_monitor_result) !=0:
                        print(len(e2e_monitor_result), "monitor testcases failed")
                    elif len(e2e_monitor_result) == 0:
                        print("All monitor e2e testcases passed")
                elif isinstance(e2e_test_result,str) and isinstance(e2e_monitor_result,str):
                    print(e2e_test_result)
                    print(e2e_monitor_result)
        
            elif cluster_status == 'FAILURE':
                print("Cluster Creation Failed")

            elif cluster_status == 'ERROR':
                print('Unable to get cluster status please check prowCI UI ')

            print("\n")

        if len(job_list) != 0:
            print ("\n{}/{} deploys succeeded".format(deploy_count, len(job_list)))
            print ("{}/{} e2e tests succeeded".format(e2e_count, len(job_list)))

        print("--------------------------------------------------------------------------------------------------")
