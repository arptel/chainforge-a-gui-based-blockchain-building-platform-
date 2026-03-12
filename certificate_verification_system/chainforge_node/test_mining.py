import subprocess
import time
import requests
import sys

print('Cleaning ports...')
try:
    pids = subprocess.check_output('powershell -c "(Get-NetTCPConnection -LocalPort 8080 -ErrorAction SilentlyContinue).OwningProcess"', shell=True).decode().split()
    for pid in pids:
        if pid.strip():
            subprocess.run(['taskkill', '/F', '/PID', pid.strip()])
except Exception:
    pass

print('Launching Node A...')
pNode = subprocess.Popen(['python', '-u', 'main.py', '--api-port', '8080', '--port', '5000', '--db-path', '../data/node_a.sqlite'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
time.sleep(3)

print('Calling backend issue API...')
try:
    t = requests.post('http://127.0.0.1:8001/auth/login', json={'username':'college_a','password':'password123'}).json()['access_token']
    r = requests.post('http://127.0.0.1:8001/api/issue', headers={'Authorization': 'Bearer ' + t}, json={'student_name':'Bob','degree':'BSc','year':2025}, timeout=20)
    print('API Result:', r.status_code, r.text)
except Exception as e:
    print('Error calling API:', e)

print('Killing Node A...')
pNode.terminate()

print('--- Node A Logs ---')
print(pNode.stdout.read())
print('--- End Logs ---')
