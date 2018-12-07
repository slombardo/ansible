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
      - Name of volume or snapshot.
      - Value is name of snapshot, if snapshot is true.
  description:
    description:
      - Description of volume.
  id:
    description:
      - ID number of volume as assigned by DigitalOcean.
  size_gigabytes:
    description:
      - Number of gigabytes to allocate to volume.
    type: int
  resize_gigabytes:
    description:
      - Number of gigabytes to grow volume to.
      - Volumes can only be increased in size.
    type: int
  region:
    description:
      - Digital Ocean region to create volume in.
  snapshot:
    description:
      - If true, actions are performed against snapshot instead of volume.
    type: bool
  snapshot_id:
    description:
      - ID number of snapshot.
  state:
    description:
      - Whether to create/modify, or delete a volume.
      - Present will attach to a droplet if droplet information is provided. Absent will detach from a droplet if droplet information is provided.
    choices: ['absent', 'present']
    default: present
  filesystem_type:
    description:
      - Filesystem of volume to create.
  filesystem_label:
    description:
      - Filesystems labels for volume.
  droplet_name:
    description:
      - Name of droplet to attach volume to or detach from.
  droplet_id:
    description:
      - ID of droplet to attach volume to or detach from.

extends_documentation_fragment: digital_ocean.documentation
notes:
  - Two environment variables can be used, DO_API_KEY and DO_API_TOKEN.
    They both refer to the v2 token.
  - As of Ansible 2.0, Version 2 of the DigitalOcean API is used.

requirements:
  - "python >= 2.6"
'''


EXAMPLES = '''
- name: Create volume
  digital_ocean_volume:
    oauth_token: abc123
    state: present
    name: ansiblevolume
    size_gigabytes: 1
    description: Ansible test volume
    region: nyc1

- name: Convert to snapshot
  digital_ocean_volume:
    oauth_token: abc123
    state: present
    name: ansiblevolume
    snapshot: yes
      
- name: Attach to existing Droplet by name
  digital_ocean_volume:
    oauth_token: abc123
    state: present
    name: ansiblevolume
    resize_gigabytes: 2
      
- name: Attach to existing Droplet by name
  digital_ocean_volume:
    oauth_token: abc123
    state: present
    name: ansiblevolume
    region: nyc1
    droplet_name: web_server

- name: Detach Droplet
  digital_ocean_volume:
    oauth_token: abc123
    state: absent
    name: ansiblevolume
    droplet_name: web_server

- name: Attach Droplet by ID
  digital_ocean_volume:
    oauth_token: abc123
    state: present
    name: ansiblevolume
    droplet_id: 1234567890

- name: Detach Droplet by ID
  digital_ocean_volume:
    oauth_token: abc123
    state: absent
    name: ansiblevolume
    droplet_id: 1234567890

- name: Delete snapshot
  digital_ocean_volume:
    oauth_token: abc123
    state: absent
    name: ansiblevolume
    snapshot: yes

- name: Delete volume
  digital_ocean_volume:
    oauth_token: abc123
    state: absent
    name: ansiblevolume
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
        
        
def get_droplets(rest):
    response = rest.get_paginated_data(base_url='droplets?', data_key_name='droplets')
    return response


def get_vid(name, volumes):
    for volume in volumes:
        if volume['name'] == name:
            return volume['id']
    return False


def get_sid(name, snaps):
    for snap in snaps:
        if name == snap['name']:
            return snap['id']
        return False
        
def get_did(name, droplets):
    for droplet in droplets:
        if name == droplet['name']:
            return droplet['id']
        return False


def core(module):
    name = module.params['name']
    vid = module.params['id']
    sid = module.params['snapshot_id']
    did = module.params['droplet_id']
    rest = DigitalOceanHelper(module)

    if name:
        vid = get_vid(name, get_all_volumes(rest)['volumes'])
    if module.params['snapshot']:
        if sid is None and name is not None:
            sid = get_sid(name, get_snaps(rest, vid)['snapshots'])
    if module.params['droplet_name']:
        # module.fail_json(msg=get_droplets(rest))
        did = get_did(module.params['droplet_name'], get_droplets(rest))

    if module.params['state'] == 'present':
        if module.params['resize_gigabytes']:  # Resize volume
            payload = {'type': 'resize',
                       'size': module.params['resize_gigabytes'],
                       }
            response = rest.post('volumes/{0}/action'.format(vid), payload)
            if response.status_code == 202:
                module.exit_json(changed=True, data=response.json)
            else:
                module.fail_json(changed=False)
        elif did:  # Attach volume to droplet
            payload = {'type': 'attach',
                       'droplet_id': did,
                       }
            if name:
                payload['volume_name'] = name
            response = rest.post('volumes/actions', payload)
            if response.status_code == 202:
                module.exit_json(changed=True, data=response.json)
            else:
                module.fail_json(msg=response.status_code)
        
        # If there's no action to perform, keep going
        payload = {'name': name}
        if module.params['snapshot'] is not True:  # Create volume
            payload['region'] = module.params['region']
            payload['size_gigabytes'] = module.params['size_gigabytes']
            payload['description'] = module.params['description']
            if module.params['filesystem_label'] is not None:
                payload['filesystem_type'] = module.params['filesystem_type']
            if module.params['filesystem_label'] is not None:
                payload['filesystem_label'] = module.params['filesystem_label']
            response = rest.post('volumes', data=payload)
        else:
            response = rest.post('volumes/{0}/snapshots'.format(vid), data=payload)  # Create snapshot
        if response.status_code == 201:
            module.exit_json(changed=False, data=response.json)
        elif response.status_code == 409:  # Error of some sort
            # TODO: Allow data to be returned
            module.exit_json(changed=True, data='{0} - {1}'.format(response.json['id'], response.json['message']))
        else:
            module.fail_json(msg=response.json)
    elif module.params['state'] == 'absent':
        if did is not None and did is not False:  # Detach volume from droplet
            payload = {'type': 'detach',
                       'droplet_id': did,
                       }
            if module.params['region']:
                payload['region'] = module.params['region']
            # module.fail_json(msg=payload)
            response = rest.post('volumes/{0}/actions'.format(vid), data=payload)
            if response.status_code == 202:
                module.exit_json(changed=True)
            else:
                module.fail_json(msg=response.info)
        if module.params['snapshot'] is None:  # Delete a volume
            response = rest.delete('volumes/{0}'.format(vid))
        else:  # Delete a snapshot
            response = rest.delete('snapshots/{0}'.format(sid))
        if response.status_code == 204:
            module.exit_json(changed=True)
    module.exit_json(changed=False)


def main():
    argument_spec = DigitalOceanHelper.digital_ocean_argument_spec()
    argument_spec.update(
        size_gigabytes=dict(type='int', aliases=['size']),
        resize_gigabytes=dict(type='int', aliases=['resize']),
        name=dict(type='str'),
        description=dict(type='str'),
        id=dict(type='str'),
        region=dict(type='str'),
        snapshot_id=dict(type='str'),
        filesystem_type=dict(type='str'),
        filesystem_label=dict(type='str'),
        state=dict(type='str', choices=['absent', 'present'], default='present'),
        snapshot=dict(type='bool'),
        droplet_name=dict(type='str'),
        droplet_id=dict(type='str'),
    )
    
    mutually_exclusive = [['name', 'id'],
                          ['droplet_name', 'droplet_id'],
                          ['droplet_name', 'resize_size'],
                          ['droplet_id', 'resize_size'],
                          ]

    module = AnsibleModule(argument_spec=argument_spec)
                           # mututally_exclusive=mutually_exclusive)

    try:
        core(module)
    except Exception as e:
        module.fail_json(msg=to_native(e), exception=format_exc())


if __name__ == '__main__':
    main()
