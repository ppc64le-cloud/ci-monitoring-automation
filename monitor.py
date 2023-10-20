import json
import re
from bs4 import BeautifulSoup
import urllib3
import requests
from datetime import datetime


urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

url_set = ['']

def get_current_date():
    return datetime.now().date()

def parse_build_date(da):
    date_2=datetime.strptime(da,"%Y-%m-%dT%H:%M:%SZ")
    job_time=date_2.date()
    return job_time

def get_builds(s):
    # print("Hi")
    for url in s:
        print("----------------------------------------------------------------------------------------------")
        response = requests.get(url, verify=False)
        # print(response.status_code)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            script_elements = soup.find_all('script')
            selected_script_element = None
            # print(len(script_elements))
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
                    all_value=match.group(1)
                    try:
                        all_array=json.loads(all_value)
                        current_date=get_current_date()
                        for ele in all_array:
                            job_time=parse_build_date(ele["Started"])
                            if job_time == current_date:
                                print(ele["ID"],ele["Result"])
                    except json.JSONDecodeError as e:
                        print("convert failed")
        else:
            print("response failed")

# def get_failure_type():
#     response = requests.get('https://gcsweb-ci.apps.ci.l2s4.p1.openshiftapps.com/gcs/origin-ci-test/logs/periodic-ci-openshift-multiarch-master-nightly-4.15-upgrade-from-nightly-4.14-ocp-ovn-remote-libvirt-ppc64le/1715201290650259456/artifacts/ocp-ovn-remote-libvirt-ppc64le/ipi-install-libvirt-install/finished.json', verify=False)
#     if response.status_code == 200:
#         print(response.text)

# get_failure_type()
get_builds(url_set)

    
