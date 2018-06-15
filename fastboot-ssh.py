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
# Fastboot SSH wrapper, executes fastboot over ssh connection, handling the copy
# of files in boot, flash, flash:raw and update commands to the remote host.
#

import sys
import os
import subprocess
import yaml
import signal


FASTBOOT_CMD = "/usr/bin/fastboot"
CONFIGS = [os.path.join(os.getcwd(), 'dut-ssh.conf'),
           '/etc/dut-ssh.conf']
if 'DUT_SSH_CONFIG' in os.environ:
    CONFIGS.insert(0,os.environ['DUT_SSH_CONFIG'])
REMOTE_FASTBOOT_DIR='lava-fastboot'


def _execute_command(cmd):
    rc = 0
    try:
        rc = subprocess.check_call(cmd)
    except subprocess.CalledProcessError as e:
        rc = e.returncode
    except KeyboardInterrupt as e:
        rc = signal.SIGINT
    return rc


def _load_device_config(config):
    with open(config, 'r') as f:
        return yaml.load(f.read())


def _fastboot_get_device_serial():
    found = False
    serial = None

    for arg in sys.argv[1:]:
        if found:
            serial = arg
            break

        if arg == '-s':
            found = True

    return serial


def _get_device_by_serial(device_config, device_serial):
    for device in device_config['devices']:
        if device['fastboot_serial'] == device_serial:
            return device

    return None


def _handle_fastboot_files(device):
    fastboot_cmds = {'boot' : 1, 'flash' : 2, 'flash:raw' : 2, 'update' : 1}
    remote_files = []

    fcmd_index = -1
    for fcmd in fastboot_cmds.keys():
        try:
            fcmd_index = sys.argv.index(fcmd) + fastboot_cmds[fcmd]
            break
        except ValueError:
            continue
    if fcmd_index == -1:
        return remote_files

    local_files = sys.argv[fcmd_index:]

    if local_files:
        cmd = ['ssh', device['host'], 'mkdir', '-p', REMOTE_FASTBOOT_DIR]
        _execute_command(cmd)
        for f in local_files:
            remote_file = os.path.join(REMOTE_FASTBOOT_DIR, os.path.basename(f))
            cmd = ['scp', f, '%s:%s' % (device['host'], remote_file)]
            _execute_command(cmd)
            remote_files.append(remote_file)

        for f in remote_files:
            idx = remote_files.index(f)
            sys.argv[fcmd_index + idx] = f

    return remote_files


def main():
    device_config = None
    for c in CONFIGS:
        if os.path.exists(c):
            device_config = _load_device_config(c)
            break

    device_serial = _fastboot_get_device_serial()

    device = _get_device_by_serial(device_config, device_serial)

    if device:
        remote_files = _handle_fastboot_files(device)

        cmd = ['ssh', device['host'], 'fastboot']
        cmd.extend(sys.argv[1:])
        rc = _execute_command(cmd)

        for f in remote_files:
            cmd = ['ssh', device['host'], 'rm', f]
            _execute_command(cmd)
    else:
        cmd = [FASTBOOT_CMD]
        cmd.extend(sys.argv[1:])
        rc = _execute_command(cmd)

    return rc


if __name__ == '__main__':
    try:
        ret =  main()
    except Exception:
        ret = 1
        import traceback
        traceback.print_exc()
    sys.exit(ret)
