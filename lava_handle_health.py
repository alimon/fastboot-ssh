#!/usr/bin/env python3
#
# Copyright (c) 2021, Linaro Ltd.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice,
# this list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice,
# this list of conditions and the following disclaimer in the documentation
# and/or other materials provided with the distribution.
#
# 3. Neither the name of the copyright holder nor the names of its contributors
# may be used to endorse or promote products derived from this software without
# specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#
# LAVA handle health helper will set the boards in Bad status to Unknown in order
# to run health checks, remote LAB boards are shared across developers so health 
# check can fail due to board is in use by a developer.
#

import os
import yaml
import xmlrpc.client

def _load_device_config(config):
    with open(config, 'r') as f:
        return yaml.safe_load(f.read())

CONFIGS = [os.path.join(os.getcwd(), 'fastboot-ssh.conf'),
           '/etc/fastboot-ssh.conf']

username = ""
token = ""
hostname = ""  # validation.linaro.org
worker_hostname = ""
server = xmlrpc.client.ServerProxy("https://%s:%s@%s/RPC2" % (username, token, hostname), allow_none=True)

device_config = None
for c in CONFIGS:
    if os.path.exists(c):
        device_config = _load_device_config(c)
        break

hostnames = []
for d in device_config['devices']:
    if 'lava_hostname' in d:
        hostnames.append(d['lava_hostname'])
devices = server.scheduler.devices.list()

for h in hostnames:
    for d in devices:
        if h == d['hostname'] and d['health'] == 'Bad':
            server.scheduler.devices.update(h, worker_hostname, None, None, True, 'UNKNOWN', 'Created automatically by LAVA.')
