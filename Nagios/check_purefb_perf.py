#!/usr/bin/env python
# Copyright (c) 2018 Pure Storage, Inc.
#
# * Overview
#
# This short Nagios/Icinga plugin code shows  how to build a simple plugin to monitor Pure Storage FlashBlade systems.
# The Pure Storage Python REST Client is used to query the FlashBlade performance counters.
# Plugin leverages the remarkably helpful nagiosplugin library by Christian Kauhaus.
#
# * Installation
#
# The script should be copied to the Nagios plugins directory on the machine hosting the Nagios server or the NRPE
# for example the /usr/lib/nagios/plugins folder.
# Change the execution rights of the program to allow the execution to 'all' (usually chmod 0755).
#
# * Dependencies
#
#  nagiosplugin      helper Python class library for Nagios plugins by Christian Kauhaus (http://pythonhosted.org/nagiosplugin)
#  purity_fb         Pure Storage Python REST Client for FlashBlade (https://github.com/purestorage/purity_fb_python_client)

__author__ = "Eugenio Grosso"
__copyright__ = "Copyright 2018, Pure Storage Inc."
__credits__ = "Christian Kauhaus"
__license__ = "Apache v2.0"
__version__ = "1.2"
__maintainer__ = "Eugenio Grosso"
__email__ = "geneg@purestorage.com"
__status__ = "Production"

"""Pure Storage FlashBlade performance indicators

   Nagios plugin to retrieve the six (6) basic KPIs from a Pure Storage FlashBlade.
   Bandwidth counters (read/write), IOPs counters (read/write) and latency (read/write) are collected from the
   target FB using the REST call.
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

"""

import argparse
import logging
import nagiosplugin
import urllib3
from purity_fb import PurityFb, ArrayPerformance, rest


_log = logging.getLogger('nagiosplugin')


class PureFBperf(nagiosplugin.Resource):
    """Pure Storage FlashBlade performance indicators

    Gets the six global KPIs of the FlashBlade and stores them in the
    metric objects
    """

    def __init__(self, endpoint, apitoken, proto=None):
        self.endpoint = endpoint
        self.apitoken = apitoken
        self.proto = proto

    @property
    def name(self):
        if (self.proto=='nfs'):
            return 'PURE_FB_NFS_PERF'
        elif (self.proto=='http'):
            return 'PURE_FB_HTTP_PERF'
        elif (self.proto=='s3'):
            return 'PURE_FB_S3_PERF'
        else:
            return 'PURE_FB_PERF'

    def get_perf(self):
        """Gets performance counters from FlashBlade."""
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        fb = PurityFb(self.endpoint)
        fb.disable_verify_ssl()
        fb.login(self.apitoken)

        if (self.proto is None):
            fbinfo = fb.arrays.list_arrays_performance()
        else:
            fbinfo = fb.arrays.list_arrays_performance(protocol=self.proto)

        fb.logout()
        return(fbinfo)


    def probe(self):

        fbinfo = self.get_perf()
        _log.debug('FB REST call returned "%s" ', fbinfo)
        wlat = int(fbinfo.items[0].usec_per_write_op)
        rlat = int(fbinfo.items[0].usec_per_read_op)
        wbw = int(fbinfo.items[0].input_per_sec)
        rbw = int(fbinfo.items[0].output_per_sec)
        wiops = int(fbinfo.items[0].writes_per_sec)
        riops = int(fbinfo.items[0].reads_per_sec)
        mlabel = 'FB '

        metrics = [
                    nagiosplugin.Metric(mlabel + 'wlat', wlat, 'us', min=0, context='wlat'),
                    nagiosplugin.Metric(mlabel + 'rlat', rlat, 'us', min=0, context='wlat'),
                    nagiosplugin.Metric(mlabel + 'wbw', wbw, '', min=0, context='wbw'),
                    nagiosplugin.Metric(mlabel + 'rbw', rbw, '', min=0, context='rbw'),
                    nagiosplugin.Metric(mlabel + 'wiops', wiops, '', min=0, context='wiops'),
                    nagiosplugin.Metric(mlabel + 'riops', riops, '', min=0, context='riops')
                  ]
        return metrics


def parse_args():
    argp = argparse.ArgumentParser()
    argp.add_argument('endpoint', help="FB hostname or ip address")
    argp.add_argument('apitoken', help="FB api_token")
    argp.add_argument('--proto', choices=('nfs', 'smb', 'http', 's3'), help="FB protocol. If omitted the whole FB performance counters are checked")
    argp.add_argument('--tw', '--ttot-warning', metavar='RANGE[,RANGE,...]',
                      type=nagiosplugin.MultiArg, default='',
                      help="positional thresholds: write_latency, read_latency, write_bandwidth, read_bandwidth, write_iops, read_iops")
    argp.add_argument('--tc', '--ttot-critical', metavar='RANGE[,RANGE,...]',
                      type=nagiosplugin.MultiArg, default='',
                      help="positional thresholds: write_latency, read_latency, write_bandwidth, read_bandwidth, write_iops, read_iops")
    argp.add_argument('-v', '--verbose', action='count', default=0,
                      help='increase output verbosity (use up to 3 times)')
    argp.add_argument('-t', '--timeout', default=30,
                      help='abort execution after TIMEOUT seconds')
    return argp.parse_args()


@nagiosplugin.guarded
def main():
    args = parse_args()
    check = nagiosplugin.Check( PureFBperf(args.endpoint, args.apitoken, args.proto) )
    check.add(nagiosplugin.ScalarContext('wlat', args.tw[0], args.tc[0]))
    check.add(nagiosplugin.ScalarContext('rlat', args.tw[1], args.tc[1]))
    check.add(nagiosplugin.ScalarContext('wbw', args.tw[2], args.tc[2]))
    check.add(nagiosplugin.ScalarContext('rbw', args.tw[3], args.tc[3]))
    check.add(nagiosplugin.ScalarContext('wiops', args.tw[4], args.tc[4]))
    check.add(nagiosplugin.ScalarContext('riops', args.tw[5], args.tc[5]))
    check.main(args.verbose, args.timeout)

if __name__ == '__main__':
    main()
