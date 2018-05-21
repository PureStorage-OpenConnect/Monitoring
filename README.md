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
* [check_purefb_hw.py](https://github.com/PureStorage-OpenConnect/Monitoring/blob/master/check_purefb_hw.py) Simple plugin for monitoring Pure Storage FlashBlade hardware components.
* [check_purefb_occpy.py](https://github.com/PureStorage-OpenConnect/Monitoring/blob/master/check_purefb_occpy.py) Simple plugin for monitoring Pure Storage FlashBlade space occupancy (global/object store/per NFS volume/).
* [check_purefb_perf.py](https://github.com/PureStorage-OpenConnect/Monitoring/blob/master/check_purefb_perf.py) Simple plugin for monitoring Pure Storage FlashBlade performance metrics (global/per protocol).
### Installation

The plugin scripts should be copied to the Nagios plugins directory on the machine hosting the Nagios server or the NRPE,
for example the /usr/lib/nagios/plugins folder should be used for Nagios XI.
Change the execution rights of the plugins to allow the execution to 'all' (usually chmod 0755).
Plugins depends on

[nagiosplugin](http://pythonhosted.org/nagiosplugin) helper Python class library for Nagios plugins by Christian Kauhaus

[purestorage](https://github.com/purestorage/rest-client) Pure Storage Python REST Client for FlashArray

[purity_fb](https://github.com/purestorage/purity_fb_python_client/archive/v1.2.tar.gz) Pure Storage Python REST Client for FlashBlade v1.2

The first two modules can be easily installed via pip

pip install nagiosplugin

pip install purestorage

while the latter must be installed in version 1.2, due to a bug in latest version

pip install 'purity_fb==1.2'

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

 *check_purefa_occpy.py endpoint api_token [--vol volname] [-w RANGE] [-c RANGE]*
 
  Nagios plugin to retrieve the overall occupancy from a Pure Storage FlashArray or from a single volume.
  Storage occupancy indicators are collected from the target FA using the REST call.
  The plugin has two mandatory arguments:  'endpoint', which specifies the target FA and 'apitoken', which
  specifies the autentication token for the REST call session. A third optional parameter, 'volname' can
  be used to check a specific named value. The optional values for the warning and critical thresholds have
  different meausure units: they must be expressed as percentages in the case of checkig the whole flasharray
  occupancy, while they must be integer byte units if checking a single volume.
 
###### Example

Check the whole FlashArray occupancy:

check_purefa_occpy.py 10.225.112.81 c4eb5b21-4122-b871-8b0f-684bf72b5283

PURE_FA_OCCUPANCY OK - FA occupancy is 66% | 'FA occupancy'=66.0%;;;0;100


Check volume *oracle-u04* occupancy

check_purefa_occpy.py 10.225.112.81 c4eb5b21-4122-b871-8b0f-684bf72b5283 --vol oracle1-u04

PURE_VOL_OCCUPANCY OK - z-oracle1-u04 occupancy is 52624121069B | 'oracle1-u04 occupancy'=52624121069B;;;0

#### check_purefa_perf.py
Nagios plugin to retrieve the six (6) basic KPIs from a Pure Storage FlashArray.
Bandwidth counters (read/write), IOPs counters (read/write) and latency (read/write) are collected from the
target FA using the REST call.

##### Syntax

 *check_purefa_perf.py endpoint api_token [--vol volname][--tw RANGE[,RANGE,...]] [--tc RANGE[,RANGE,...]] [--t TIMEOUT]*
 
The plugin has two mandatory arguments:  'endpoint', which specifies the target FA and 'apitoken', which
specifies the autentication token for the REST call session. A third optional parameter, 'volname' can
be used to check a specific named volume.
In addition to these parameters, the plugin accepts multiple warning and critical threshold parameters in positional order:
   1st threshold refers to write latency
   2nd threshold refers to read latency
   3rd threshold refers to write bandwidth
   4th threshold refers to read bandwidth
   5th threshold refers to write IOPS
   6th threshold refers to read IOPS.
 
###### Example

Check the whole FlashArray performance indicators.

check_purefa_perf.py 10.225.112.81 c4eb5b21-4122-b871-8b0f-684bf72b5283

PURE_FA_PERF OK - FA wlat is 237us | 'FA rbw'=328977030B/s;;;0 'FA riops'=80269rd/s;;;0 'FA rlat'=419us;;;0 'FA wbw'=110185869B/s;;;0 'FA wiops'=26798wr/s;;;0 'FA wlat'=237us;;;0

Check the volume *oracle1-u04* performance indicators

check_purefa_perf.py 10.225.112.81 c4eb5b21-4122-b871-8b0f-684bf72b5283 --vol oracle1-u04

PURE_VOL_PERF OK - oracle1-u04 wlat is 205us | 'oracle1-u04 rbw'=336190250B/s;;;0 'oracle1-u04 riops'=82078rd/s;;;0 'oracle1-u04 rlat'=370us;;;0 'oracle1-u04 wbw'=111469774B/s;;;0 'oracle1-u04 wiops'=27214wr/s;;;0 'oracle1-u04 wlat'=205us;;;0

#### check_purefb_hw.py

Nagios plugin to retrieve the current status of hardware components from a Pure Storage FlashBlade.
Hardware status indicators are collected from the target FB using the REST call.

##### Syntax

 *check_purefb_hw.py endpoint api_token hw_component*
 
The plugin has three mandatory arguments:  'endpoint', which specifies the target FB, 'apitoken', which
specifies the autentication token for the REST call session and 'component', that is the name of the
hardware component to be monitored. The component must be specified using the internal naming schema of
the Pure FlashBlade: i.e CH1 for the main chassis, CH1.FM1 for the primary flash module, CH1.FM2 for the secondary,
CH1.FB1 for the first blade of first chassis, CH1.FB2 for the secondary blade, CH2 for the second chained FlashBlade
and so on.
 
###### Example

check_purefb_hw.py 10.225.112.69 T-a1c1a9de-5d14-4f1d-9469-4e1853232ece  CH1.FM1

PURE_CH1.FM1 OK - CH1.FM1 status is 0 | 'CH1.FM1 status'=0;1;1

#### check_purefb_occpy.py

Nagios plugin to retrieve the overall occupancy from a Pure Storage FlashBlade, or from a single volume, or from the object store.
Storage occupancy indicators are collected from the target FB using the REST call.

##### Syntax

 *check_purefa_occpy.py endpoint api_token [--vol volname] [-w RANGE] [-c RANGE]*

The plugin has two mandatory arguments:  'endpoint', which specifies the target FB and 'apitoken', which
specifies the autentication token for the REST call session. A third optional parameter, 'volname' or 'objectstore' can
be used to check a specific named value or the objectstore occupancy. The optional values for the warning and critical thresholds have
different meausure units: they must be expressed as percentages in the case of checkig the whole flasharray
occupancy, while they must be integer byte units if checking a single volume.
 
###### Example

Check the whole FlashBlace occupancy:

check_purefb_occpy.py 10.225.112.69 T-a1c1a9de-5d14-4f1d-9469-4e1853232ece

PURE_FB_OCCUPANCY OK - FB occupancy is 21% | 'FB occupancy'=21.0%;;;0;100

Check volume *oracle-u01* occupancy

./check_purefb_occpy.py 10.225.112.69 T-a1c1a9de-5d14-4f1d-9469-4e1853232ece --vol oracle-u01

PURE_FB_VOL_OCCUPANCY OK - oracle-u01 occupancy is 193883707392B | 'oracle-u01 occupancy'=193883707392B;;;0

Check objectsore overall occupancy

check_purefb_occpy.py 10.225.112.69 T-a1c1a9de-5d14-4f1d-9469-4e1853232ece --objstore

PURE_FB_OBJSTOR_OCCUPANCY OK - FB occupancy is 1% | 'FB occupancy'=1.0%;;;0;100

#### check_purefb_perf.py

Nagios plugin to retrieve the six (6) basic KPIs from a Pure Storage FlashBlade.
Bandwidth counters (read/write), IOPs counters (read/write) and latency (read/write) are collected from the
target FB using the REST call.

##### Syntax

*check_purefb_perf.py endpoint api_token [--proto nfs|http|s3][--tw RANGE[,RANGE,...]] [--tc RANGE[,RANGE,...]] [--t TIMEOUT]*
 
The plugin has two mandatory arguments:  'endpoint', which specifies the target FA and 'apitoken', which
specifies the autentication token for the REST call session. A third optional parameter, 'protocol' can
be used to check a specific protocol.
The plugin accepts multiple warning and critical threshold parameters in a positional fashion:
   1st threshold refers to write latency
   2nd threshold refers to read latency
   3rd threshold refers to write bandwidth
   4th threshold refers to read bandwidth
   5th threshold refers to write IOPS
   6th threshold refers to read IOPS
 
###### Example

Check the whole FlashBlade performance indicators.

check_purefb_perf.py 10.225.112.69 T-a1c1a9de-5d14-4f1d-9469-4e1853232ece

PURE_FB_PERF OK - FB wlat is 0us | 'FB rbw'=0B/s;;;0 'FB riops'=0rd/s;;;0 'FB rlat'=0us;;;0 'FB wbw'=0B/s;;;0 'FB wiops'=0wr/s;;;0 'FB wlat'=0us;;;0

Check the NFS performance indicators.

check_purefb_perf.py 10.225.112.69 T-a1c1a9de-5d14-4f1d-9469-4e1853232ece --proto nfs

PURE_FB_NFS_PERF OK - FB wlat is 0us | 'FB rbw'=0B/s;;;0 'FB riops'=0rd/s;;;0 'FB rlat'=0us;;;0 'FB wbw'=0B/s;;;0 'FB wiops'=0wr/s;;;0 'FB wlat'=0us;;;0

Check the S3 performance indicators.

check_purefb_perf.py 10.225.112.69 T-a1c1a9de-5d14-4f1d-9469-4e1853232ece --proto s3

PURE_FB_S3_PERF OK - FB wlat is 0us | 'FB rbw'=0B/s;;;0 'FB riops'=0rd/s;;;0 'FB rlat'=0us;;;0 'FB wbw'=0B/s;;;0 'FB wiops'=0wr/s;;;0 'FB wlat'=0us;;;0

Check the HTTP performance indicators.

check_purefb_perf.py 10.225.112.69 T-a1c1a9de-5d14-4f1d-9469-4e1853232ece --proto http

PURE_FB_HTTP_PERF OK - FB wlat is 0us | 'FB rbw'=0B/s;;;0 'FB riops'=0rd/s;;;0 'FB rlat'=0us;;;0 'FB wbw'=0B/s;;;0 'FB wiops'=0wr/s;;;0 'FB wlat'=0us;;;
