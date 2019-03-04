#!/usr/bin/env python
# Copyright (c) 2018 Pure Storage, Inc.
#
# * Overview
#
# This short Nagios/Icinga plugin code shows  how to build a simple plugin to monitor Pure Storage FlashBlade systems.
# The Pure Storage Python REST Client is used to query the FlashBlade alert messages.
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

"""Pure Storage FlashBlade alert messages status

   Nagios plugin to check the general state of a Pure Storage FlashBlade from the internal alert messages.
   The plugin has two mandatory arguments:  'endpoint', which specifies the target FB, 'apitoken', which
   specifies the autentication token for the REST call session. The FlashBlade is considered unhealty if
   there is any pending message that reports a warning or critical status of one or more components
"""

import argparse
import logging
import nagiosplugin
import urllib3
from purity_fb import PurityFb, rest


#logging.basicConfig(level=logging.DEBUG)
_log = logging.getLogger('nagiosplugin')

class PureFBalerts(nagiosplugin.Resource):
    """Pure Storage FlashBlade active alerts

    Retrieves the general health state of a FlashBlade from the internal alerts.

    """

    def __init__(self, endpoint, apitoken):
        self.endpoint = endpoint
        self.apitoken = apitoken

    @property
    def name(self):
        return 'PURE_FB_ALERTS'

    def get_alerts(self):
        """Gets active alerts from FlashBlade."""
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        fb = PurityFb(self.endpoint)
        fb.disable_verify_ssl()
        fb.login(self.apitoken)
        fbinfo = fb.alerts.list_alerts(filter='(state=\'closing\' or state=\'open\') and (severity=\'warning\' or severity=\'critical\')')
        fb.logout()
        return(fbinfo)

    def probe(self):

        fbinfo = self.get_alerts()
        _log.debug('FB REST call returned "%s" ', fbinfo)
        status = fbinfo.items
        if len(fbinfo.items) == 0:
            metric = nagiosplugin.Metric('FB_ALERTS', 0, context='default' )
        else:
            metric = nagiosplugin.Metric('FB_ALERTS', 1, context='default')
        return metric


def parse_args():
    argp = argparse.ArgumentParser()
    argp.add_argument('endpoint', help="FB hostname or ip address")
    argp.add_argument('apitoken', help="FB api_token")
    argp.add_argument('-v', '--verbose', action='count', default=0,
                      help='increase output verbosity (use up to 3 times)')
    argp.add_argument('-t', '--timeout', default=30,
                      help='abort execution after TIMEOUT seconds')
    return argp.parse_args()


@nagiosplugin.guarded
def main():
    args = parse_args()
    check = nagiosplugin.Check( PureFBalerts(args.endpoint, args.apitoken) )
    check.add(nagiosplugin.ScalarContext('default', '', '@1:1'))
    check.main(args.verbose, args.timeout)

if __name__ == '__main__':
    main()
