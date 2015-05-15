## Cloud99 (Framework for Openstack HA Testing ##

Testing an OpenStack cloud for High Availability(HA)  is a critical aspect of certifying an OpenStack Cloud for production. But High Availability testing of OpenStack clouds involves a combination of several aspects

 - Generating an initial load on the cloud before testing starts
 - Health checks to make sure the cloud is ready for HA testing
 - Running control/plane data plane tests in parallel with service disruptions
 - Active monitoring of the cloud during the HA test run
 -  Quantification of failures and test results

This tool attempts to automate some of these workflows and makes it easier for the Cloud admin to trigger disruptions and asses "how available" the OpenStack cloud actually is. 

Cloud99 has 3 important components embedded

 - Monitors
 - Disruptors
 - Runners

All 3 of the above are written using a plugin model so there can be several monitors, disruptors and runners based on your OpenStack deployment. For now we implement commonly used plugins for some of these. The sections below describe these in more detail. 


----------
Monitors as the name suggests, monitor the cloud while the disruption event/tests are in progress. For now the following monitors are supported. 

 - OpenStack API monitor (reports status of API services and agents)
 - Ansible Host monitor (uses ansible to login to all your openstack nodes and check service status)
 - Nagios monitor (Leverage Nagios agents if available in your openstack nodes, also always monitors application VMs on cloud)

For the Nagios monitor being used with Application VMs we prebuild a qcow2 images with nagios agent enabled and launch this on the cloud before testing starts. This flow will also be automated in the next release.

Disruptors as the name suggests disrupts the Openstack services/Nodes. For now the following disruptors are supported

 - Node disruptor (reboots openstack nodes like compute and controllers)
 - Process disruptor (disrupts services on different nodes)
 - Container disruptor (supports stopping docker containers, more for container based openstack deployments)

Runners are the critical part which actually runs scale/functionality tests in parallel with disruptions. This can be any script/framework that runs OpenStack tests. The only requirement is the framework should continue on failure as disruptions can cause failures. For now we support the following runner

 - Rally runner (provide a pre-installer rally framework and pointer to scenario file)

The framework spawns separate threads for each runner, monitor and disruptors and performs all these in parallel. So for example you can perform a test which Boots  a VM, stop the nova scheduler and monitors the cloud. All these actions happen in parallel.  

Now lets talk about how to use the tool and commands involved

----------
**Getting Started**

    git clone https://github.com/cisco-oss-eng/Cloud99.git
    pip install -r requirements.txt
    sudo ./install.sh
    python ha_engine/ha_main.py -f configs/executor.yaml
   
Before you run the tool you need to provide some information to the tool about your openstack cloud and also what kind of disruptions you would like to have. 

The configs directory has information on configuration files that you need to modify to use the tool. 

