#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2019, Kevin Breit (@kbreit) <kevin.breit@kevinbreit.net>
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
module: meraki_nat
short_description: Manage NAT rules in Meraki cloud
version_added: "2.8"
description:
- Allows for creation, management, and visibility of NAT rules (1:1, 1:many, port forwarding) within Meraki.

options:
    auth_key:
        description:
        - Authentication key provided by the dashboard. Required if environmental variable MERAKI_KEY is not set.
        type: str
    state:
        description:
        - Create or modify an organization.
        choices: [present, query]
        default: present
        type: str
    net_name:
        description:
        - Name of a network.
        aliases: [name, network]
        type: str
    net_id:
        description:
        - ID number of a network.
        type: str
    org_name:
        description:
        - Name of organization associated to a network.
        type: str
    org_id:
        description:
        - ID of organization associated to a network.
        type: str
    subset:
        description:
        - Specifies which NAT components to query.
        choices: ['1:1', '1:many', all, port_forwarding]
        default: all
        type: list
    one_to_one:
        description:
        - List of 1:1 NAT rules.
        type: list
        suboptions:
            name:
                description:
                - A descriptive name for the rule.
                type: str
            public_ip:
                description:
                - The IP address that will be used to access the internal resource from the WAN.
                type: str
            lan_ip:
                description:
                - The IP address of the server or device that hosts the internal resource that you wish to make available on the WAN.
                type: str
            uplink:
                description:
                - The physical WAN interface on which the traffic will arrive.
                choices: [both, internet1, internet2]
            allowed_inbound:
                description:
                - The ports this mapping will provide access on, and the remote IPs that will be allowed access to the resource.
                type: list
                suboptions:
                    protocol:
                        description:
                        - Protocol to apply NAT rule to.
                        choices: [any, icmp-ping, tcp, udp]
                        type: str
                        default: any
                    destination_ports:
                        description:
                        - List of ports or port ranges that will be forwarded to the host on the LAN.
                        type: list
                    allowed_ips:
                        description:
                        - ranges of WAN IP addresses that are allowed to make inbound connections on the specified ports or port ranges, or 'any'.
                        type: list
    one_to_many:
        description:
        - List of 1:many NAT rules.
        type: list
        suboptions:
            public_ip:
                description:
                - The IP address that will be used to access the internal resource from the WAN.
                type: str
            uplink:
                description:
                - The physical WAN interface on which the traffic will arrive.
                choices: [both, internet1, internet2]
                type: str
            port_rules:
                description:
                - List of associated port rules.
                type: list
                suboptions:
                    name:
                        description:
                        - A description of the rule.
                        type: str
                    protocol:
                        description:
                        - Protocol to apply NAT rule to.
                        choices: [tcp, udp]
                        type: str
                    public_port:
                        description:
                        - Destination port of the traffic that is arriving on the WAN.
                        type: str
                    local_ip:
                        description:
                        - Local IP address to which traffic will be forwarded.
                        type: str
                    local_port:
                        description:
                        - Destination port of the forwarded traffic that will be sent from the MX to the specified host on the LAN.
                        - If you simply wish to forward the traffic without translating the port, this should be the same as the Public port.
                        type: str
                    allowed_ips:
                        description:
                        - Remote IP addresses or ranges that are permitted to access the internal resource via this port forwarding rule, or 'any'.
                        type: list
    port_forwarding:
        description:
        - List of port forwarding rules.
        type: list
        suboptions:
            name:
                description:
                - A descriptive name for the rule.
                type: str
            lan_ip:
                description:
                - The IP address of the server or device that hosts the internal resource that you wish to make available on the WAN.
                type: str
            uplink:
                description:
                - The physical WAN interface on which the traffic will arrive.
                choices: [both, internet1, internet2]
                type: str
            public_port:
                description:
                - A port or port ranges that will be forwarded to the host on the LAN.
                type: str
            local_port:
                description:
                - A port or port ranges that will receive the forwarded traffic from the WAN.
                type: str
            allowed_ips:
                description:
                - List of ranges of WAN IP addresses that are allowed to make inbound connections on the specified ports or port ranges (or any).
            protocol:
                description:
                - Protocol to forward traffic for.
                choices: [tcp, udp]
                type: str

author:
    - Kevin Breit (@kbreit)
extends_documentation_fragment: meraki
'''

EXAMPLES = r'''
- name: Query all NAT rules
  meraki_nat:
    auth_key: abc123
    org_name: YourOrg
    net_name: YourNet
    state: query
    subset: all
  delegate_to: localhost

- name: Query 1:1 NAT rules
  meraki_nat:
    auth_key: abc123
    org_name: YourOrg
    net_name: YourNet
    state: query
    subset: '1:1'
  delegate_to: localhost

- name: Create 1:1 rule
  meraki_nat:
    auth_key: abc123
    org_name: YourOrg
    net_name: YourNet
    state: present
    one_to_one:
      - name: Service behind NAT
        public_ip: 1.2.1.2
        lan_ip: 10.200.1.10
        uplink: both
        allowed_inbound:
          - protocol: tcp
            destination_ports: 80
            allowed_ips: 10.10.10.10
  delegate_to: localhost

- name: Create 1:many rule
  meraki_nat:
    auth_key: abc123
    org_name: YourOrg
    net_name: YourNet
    state: present
    one_to_many:
      - name: Test map
        public_ip: 1.1.1.1
        lan_ip: 10.200.1.10
        uplink: both
        protocol: tcp
        allowed_ips:
          - 1.1.1.1
        port_rules:
          - Hello
        public_port: 10
        local_ip: 1.1.1.1
        local_port: 11
  delegate_to: localhost

- name: Create port forwarding rule
  meraki_nat:
    auth_key: abc123
    org_name: YourOrg
    net_name: YourNet
    state: present
    port_forwarding:
      - name: Test map
        lan_ip: 10.200.1.10
        uplink: both
        protocol: tcp
        allowed_ips:
          - 1.1.1.1
        public_port: 10
        local_port: 11
  delegate_to: localhost
'''

RETURN = r'''
data:
    description: Information about the created or manipulated object.
    returned: success
    type: complex
    contains:
        one_to_one:
            description: Information about 1:1 NAT object.
            returned: success, when 1:1 NAT object is in task
            type: complex
            contains:
                rules:
                    description: List of 1:1 NAT rules.
                    returned: success, when 1:1 NAT object is in task
                    type: complex
                    contains:
                        name:
                            description: Name of NAT object.
                            returned: success, when 1:1 NAT object is in task
                            type: string
                            example: Web server behind NAT
                        lanIp:
                            description: Local IP address to be mapped.
                            returned: success, when 1:1 NAT object is in task
                            type: string
                            example: 192.168.128.22
                        publicIp:
                            description: Public IP address to be mapped.
                            returned: success, when 1:1 NAT object is in task
                            type: string
                            example: 148.2.5.100
                        uplink:
                            description: Internet port where rule is applied.
                            returned: success, when 1:1 NAT object is in task
                            type: string
                            example: internet1
                        allowedInbound:
                            description: List of inbound forwarding rules.
                            returned: success, when 1:1 NAT object is in task
                            type: complex
                            contains:
                                protocol:
                                    description: Protocol to apply NAT rule to.
                                    returned: success, when 1:1 NAT object is in task
                                    type: string
                                    example: tcp
                                allowedIps:
                                    description: List of IP addresses to be forwarded.
                                    returned: success, when 1:1 NAT object is in task
                                    type: list
                                    example: 10.80.100.0/24
        one_to_many:
            description: Information about 1:many NAT object.
            returned: success, when 1:many NAT object is in task
            type: complex
            contains:
                rules:
                    description: List of 1:many NAT rules.
                    returned: success, when 1:many NAT object is in task
                    type: complex
                    contains:
                        publicIp:
                            description: Public IP address to be mapped.
                            returned: success, when 1:many NAT object is in task
                            type: string
                            example: 148.2.5.100
                        uplink:
                            description: Internet port where rule is applied.
                            returned: success, when 1:many NAT object is in task
                            type: string
                            example: internet1
                        portRules:
                            description: List of NAT port rules.
                            returned: success, when 1:many NAT object is in task
                            type: complex
                            contains:
                                name:
                                    description: Name of NAT object.
                                    returned: success, when 1:many NAT object is in task
                                    type: string
                                    example: Web server behind NAT
                                protocol:
                                    description: Protocol to apply NAT rule to.
                                    returned: success, when 1:1 NAT object is in task
                                    type: string
                                    example: tcp
                                publicPort:
                                    description: Destination port of the traffic that is arriving on WAN.
                                    returned: success, when 1:1 NAT object is in task
                                    type: int
                                    example: 9443
                                localIp:
                                    description: Local IP address traffic will be forwarded.
                                    returned: success, when 1:1 NAT object is in task
                                    type: string
                                    example: 192.0.2.10
                                localPort:
                                    description: Destination port to be forwarded to.
                                    returned: success, when 1:1 NAT object is in task
                                    type: int
                                    example: 443
                                allowedIps:
                                    description: List of IP addresses to be forwarded.
                                    returned: success, when 1:1 NAT object is in task
                                    type: list
                                    example: 10.80.100.0/24
        port_forwarding:
            description: Information about port forwarding rules.
            returned: success, when port forwarding is in task
            type: complex
            contains:
                rules:
                    description: List of port forwarding rules.
                    returned: success, when port forwarding is in task
                    type: complex
                    contains:
                        lanIp:
                            description: Local IP address to be mapped.
                            returned: success, when port forwarding is in task
                            type: string
                            example: 192.168.128.22
                        allowedIps:
                            description: List of IP addresses to be forwarded.
                            returned: success, when port forwarding is in task
                            type: list
                            example: 10.80.100.0/24
                        name:
                            description: Name of NAT object.
                            returned: success, when port forwarding is in task
                            type: string
                            example: Web server behind NAT
                        protocol:
                            description: Protocol to apply NAT rule to.
                            returned: success, when port forwarding is in task
                            type: string
                            example: tcp
                        publicPort:
                            description: Destination port of the traffic that is arriving on WAN.
                            returned: success, when port forwarding is in task
                            type: int
                            example: 9443
                        localPort:
                            description: Destination port to be forwarded to.
                            returned: success, when port forwarding is in task
                            type: int
                            example: 443
                        uplink:
                            description: Internet port where rule is applied.
                            returned: success, when port forwarding is in task
                            type: string
                            example: internet1
'''

import os
from ansible.module_utils.basic import AnsibleModule, json, env_fallback
from ansible.module_utils.urls import fetch_url
from ansible.module_utils._text import to_native
from ansible.module_utils.network.meraki.meraki import MerakiModule, meraki_argument_spec

key_map = {'name': 'name',
           'public_ip': 'publicIp',
           'lan_ip': 'lanIp',
           'uplink': 'uplink',
           'allowed_inbound': 'allowedInbound',
           'protocol': 'protocol',
           'destination_ports': 'destinationPorts',
           'allowed_ips': 'allowedIps',
           'port_rules': 'portRules',
           'public_port': 'publicPort',
           'local_ip': 'localIp',
           'local_port': 'localPort',
           }


def construct_payload(params):
    if isinstance(params, list):
        items = []
        for item in params:
            items.append(construct_payload(item))
        return items
    elif isinstance(params, dict):
        info = {}
        for param in params:
            info[key_map[param]] = construct_payload(params[param])
        return info
    elif isinstance(params, str) or isinstance(params, int):
        return params


def main():

    # define the available arguments/parameters that a user can pass to
    # the module

    one_to_one_allowed_inbound_spec = dict(protocol=dict(type='str', choices=['tcp', 'udp', 'icmp-ping', 'any'], default='any'),
                                           destination_ports=dict(type='list'),
                                           allowed_ips=dict(type='list'),
                                           )

    one_to_one_spec = dict(name=dict(type='str'),
                           public_ip=dict(type='str'),
                           lan_ip=dict(type='str'),
                           uplink=dict(type='str', choices=['internet1', 'internet2', 'both']),
                           allowed_inbound=dict(type='list', element='dict', options=one_to_one_allowed_inbound_spec),
                           )

    one_to_many_spec = dict(name=dict(type='str'),
                            public_ip=dict(type='str'),
                            lan_ip=dict(type='str'),
                            uplink=dict(type='str', choices=['internet1', 'internet2', 'both']),
                            protocol=dict(type='str', choices=['tcp', 'udp']),
                            allowed_ips=dict(type='list'),
                            port_rules=dict(type='list'),
                            public_port=dict(type='int'),
                            local_ip=dict(type='str'),
                            local_port=dict(type='str'),
                            )

    port_forwarding_spec = dict(name=dict(type='str'),
                                lan_ip=dict(type='str'),
                                uplink=dict(type='str', choices=['internet1', 'internet2', 'both']),
                                protocol=dict(type='str', choices=['tcp', 'udp']),
                                public_port=dict(type='int'),
                                local_port=dict(type='int'),
                                allowed_ips=dict(type='list'),
                                )

    argument_spec = meraki_argument_spec()
    argument_spec.update(
        net_id=dict(type='str'),
        net_name=dict(type='str', aliases=['name', 'network']),
        state=dict(type='str', choices=['present', 'query'], default='present'),
        subset=dict(type='list', choices=['1:1', '1:many', 'all', 'port_forwarding'], default='all'),
        one_to_one=dict(type='list', element='dict', options=one_to_one_spec),
        one_to_many=dict(type='list', element='dict', options=one_to_many_spec),
        port_forwarding=dict(type='list', element='dict', options=port_forwarding_spec),
    )

    # the AnsibleModule object will be our abstraction working with Ansible
    # this includes instantiation, a couple of common attr would be the
    # args/params passed to the execution, as well as if the module
    # supports check mode
    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=False,
                           )

    meraki = MerakiModule(module, function='nat')
    module.params['follow_redirects'] = 'all'

    one_to_one_payload = None
    one_to_many_payload = None
    port_forwarding_payload = None
    if meraki.params['state'] == 'present':
        if meraki.params['one_to_one'] is not None:
            one_to_one_payload = {'rules': construct_payload(meraki.params['one_to_one'])}
        if meraki.params['one_to_many'] is not None:
            one_to_many_payload = {'rules': construct_payload(meraki.params['one_to_many'])}
        if meraki.params['port_forwarding'] is not None:
            port_forwarding_payload = {'rules': construct_payload(meraki.params['port_forwarding'])}

    # meraki.fail_json(msg="Payload", one_to_one=one_to_one_payload)
    # meraki.fail_json(msg="Payload", one_to_many=one_to_many_payload)
    # meraki.fail_json(msg="Payload", port_forwarding=port_forwarding_payload)

    onetomany_urls = {'nat': '/networks/{net_id}/oneToOneNatRules'}
    onetoone_urls = {'nat': '/networks/{net_id}/oneToManyNatRules'}
    port_forwarding_urls = {'nat': '/networks/{net_id}/portForwardingRules'}
    meraki.url_catalog['1:many'] = onetomany_urls
    meraki.url_catalog['1:1'] = onetoone_urls
    meraki.url_catalog['port_forwarding'] = port_forwarding_urls

    if meraki.params['net_name'] and meraki.params['net_id']:
        meraki.fail_json(msg='net_name and net_id are mutually exclusive')

    org_id = meraki.params['org_id']
    if not org_id:
        org_id = meraki.get_org_id(meraki.params['org_name'])
    net_id = meraki.params['net_id']
    if net_id is None:
        nets = meraki.get_nets(org_id=org_id)
        net_id = meraki.get_net_id(org_id, meraki.params['net_name'], data=nets)

    if meraki.params['state'] == 'query':
        if meraki.params['subset'][0] == 'all':
            path = meraki.construct_path('1:many', net_id=net_id)
            data = {'1:many': meraki.request(path, method='GET')}
            path = meraki.construct_path('1:1', net_id=net_id)
            data['1:1'] = meraki.request(path, method='GET')
            path = meraki.construct_path('port_forwarding', net_id=net_id)
            data['port_forwarding'] = meraki.request(path, method='GET')
            meraki.result['data'] = data
        else:
            for subset in meraki.params['subset']:
                path = meraki.construct_path(subset, net_id=net_id)
                data = {subset: meraki.request(path, method='GET')}
                try:
                    meraki.result['data'][subset] = data
                except KeyError:
                    meraki.result['data'] = {subset: data}
    elif meraki.params['state'] == 'present':
        if one_to_one_payload is not None:
            path = meraki.construct_path('1:1', net_id=net_id)
            current = meraki.request(path, method='GET')
            if meraki.is_update_required(current, one_to_one_payload):
                r = meraki.request(path, method='PUT')
                if meraki.status == 200:
                    meraki.result['data'] = {'one_to_one': r}
                    meraki.result['changed'] = True
        if one_to_many_payload is not None:
            path = meraki.construct_path('1:many', net_id=net_id)
            current = meraki.request(path, method='GET')
            if meraki.is_update_required(current, one_to_many_payload):
                r = meraki.request(path, method='PUT')
                if meraki.status == 200:
                    meraki.result['data'] = {'one_to_many': r}
                    meraki.result['changed'] = True
        if port_forwarding_payload is not None:
            path = meraki.construct_path('port_forwarding', net_id=net_id)
            current = meraki.request(path, method='GET')
            if meraki.is_update_required(current, port_forwarding_payload):
                r = meraki.request(path, method='PUT')
                if meraki.status == 200:
                    meraki.result['data'] = {'port_forwarding': r}
                    meraki.result['changed'] = True

    # in the event of a successful module execution, you will want to
    # simple AnsibleModule.exit_json(), passing the key/value results
    meraki.exit_json(**meraki.result)


if __name__ == '__main__':
    main()
