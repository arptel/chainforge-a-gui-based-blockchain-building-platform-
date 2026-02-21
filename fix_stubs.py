import os

sync_modules = [
    ('fast', 'FastSync'),
    ('light', 'LightSync'),
    ('snapshot', 'SnapshotSync'),
    ('realtime', 'RealtimeSync'),
    ('batch', 'BatchSync')
]

for f, c in sync_modules:
    path = f'chainforge/templates/chain_core/modules/sync/{f}.py'
    with open(path, 'w') as fh:
        fh.write(f'from interfaces.sync import SyncInterface\nclass {c}(SyncInterface):\n    def __init__(self, chain, network): pass\n    def sync_chain(self): pass\n    def handle_new_block(self, block): pass\n')

vm_modules = [
    ('wasm', 'WASMRuntime'),
    ('evm', 'EVMRuntime'),
    ('python_vm', 'PythonVM')
]

for f, c in vm_modules:
    path = f'chainforge/templates/chain_core/modules/vm/{f}.py'
    with open(path, 'w') as fh:
        fh.write(f'from interfaces.vm import VMInterface\nclass {c}(VMInterface):\n    def execute_transaction(self, tx, state): pass\n')
