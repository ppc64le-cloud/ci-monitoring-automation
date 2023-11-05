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
                    print("convert failed")
    else:
        print("response failed")
    
    #work on removing the unwanted code used to select the script
    #improve code to do better error handling

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
    _,job_platform = job_classifier(spy_link)
    if "libvirt" in spy_link and "upgrade" not in spy_link:
        job_platform = "ocp-e2e-ovn-remote-libvirt-ppc64le/gather-libvirt"
    elif "powervs" in spy_link:
        job_platform = "ocp-e2e-ovn-ppc64le-powervs/gather-extra"
    elif "upgrade" in spy_link:
        job_platform = "ocp-ovn-remote-libvirt-ppc64le/gather-libvirt"
    
    node_log_url = "https://gcsweb-ci.apps.ci.l2s4.p1.openshiftapps.com/gcs" + spy_link[8:] + \
        "/artifacts/" + job_platform +"/artifacts/oc_cmds/nodes"
    node_log_response = requests.get(node_log_url, verify=False, timeout=15)
    response_str=node_log_response.text
    if response_str.count("libvirt-ppc64le") != 5:
        return "Not all nodes are up and running"
    if "NotReady" in response_str:
        return "Some Nodes are in NotReady state"
    return "All nodes are in Ready state"

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
                    return 'ERROR'
            else:
                return 'ERROR'
        else:
            return 'ERROR'
    else:
        return 'ERROR'


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
                    return 'ERROR'
            else:
                return 'ERROR'
        else:
            return 'ERROR'
    else:
        return 'ERROR' 

def print_e2e_testcase_failures(spylink,jobtype):
    e2e_result = False
    e2e_failures = get_failed_e2e_testcases(spylink,jobtype)
    if e2e_failures != 'ERROR':
        if not e2e_failures:
            print("All e2e conformance test cases passed")
            e2e_result = True
        else:
            print("Failed conformance testcases: ")
            for e in e2e_failures:
                print(e["Test"]["Name"])
    else:
        print("ERROR: Could not find test-failures-summary_*.json…")
    return e2e_result

def print_monitor_testcase_failures(spylink,jobtype):
    e2e_result = False
    monitor_e2e_failures = get_failed_monitor_testcases(spylink,jobtype)
    if monitor_e2e_failures != 'ERROR':
        if not monitor_e2e_failures:
            print("All monitor test cases passed")
            e2e_result = True
        else:
            print("Failed monitor testcases: ")
            for e in monitor_e2e_failures:
                print(e["Test"]["Name"])
    else:
        print("ERROR: Could not find test-failures-summary_monitor_*.json…")
    return e2e_result


def temporary_main_function(prow_ci_data):

    j=0
    
    for url in prow_ci_data["prow_ci_links"]:
        url = "https://prow.ci.openshift.org/job-history/gs/origin-ci-test/logs/" + url
        if "4.15" in url:
            sep = True
        else:
            sep = False

        print(prow_ci_data["prow_ci_names"][j])
        job_list = get_jobs(url)
        i=0
        print("-------------------------------------------------------------------------------------------------")
        if len(job_list) == 0:
            print ("No job runs on {} today".format(prow_ci_data["prow_ci_names"][j]))
        j=j+1
        deploy_count = 0
        e2e_count = 0
        for job in job_list:
            e2e_test_result = e2e_monitor_result = False
            cluster_status=cluster_deploy_status(job["SpyglassLink"])
            i=i+1
            print(i,". Job ID: ",job["ID"])
            get_quota_and_nightly(job["SpyglassLink"])
            print("Node Status:\n ", get_node_status(job["SpyglassLink"]))

            if cluster_status == 'SUCCESS' and sep == False:
                deploy_count += 1
                job_type,_ = job_classifier(job["SpyglassLink"])
                e2e_test_result = print_e2e_testcase_failures(job["SpyglassLink"],job_type)
                if e2e_test_result:
                    e2e_count += 1
            
            elif cluster_status == 'SUCCESS' and sep == True:
                deploy_count += 1
                job_type,_ = job_classifier(job["SpyglassLink"])
                e2e_test_result = print_e2e_testcase_failures(job["SpyglassLink"],job_type)
                e2e_monitor_result = print_monitor_testcase_failures(job["SpyglassLink"],job_type)
                if e2e_test_result and e2e_monitor_result:
                    e2e_count += 1
                
            elif cluster_status == 'FAILURE':
                print("Cluster Creation Failed")
            
            elif cluster_status == 'ERROR':
                print('Unable to get cluster status please check prowCI UI ')

            print("\n")

        if len(job_list) != 0:
            print ("\n{}/{} deploys succeeded".format(deploy_count, len(job_list)))
            print ("{}/{} e2e tests succeeded".format(e2e_count, len(job_list)))
                #write function analyze cluster installation failures
        
        
        print("--------------------------------------------------------------------------------------------------")

temporary_main_function(config_data)
