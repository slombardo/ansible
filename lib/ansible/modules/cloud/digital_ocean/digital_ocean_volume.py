#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: digital_ocean_volume  
short_description: Create and delete Digital Ocean block storage volumes.
description:
    - Create and delete Digital Ocean block storage volumes.
author: "Kevin Breit (@kbreit)"
version_added: "2.8"
options:
  name:
    description:
      - Name of project.
      - Maximum of 255 characters.
  id:
    description:
      - ID number of project as assigned by DigitalOcean.

extends_documentation_fragment: digital_ocean.documentation
notes:
  - Two environment variables can be used, DO_API_KEY and DO_API_TOKEN.
    They both refer to the v2 token.
  - As of Ansible 2.0, Version 2 of the DigitalOcean API is used.

requirements:
  - "python >= 2.6"
'''


EXAMPLES = '''
- name: Create a new project
  digital_ocean_project:
    oauth_token: abc123
    state: present
    name: Web Frontends
    description: Contains all corporate web frontends
    purpose: Web application
    environment: Production

- name: Assign a resource to an existing project
  digital_ocean_project:
    oauth_token: abc123
    state: present
    name: Web Frontends
    resources:
      - "do:droplet:1"
      - "do:volume:42"

- name: Assign a resource to the default project
  digital_ocean_project:
    oauth_token: abc123
    state: present
    default: yes
    resources:
      - "do:droplet:1"
      - "do:volume:42"

- name: Modify properties of an existing project
  digital_ocean_project:
    oauth_token: abc123
    state: present
    name: Web Frontends
    description: Contains all corporate public web frontends
    purpose: Web application
    environment: Production
    default: no
'''


RETURN = '''
data:
    description: a DigitalOcean Tag resource
    returned: success and no resource constraint
    type: dict
    sample: {
        "tag": {
        "name": "awesome",
        "resources": {
          "droplets": {
            "count": 0,
            "last_tagged": null
          }
        }
      }
    }
'''

from traceback import format_exc
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.digital_ocean import DigitalOceanHelper
from ansible.module_utils._text import to_native


def get_all_volumes(rest):
    response = rest.get('volumes')
    if response.status_code == 200:
        return response.json


def get_snaps(rest, vid):
    response = rest.get('volumes/{0}/snapshots'.format(vid))
    if response.status_code == 200:
        return response.json


def get_vid(name, volumes):
    for volume in volumes:
        if volume['name'] == name:
            return volume['id']
    return False


def get_snap_id(name, snaps):
    for snap in snaps:
        if name == snap['name']:
            return snap['id']
        return False


def core(module):
    name = module.params['name']
    vid = module.params['id']
    rest = DigitalOceanHelper(module)

    if vid is None and name is not None:
        vid = get_vid(name, get_all_volumes(rest)['volumes'])

    if module.params['state'] == 'present':
        payload = {'name': name,
                   }
        if module.params['snapshot_id'] is None:
            payload['region'] = module.params['region']
            payload['size_gigabytes'] = module.params['size_gigabytes']
            payload['description'] = module.params['description']
            if module.params['filesystem_label'] is not None:
                payload['filesystem_type'] = module.params['filesystem_type']
            if module.params['filesystem_label'] is not None:
                payload['filesystem_label'] = module.params['filesystem_label']
        else:
            payload['snapshot_id'] = module.params['snapshot_id']
        if module.params['snapshot'] is False or module.params['snapshot'] is None:
            # module.fail_json(msg=payload)
            response = rest.post('volumes', data=payload)
        else:
            # module.fail_json(msg=get_snaps(rest, vid))
            response = rest.post('volumes/{0}/snapshots'.format(vid), data=payload) 
        if response.status_code == 201:
            module.exit_json(changed=True, data=response.json)
        else:
            module.fail_json(msg=response.json)
    elif module.params['state'] == 'absent':
        if module.params['snapshot_id'] is None:
            response = rest.delete('volumes/{0}'.format(vid))
        else:
            response = rest.delete('snapshots/{0}'.format(vid))
        if response.status_code == 204:
            module.exit_json(changed=True)
    module.exit_json(changed=False)



def main():
    argument_spec = DigitalOceanHelper.digital_ocean_argument_spec()
    argument_spec.update(
        size_gigabytes=dict(type='int'),
        name=dict(type='str'),
        description=dict(type='str'),
        id=dict(type='str'),
        region=dict(type='str'),
        snapshot_id=dict(type='str'),
        filesystem_type=dict(type='str'),
        filesystem_label=dict(type='str'),
        state=dict(type='str', choices=['absent', 'present'], default='present'),
        snapshot=dict(type='bool'),
    )

    module = AnsibleModule(argument_spec=argument_spec)

    try:
        core(module)
    except Exception as e:
        module.fail_json(msg=to_native(e), exception=format_exc())


if __name__ == '__main__':
    main()
