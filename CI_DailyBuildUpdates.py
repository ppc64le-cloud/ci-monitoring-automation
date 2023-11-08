import json
from bs4 import BeautifulSoup
import urllib3
import monitor
import subprocess

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

with open('config.json') as config_file:
    config_data = json.load(config_file)

def temporary_main_function(prow_ci_data):

    j=0
    
    for url in prow_ci_data["prow_ci_links"]:
        url = "https://prow.ci.openshift.org/job-history/gs/origin-ci-test/logs/" + url

 
        print(prow_ci_data["prow_ci_names"][j])
        job_list = monitor.get_jobs(url)
        i=0
        print("-------------------------------------------------------------------------------------------------")

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
            cluster_status=monitor.cluster_deploy_status(job["SpyglassLink"])
            i=i+1
            print(i,". Job ID: ",job["ID"])
            monitor.get_quota_and_nightly(job["SpyglassLink"])

            if cluster_status == 'SUCCESS' and "4.15" not in url:
                deploy_count += 1
                job_type,_ = monitor.job_classifier(job["SpyglassLink"])
                e2e_test_result = monitor.print_e2e_testcase_failures(job["SpyglassLink"],job_type)
                if e2e_test_result:
                    e2e_count += 1
                print("Node Status:\n ", monitor.get_node_status(job["SpyglassLink"]))
            
            elif cluster_status == 'SUCCESS' and "4.15" in url:
                deploy_count += 1
                job_type,_ = monitor.job_classifier(job["SpyglassLink"])
                e2e_test_result = monitor.print_e2e_testcase_failures(job["SpyglassLink"],job_type)
                e2e_monitor_result = monitor.print_monitor_testcase_failures(job["SpyglassLink"],job_type)
                if e2e_test_result and e2e_monitor_result:
                    e2e_count += 1
                print("Node Status:\n ", monitor.get_node_status(job["SpyglassLink"]))

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
