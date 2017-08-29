import nova.conf

from hastack.has.conf import client
from hastack.has.conf import ha

CONF = nova.conf.CONF

client.register_opts(CONF)
ha.register_opts(CONF)
