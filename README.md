# OpenstackHA
 Framework to test the Openstack HA
 High availability testing is a critical aspect of certifying an Openstack cloud for 
production. But high availability testing of openstack clouds involves a combination
of several aspects
1. Generating an initial load on the cloud before testing starts
2. Health Checks to make sure the cloud is ready for HA testing
3. Running control plane/data plane scale tests in parallel with disruptions
4. Active monitoring to get an idea of the impact of disruption event

This tool attempts to automate the entire flow of HA testing of 
Openstack clouds. The test tool has 3 important concepts
1. Monitors 
2. Disruptors
3. Runners

All three of the above are written based on a plugin model so you can
have multiple backend plugins for each of these. For now the following 
plugins have been implemented but you can add your own if these dont fit
your needs. 

Monitors as the name suggest monitor the cloud while the Disruption event/
tests are running. For now the following monitors are supported
a. Openstack API monitor (essentially reports nova service-list and neutron agent-list)
b. Ansible host monitor (monitors that all required services are running on your openstack nodes)
c. Nagios plugin monitor (Monitors your openstack nodes if nagios is enabled. Always monitors Openstack
pre-defined application VMs)

Disruptors as the name suggest disrupts the Openstack services/Nodes. For now
the following disruptors are supported
a. Node disruptor (reboots nodes like compute, network, controller etc)
b. Process disruptor (disrupts/kills openstack services on specific nodes)
c. Container disruptor (disrupts containers in environments like kolla openstack installations)
 
Runners are a critical part which actually runs scale/functionality tests while
disruption is happening. For now the following runners are supported
a. Rally runner (provide a pointer to your rally scenario file)

The way the framework works is it spawns seperate threads for each runner, monitor and disruptor
and performs all these in parallel. So for example you can do things like
Perform a VM boot test and in parallel stop openstack nova scheduler service for instance
and assess the impact through monitoring

How to run/use the tool (User View)
