#!/usr/bin/env python3
"""Repeatable local Semaphore provisioning. Secrets and state stay outside Git."""
import argparse
import http.cookiejar
import http.client
import json
import os
from pathlib import Path
import shlex
import sqlite3
import subprocess
import time
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
STATE = Path(os.environ.get('SEMAPHORE_STATE_DIR', str(Path.home() / '.local/state/gcp-setup-semaphore'))).expanduser().resolve()
BASE = 'http://127.0.0.1:3000/api'
CONTAINER = 'valensys-t2-semaphore-semaphore-1'
VOLUME = 'valensys-t2-semaphore_semaphore-data'


def private_json(path, value):
    # Exclusive permissions from creation, including token material.
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, 'w') as stream:
        json.dump(value, stream, indent=2)
        stream.write('\n')


def run(args, **kwargs):
    return subprocess.run(args, check=True, **kwargs)


def backup():
    info = json.loads(subprocess.check_output(['docker', 'inspect', CONTAINER]))[0]
    mounts = [m for m in info['Mounts'] if m['Destination'] == '/var/lib/semaphore']
    if len(mounts) != 1 or mounts[0].get('Name') != VOLUME:
        raise RuntimeError('Unexpected database volume; refusing to change service')
    if info['Config']['Labels'].get('com.docker.compose.project') != 'valensys-t2-semaphore':
        raise RuntimeError('Unexpected Compose project; refusing to change service')
    target = STATE / ('backup-' + time.strftime('%Y%m%dT%H%M%SZ', time.gmtime()) + '.sqlite')
    remote = '/tmp/gcp-setup-backup-' + str(time.time_ns()) + '.sqlite'
    code = "import sqlite3; s=sqlite3.connect('file:/var/lib/semaphore/database.sqlite?mode=ro',uri=True); d=sqlite3.connect(" + repr(remote) + "); s.backup(d); d.close(); s.close()"
    run(['docker', 'exec', CONTAINER, 'python3', '-c', code])
    try:
        run(['docker', 'cp', CONTAINER + ':' + remote, str(target)], stdout=subprocess.DEVNULL)
        target.chmod(0o600)
        with sqlite3.connect(target.as_uri() + '?mode=ro&immutable=1', uri=True) as db:
            if db.execute('PRAGMA quick_check').fetchone()[0] != 'ok':
                raise RuntimeError('Database backup failed integrity check')
    finally:
        run(['docker', 'exec', CONTAINER, 'rm', '-f', remote])
    print('Database backup verified:', target)


def api(opener, method, path, body=None, token=None):
    headers = {'Content-Type': 'application/json'}
    if token:
        headers['Authorization'] = 'Bearer ' + token
    req = urllib.request.Request(BASE + path, data=None if body is None else json.dumps(body).encode(), headers=headers, method=method)
    with opener.open(req, timeout=30) as response:
        data = response.read()
        return json.loads(data) if data else None


def authenticate():
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
    token_file = STATE / 'api-token.json'
    if token_file.exists():
        token = json.loads(token_file.read_text())['token']
        try:
            api(opener, 'GET', '/user', token=token)
            return opener, token
        except urllib.error.HTTPError as exc:
            if exc.code not in (401, 403):
                raise
    env_path = Path(os.environ['SEMAPHORE_ENV_FILE']).expanduser()
    secrets = {}
    for line in env_path.read_text().splitlines():
        if line.strip() and not line.lstrip().startswith('#') and '=' in line:
            key, value = line.split('=', 1)
            parts = shlex.split(value)
            secrets[key.strip()] = parts[0] if parts else ''
    api(opener, 'POST', '/auth/login', {'auth': 'admin', 'password': secrets['SEMAPHORE_ADMIN_PASSWORD']})
    name = 'gcp-setup-local-terraform'
    tokens = api(opener, 'GET', '/user/tokens')
    existing = next((t for t in tokens if t.get('name') == name and not t.get('expired')), None)
    token = (existing or api(opener, 'POST', '/user/tokens', {'name': name}))['id']
    private_json(token_file, {'token': token})
    return opener, token


def terraform(token, extra):
    env = dict(os.environ, SEMAPHOREUI_API_TOKEN=token, TF_DATA_DIR=str(STATE / 'terraform-data'))
    prefix = ['terraform', '-chdir=' + str(HERE)]
    run(prefix + ['init', '-input=false', '-lockfile=readonly', '-backend-config=path=' + str(STATE / 'terraform.tfstate')], env=env)
    plan_file = STATE / 'apply.tfplan'
    run(prefix + ['plan', '-input=false', '-no-color', '-out=' + str(plan_file)] + extra, env=env)
    if '-auto-approve' not in extra:
        answer = input('Apply the Terraform plan? [y/N] ').strip().lower()
        if answer not in ('y', 'yes'):
            raise RuntimeError('Apply cancelled')
    run(prefix + ['apply', '-input=false', str(plan_file)], env=env)
    plan_file.unlink(missing_ok=True)
    result = subprocess.run(prefix + ['plan', '-input=false', '-detailed-exitcode', '-no-color'], env=env)
    if result.returncode != 0:
        raise RuntimeError('Repeat plan has drift or failed (exit ' + str(result.returncode) + ')')
    print('Repeat plan: no changes')
    outputs = json.loads(subprocess.check_output(prefix + ['output', '-json'], env=env))
    return outputs


def verify(opener, token, outputs):
    project = outputs['project_id']['value']
    results = []
    for name, template in sorted(outputs['template_ids']['value'].items()):
        task = api(opener, 'POST', f'/project/{project}/tasks', {'template_id': int(template), 'message': 'Local code-managed validation'}, token)
        task_id = task['id']
        deadline = time.monotonic() + 180
        while time.monotonic() < deadline:
            task = api(opener, 'GET', f'/project/{project}/tasks/{task_id}', token=token)
            if task['status'] in ('success', 'error', 'stopped', 'failed'):
                break
            time.sleep(2)
        logs = api(opener, 'GET', f'/project/{project}/tasks/{task_id}/output', token=token)
        private_json(STATE / f'task-{task_id}-output.json', logs)
        result = {'name': name, 'id': task_id, 'status': task['status']}
        results.append(result)
        private_json(STATE / 'verification.json', results)
        print(json.dumps(result))
        if task['status'] != 'success':
            raise RuntimeError('Validation task did not succeed; private output saved')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['setup', 'apply', 'verify', 'backup'])
    parser.add_argument('--yes', action='store_true', help='Apply the Terraform plan without prompting')
    args, extra = parser.parse_known_args()
    if STATE == ROOT or ROOT in STATE.parents:
        raise RuntimeError('SEMAPHORE_STATE_DIR must be outside the repository')
    STATE.mkdir(parents=True, exist_ok=True, mode=0o700)
    STATE.chmod(0o700)
    if args.command in ('setup', 'backup'):
        backup()
    if args.command == 'backup':
        return
    if args.command == 'setup':
        run([str(HERE / 'start.sh')])
        for attempt in range(60):
            try:
                urllib.request.urlopen(BASE + '/ping', timeout=2).close()
                break
            except (urllib.error.URLError, TimeoutError, http.client.HTTPException, OSError):
                time.sleep(2)
        else:
            raise RuntimeError('Semaphore did not become ready')
    opener, token = authenticate()
    if args.command == 'verify':
        outputs = json.loads((STATE / 'outputs.json').read_text())
    else:
        outputs = terraform(token, (['-auto-approve'] if args.yes else []) + extra)
        private_json(STATE / 'outputs.json', outputs)
    if args.command in ('setup', 'verify'):
        verify(opener, token, outputs)


if __name__ == '__main__':
    # Private plans/state/backups and provider-generated files inherit safe modes.
    os.umask(0o077)
    main()
