#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2018, Kevin Breit (@kbreit) <kevin.breit@kevinbreit.net>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = r'''
---
module: meraki_wireless_health_facts
short_description: View wireless client health information
version_added: "2.8"
description:
- Gain visibility into wireless health of clients for Meraki wireless environments.

options:
    auth_key:
        description:
        - Authentication key provided by the dashboard. Required if environmental variable MERAKI_KEY is not set.
    state:
        description:
        - Create or modify an organization.
        choices: [absent, present, query]
        default: present
    net_name:
        description:
        - Name of a network.
        aliases: [name, network]
    net_id:
        description:
        - ID number of a network.
    org_name:
        description:
        - Name of organization associated to a network.
    org_id:
        description:
        - ID of organization associated to a network.


author:
    - Kevin Breit (@kbreit)
extends_documentation_fragment: meraki
'''

EXAMPLES = r'''

'''

RETURN = r'''
data:
    description: Information about the created or manipulated object.
    returned: info
    type: complex
    contains:
      id:
        description: Identification string of network.
        returned: success
        type: string
        sample: N_12345

'''

import os
from ansible.module_utils.basic import AnsibleModule, json, env_fallback
from ansible.module_utils.urls import fetch_url
from ansible.module_utils._text import to_native
from ansible.module_utils.network.meraki.meraki import MerakiModule, meraki_argument_spec


def list_to_csv(data):
    items = str()
    for i, item in enumerate(data):
        if i == len(data):
            items = items + item
        else:
            items = items + item + ','
    return items

def main():

    # define the available arguments/parameters that a user can pass to
    # the module

    argument_spec = meraki_argument_spec()
    argument_spec.update(
        net_id=dict(type='str'),
        net_name=dict(type='str', aliases=['name', 'network']),
        type=dict(type='str', choices=['connectivity', 'latency', 'failure']),
        group_by=dict(type='str', choices=['client', 'node']),
        client=dict(type='str'),
        serial=dict(type='str', aliases=['access_point', 'ap']),
        start=dict(type='int', required=True),
        end=dict(type='int', required=True),
        ssid=dict(type='str'),
        vlan=dict(type='str'),
        fields=dict(type='list'),
        client_id=dict(type='str'),
    )

    # the AnsibleModule object will be our abstraction working with Ansible
    # this includes instantiation, a couple of common attr would be the
    # args/params passed to the execution, as well as if the module
    # supports check mode
    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=False,
                           )
    meraki = MerakiModule(module, function='wireless_health_facts')
    module.params['follow_redirects'] = 'all'
    payload = None
    key_aliases = {'start': 't0',
                   'end': 't1',
                   }
 
    connectivity_net_urls = {'wireless_health_facts': '/networks/{net_id}/connectionStats'}
    connectivity_net_group_node_urls = {'wireless_health_facts': '/networks/{net_id}/devices/connectionStats'}
    connectivity_net_group_client_urls = {'wireless_health_facts': '/networks/{net_id}/clients/connectionStats'}
    connectivity_ap_urls = {'wireless_health_facts': '/networks/{net_id}/devices/[serial]/connectionStats'}
    connectivity_client_urls = {'wireless_health_facts': '/networks/{net_id}/clients/[clientId]/connectionStats'}
    latency_net_urls = {'wireless_health_facts': '/networks/{net_id}/latencyStats'}
    latency_net_group_node_urls = {'wireless_health_facts': '/networks/{net_id}/devices/latencyStats'}
    latency_net_group_client_urls = {'wireless_health_facts': '/networks/{net_id}/clients/latencyStats'}
    latency_ap_urls = {'wireless_health_facts': '/networks/{net_id}/devices/[serial]/latencyStats'}
    latency_client_urls = {'wireless_health_facts': '/networks/{net_id}/clients/[clientId]/latencyStats'}
    failed_client_urls = {'wireless_health_facts': '/networks/{net_id}/failedConnections'}
    meraki.url_catalog['connectivity_net'] = connectivity_net_urls
    meraki.url_catalog['connectivity_net_group_node'] = connectivity_net_group_node_urls
    meraki.url_catalog['connectivity_net_group_client'] = connectivity_net_group_node_urls
    meraki.url_catalog['connectivity_ap'] = connectivity_ap_urls
    meraki.url_catalog['connectivity_client'] = connectivity_client_urls
    meraki.url_catalog['latency_net'] = latency_net_urls
    meraki.url_catalog['latency_net_group_node'] = latency_net_group_node_urls
    meraki.url_catalog['latnecy_net_group_client'] = latency_net_group_client_urls
    meraki.url_catalog['latency_ap'] = latency_ap_urls
    meraki.url_catalog['latency_client'] = latency_client_urls
    meraki.url_catalog['failed_client'] = failed_client_urls

    # validate parameters
    meraki.module.mutually_exclusive=[['net_name', 'net_id'],
                                      ['org_name', 'org_id'],
                                      ]
    if not meraki.params['net_name'] or meraki.params['net_id']:
        if not meraki.params['org_name'] and not meraki.params['org_id']:
            meraki.fail_json(msg='org_name or org_id parameters are required')
        # meraki.fail_json(msg='net_name or net_id is required')
    if meraki.params['net_name'] and meraki.params['net_id']:
        meraki.fail_json(msg='net_name and net_id are mutually exclusive')

    # if the user is working with this module in only check mode we do not
    # want to make any changes to the environment, just return the current
    # state with no modifications
    if module.check_mode:
        return meraki.result

    # Construct payload
    payload = dict()
    payload['t0'] = meraki.params['start']
    payload['t1'] = meraki.params['end']
    if meraki.params['ssid']:
        payload['ssid']= meraki.params['ssid']
    if meraki.params['vlan']:
        payload['vlan'] = meraki.params['vlan']
    if meraki.params['fields']:
        payload['fields'] = list_to_csv(meraki.params['fields'])

    # manipulate or modify the state as needed (this is going to be the
    # part where your module will do what it needs to do)

    org_id = meraki.params['org_id']
    if not org_id and meraki.params['org_name']:
        org_id = meraki.get_org_id(meraki.params['org_name'])
    net_id = meraki.params['net_id']
    if meraki.params['net_id'] is None:
        nets = meraki.get_nets(org_id=org_id)
        net_id = meraki.get_net_id(net_name=meraki.params['net_name'], data=nets)

    path = ''
    if meraki.params['type'] == 'connectivity':
        if meraki.params['group_by'] == 'client':
            path = meraki.construct_path('connectivity_net_group_client', net_id=net_id)
        elif meraki.params['group_by'] == 'node':
            path = meraki.construct_path('connectivity_net_group_node', net_id=net_id)
        else:
            path = meraki.construct_path('connectivity_net', net_id=net_id)
        path = path + meraki.encode_url_params(meraki.construct_params_list(['start', 'end'],
                                               aliases=key_aliases))
        r = meraki.request(path, method='GET', payload=json.dumps(payload))
        if meraki.status == 200:
            meraki.result['data'] = r


    # in the event of a successful module execution, you will want to
    # simple AnsibleModule.exit_json(), passing the key/value results
    meraki.exit_json(**meraki.result)


if __name__ == '__main__':
    main()
