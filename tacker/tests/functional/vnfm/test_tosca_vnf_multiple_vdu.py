# Copyright 2016 Brocade Communications System, Inc.
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from oslo_config import cfg
from toscaparser.tosca_template import ToscaTemplate
import yaml

from tacker.common import utils
from tacker.tests import constants
from tacker.tests.functional import base
from tacker.tests.utils import read_file
from tacker.vm.tosca import utils as toscautils

CONF = cfg.CONF


class VnfTestToscaMultipleVDU(base.BaseTackerTest):
    def test_create_delete_tosca_vnf_with_multiple_vdus(self):
        data = dict()
        input_yaml = read_file('sample-tosca-vnfd-multi-vdu.yaml')
        data['tosca'] = input_yaml
        toscal = data['tosca']
        vnfd_name = 'sample-tosca-vnfd-multi-vdu'
        tosca_arg = {'vnfd': {'name': vnfd_name,
                              'attributes': {'vnfd': toscal}}}

        # Create vnfd with tosca template
        vnfd_instance = self.client.create_vnfd(body=tosca_arg)
        self.assertIsNotNone(vnfd_instance)

        # Create vnf with vnfd_id
        vnfd_id = vnfd_instance['vnfd']['id']
        vnf_arg = {'vnf': {'vnfd_id': vnfd_id, 'name':
                           "test_tosca_vnf_with_multiple_vdus"}}
        vnf_instance = self.client.create_vnf(body=vnf_arg)

        vnf_id = vnf_instance['vnf']['id']
        self.wait_until_vnf_active(vnf_id,
                                   constants.VNF_CIRROS_CREATE_TIMEOUT,
                                   constants.ACTIVE_SLEEP_TIME)
        self.assertEqual('ACTIVE',
                         self.client.show_vnf(vnf_id)['vnf']['status'])
        self.validate_vnf_instance(vnfd_instance, vnf_instance)

        # Validate mgmt_url with input yaml file
        mgmt_url = self.client.show_vnf(vnf_id)['vnf']['mgmt_url']
        self.assertIsNotNone(mgmt_url)
        mgmt_dict = yaml.load(str(mgmt_url))

        input_dict = yaml.load(input_yaml)
        toscautils.updateimports(input_dict)

        tosca = ToscaTemplate(parsed_params={}, a_file=False,
                          yaml_dict_tpl=input_dict)

        vdus = toscautils.findvdus(tosca)

        self.assertEqual(len(vdus), len(mgmt_dict.keys()))
        for vdu in vdus:
            self.assertIsNotNone(mgmt_dict[vdu.name])
            self.assertEqual(True, utils.is_valid_ipv4(mgmt_dict[vdu.name]))

        # Delete vnf_instance with vnf_id
        try:
            self.client.delete_vnf(vnf_id)
        except Exception:
            assert False, "vnf Delete of test_vnf_with_multiple_vdus failed"

        # Delete vnfd_instance
        self.addCleanup(self.client.delete_vnfd, vnfd_id)
        self.addCleanup(self.wait_until_vnf_delete, vnf_id,
            constants.VNF_CIRROS_DELETE_TIMEOUT)
