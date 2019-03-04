#!/usr/bin/env python
# Copyright (c) 2018 Pure Storage, Inc.
#
# * Overview
#
# This short Nagios/Icinga plugin code shows  how to build a simple plugin to monitor Pure Storage FlashBlade systems.
# The Pure Storage Python REST Client is used to query the FlashBlade hardware compoment status.
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

"""Pure Storage FlashBlade hardware components status

   Nagios plugin to retrieve the current status of hardware components from a Pure Storage FlashBlade.
   Hardware status indicators are collected from the target FA using the REST call.
   The plugin has three mandatory arguments:  'endpoint', which specifies the target FB, 'apitoken', which
   specifies the autentication token for the REST call session and 'component', that is the name of the
   hardware component to be monitored. The component must be specified using the internal naming schema of
   the Pure FlashBlade: i.e CH1 for the main chassis, CH1.FM1 for the primary flash module, CH1.FM2 for the secondary,
   CH1.FB1 for the first blade of first chassis, CH1.FB2 for the secondary blade, CH2 for the second chained FlashBlade
   and so on.
"""

import argparse
import logging
import nagiosplugin
import urllib3
from purity_fb import PurityFb, Hardware, rest


_log = logging.getLogger('nagiosplugin')

class PureFBhw(nagiosplugin.Resource):
    """Pure Storage FlashBlade hardware component status

    Retrieves the currents operating status of a specified hardware component

    """

    def __init__(self, endpoint, apitoken, component):
        self.endpoint = endpoint
        self.apitoken = apitoken
        self.component = component

    @property
    def name(self):
        return 'PURE_FB_' + str(self.component)

    def get_status(self):
        """Gets hardware component status from FlashBlade."""
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        fb = PurityFb(self.endpoint)
        fb.disable_verify_ssl()
        fb.login(self.apitoken)
        fbinfo = fb.hardware.list_hardware(names=[self.component])
        fb.logout()
        return(fbinfo)

    def probe(self):

        fbinfo = self.get_status()
        _log.debug('FB REST call returned "%s" ', fbinfo)
        status = fbinfo.items[0].status
        if (status == 'healthy') or (status == 'unused'):
            metric = nagiosplugin.Metric(self.component + ' status', 0, context='default' )
        else:
            metric = nagiosplugin.Metric(self.component + ' status', 1, context='default')
        return metric


def parse_args():
    argp = argparse.ArgumentParser()
    argp.add_argument('endpoint', help="FB hostname or ip address")
    argp.add_argument('apitoken', help="FB api_token")
    argp.add_argument('component', help="FB hardware component")
    argp.add_argument('-v', '--verbose', action='count', default=0,
                      help='increase output verbosity (use up to 3 times)')
    argp.add_argument('-t', '--timeout', default=30,
                      help='abort execution after TIMEOUT seconds')
    return argp.parse_args()


@nagiosplugin.guarded
def main():
    args = parse_args()
    check = nagiosplugin.Check( PureFBhw(args.endpoint, args.apitoken, args.component) )
    check.add(nagiosplugin.ScalarContext('default', '', '@1:1'))
    check.main(args.verbose, args.timeout)

if __name__ == '__main__':
    main()
