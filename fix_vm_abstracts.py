import os

vm_modules = [
    ('wasm', 'WASMRuntime'),
    ('evm', 'EVMRuntime'),
    ('python_vm', 'PythonVM')
]

for f, c in vm_modules:
    path = f'chainforge/templates/chain_core/modules/vm/{f}.py'
    with open(path, 'w') as fh:
        fh.write(f'''from interfaces.vm import VMInterface
class {c}(VMInterface):
    def execute_transaction(self, tx, state): pass
    def deploy_contract(self, code, state): pass
''')
