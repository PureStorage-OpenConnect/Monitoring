# Monitoring
A repository of plugins and extensions to monitor Pure Storage FlashArrays using some of the most popular monitoring tools.

## PRTG sensors

* [PRTG_PureFA-HW.ps1](https://github.com/PureStorage-OpenConnect/Monitoring/blob/master/PRTG_PureFA-HW.ps1) Simple PRTG custom sensor for monitoring Pure Storage FlashArrays hardware components.
* [PRTG_PureFA-Perf.ps1](https://github.com/PureStorage-OpenConnect/Monitoring/blob/master/PRTG_PureFA-Perf.ps1) Simple PRTG custom sensor for monitoring Pure Storage FlashArrays basic KPIs - PowerShell version.
* [Pure-FA_prtg.py](https://github.com/PureStorage-OpenConnect/Monitoring/blob/master/Pure-FA_prtg.py) Simple PRTG custom sensor for monitoring Pure Storage FlashArrays basic KPIs - Python version
* [PRTG_PureFA-Volume.ps1](https://github.com/PureStorage-OpenConnect/Monitoring/blob/master/PRTG_PureFA-Volume.ps1) Simple PRTG custom sensor for monitoring Pure Storage FlashArrays volumes.

## Zabbix

* [Pure-FA_zabbix.py](https://github.com/PureStorage-OpenConnect/Monitoring/blob/master/Pure-FA_zabbix.py) Short example that illustrates how to build a simple extension to the Zabbix agent to monitor a Pure Storage FlashArray.

## Nagios/Icinga2

* [check_purefa_hw.py](https://github.com/PureStorage-OpenConnect/Monitoring/blob/master/check_purefa_hw.py) Simple plugin for monitoring Pure Storage FlashArray hardware components.
* [check_purefa_occpy.py](https://github.com/PureStorage-OpenConnect/Monitoring/blob/master/check_purefa_occpy.py) Simple plugin for monitoring Pure Storage FlashArray space occupancy (global/per volume).
* [check_purefa_perf.py](https://github.com/PureStorage-OpenConnect/Monitoring/blob/master/check_purefa_perf.py) Simple plugin for monitoring Pure Storage FlashArray performance metrics (global/per volume).

### Installation

The plugin scripts should be copied to the Nagios plugins directory on the machine hosting the Nagios server or the NRPE,
for example the /usr/lib/nagios/plugins folder should be used for Nagios XI.
Change the execution rights of the plugins to allow the execution to 'all' (usually chmod 0755).
Plugins depends on

[nagiosplugin](http://pythonhosted.org/nagiosplugin) helper Python class library for Nagios plugins by Christian Kauhaus
[purestorage](https://github.com/purestorage/rest-client) Pure Storage Python REST Client

The two modules can be easily installed via pip

pip install nagiosplugin
pip install purestorage

### Usage

#### check_purefa_hw.py

Nagios plugin to retrieve the current status of hardware components from a Pure Storage FlashArray.
Hardware status indicators are collected from the target FA using the REST call.

##### Syntax

 *check_purefa_hw.py endpoint api_token hw_component*
 
 The plugin has three mandatory arguments:  'endpoint', which specifies the target FA, 'apitoken', which
 specifies the autentication token for the REST call session and 'component', that is the name of the
 hardware component to be monitored. The component must be specified using the internal naming schema of
 the Pure FlashArray: i.e CH0 for the main chassis, CH1 for the secondary chassis (shelf 1), CT0 for controller 0,i
 CT1 for controller 1, CH0.NVB0 for the first NVRAM module, CH0.NVB1 for the second NVRAM module, CH0.BAY0 for
 the first flash module, CH0.BAY10 for the tenth flash module, CH1.BAY1, for the first flash module on the
 first additional shelf,...
 
###### Example

check_purefa_hw.py 10.225.112.81 c4eb5b21-4122-b871-8b0f-684bf72b5283 CH0.BAY2
PURE_CH0.BAY2 OK - CH0.BAY2 status is 0 | 'CH0.BAY2 status'=0;1;1

#### check_purefa_occpy.py

Nagios plugin to retrieve the current status of hardware components from a Pure Storage FlashArray.
Hardware status indicators are collected from the target FA using the REST call.

##### Syntax

 *check_purefa_occpy.py endpoint api_token [volname]*
 
  Nagios plugin to retrieve the overall occupancy from a Pure Storage FlashArray or from a single volume.
  Storage occupancy indicators are collected from the target FA using the REST call.
  The plugin has two mandatory arguments:  'endpoint', which specifies the target FA and 'apitoken', which
  specifies the autentication token for the REST call session. A third optional parameter, 'volname' can
  be used to check a specific named value. The optional values for the warning and critical thresholds have
  different meausure units: they must be expressed as percentages in the case of checkig the whole flasharray
  occupancy, while they must be integer byte units if checking a single volume.
 
###### Example

check_purefa_occpy.py 10.225.112.81 c4eb5b21-4122-b871-8b0f-684bf72b5283
PURE_FA_OCCUPANCY OK - FA occupancy is 66% | 'FA occupancy'=66.0%;;;0;100

check_purefa_occpy.py 10.225.112.81 c4eb5b21-4122-b871-8b0f-684bf72b5283 --vol oracle1-u04
PURE_VOL_OCCUPANCY OK - z-oracle1-u04 occupancy is 52624121069B | 'oracle1-u04 occupancy'=52624121069B;;;0
