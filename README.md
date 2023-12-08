# CI-Monitoring-Automation



### Overview

The ci-monitoring-automation Repository is a collection of Python scripts designed to automate monitoring of Continuous Integration (CI) system workflows. These scripts facilitate the retrieval and analysis of information related to coreOS CI builds, offering developers the flexibility to gather data of builds run for the current day or within a specified date range.


### Prerequisites

```
Python3
pip
```


### Installation

```
git clone https://github.com/ocp-power-automation/ci-monitoring-automation.git
cd ci-monitoring-automation
Create a virtualenv if required and install required packages using "pip install -r requirements.txt"
```

### Usage

1. **CI_DailyBuildUpdate.py:** The CI_DailyBuildUpdates.py script will fetch and display information of the all builds that ran on the CI system for the current day.  

    1. Brief Information: The CI_DailyBuildUpdates.py script when invoked with command line argument info_type as "brief" it will display Build type, job id, cluster deployment status, Lease and total number of failed testcases.

        ```python3 CI_DailyBuildUpdates.py --info_type brief```
        
    2. The CI_DailyBuildUpdates.py script when invoked with command line arguments info_type as "brief" and zone, it will display the builds details in the provided zone.
        
        ```python3 CI_DailyBuildUpdates.py --info_type brief --zone syd04```

    3. Detailed Information: The CI_DailyBuildUpdates.py script when invoked with command line argument info_type as "detailed" it will display the Job id, job link, cluster deployment error message if it occured, Nightly image used, Node status, Checks for Node crash and lists all the failed testcases.  

        ```python3 CI_DailyBuildUpdates.py --info_type detailed```

    4. The CI_DailyBuildUpdates.py script when invoked with command line arguments info_type as "detailed" and zone, it will display the builds details in the provided zone.

        ```python3 CI_DailyBuildUpdates.py --info_type detailed --zone syd04```



2. **CI_JobHistory.py:** The CI_JobHistory.py is a interactive script which allows user to query a specific information from all builds that ran on the CI system within a given date range.  
    
    ```python3 CI_JobHistory.py```

    1. The CI_JobHistory.py when invoked with command line argument zone, it will get all builds that ran in the particular zone.

        ```python3 CI_JobHistory.py --zone syd04```


3. **p_config.json:** The p_config.json file will have ci name and ci links of ppc64le architecture CI in the key value pair where value of ci link will be prow periodic job name.The new CI's can be easily integrated by adding the ci name and ci link in the config.json file.


4. **z_config.json:** The p_config.json file will have ci name and ci links of s390x architecture CI in the key value pair where value of ci link will be prow periodic job name.The new CI's can be easily integrated by adding the ci name and ci link in the config.json file.
