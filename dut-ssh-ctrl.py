#!/usr/bin/env python3
#
# Copyright (c) 2018, Linaro Ltd.
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
# Device Under Test (DUT) command execution
#

import sys
import os
import subprocess
import yaml
import signal


CONFIGS = [os.path.join(os.getcwd(), 'dut-ssh.conf'),
           '/etc/dut-ssh.conf']
if 'DUT_SSH_CONFIG' in os.environ:
    CONFIGS.insert(0, os.environ['DUT_SSH_CONFIG'])


def _execute_command(cmd):
    rc = 0
    try:
        rc = subprocess.check_call(cmd, shell=True)
    except subprocess.CalledProcessError as e:
        rc = e.returncode
    except KeyboardInterrupt as e:
        rc = signal.SIGINT
    return rc


def _load_device_config(config):
    with open(config, 'rb') as f:
        return yaml.load(f.read())


def _get_device_by_name(device_config, device_name):
    for device in device_config['devices']:
        if device['board'] == device_name:
            return device
    return None


def _get_device_remote_command(cmd, remote_commands):
    for rcmd in remote_commands:
        if cmd in rcmd:
            return rcmd[cmd]
    return None


def main():
    if len(sys.argv) < 3:
        print("ERROR: Usage: %s <device> <console|power_on|power_off|hard_reset>" % sys.argv[0])
        sys.exit(1)

    device_config = None
    for c in CONFIGS:
        if os.path.exists(c):
            device_config = _load_device_config(c)
            break

    device_name = sys.argv[1]
    cmd = sys.argv[2]

    device = _get_device_by_name(device_config, device_name)
    rc = 0
    if device:
        remote_cmd = _get_device_remote_command(cmd, device['commands'])
        if remote_cmd:
            ssh_cmd = 'ssh %s \"%s\"' % (device['host'], remote_cmd)
            rc = _execute_command(ssh_cmd)
        else:
            print("ERROR: No command %s in device %s" % (cmd, device_name))
            rc = 3
    else:
        print("ERROR: No device %s found" % device_name)
        rc = 2

    return rc


if __name__ == '__main__':
    try:
        ret = main()
    except Exception:
        ret = 1
        import traceback
        traceback.print_exc()
    sys.exit(ret)
