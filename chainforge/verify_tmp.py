import sys
sys.path.append('platform-backend')
from generator.builder import ChainBuilder
import zipfile, io

class MockProject:
    config = {
        'networkType': 'public', 
        'publicConsensus': 'poa', 
        'publicSyncMode': 'full', 
        'publicRuntime': 'python_vm', 
        'smartContracts': [
            {'id': 'user_contract', 'name': 'MyContract', 'type': 'python', 'code': 'class MyContract:\n    pass', 'apiKey': 'test_key'}
        ]
    }

b = ChainBuilder(MockProject())
z = b.build_package()
zip = zipfile.ZipFile(io.BytesIO(z))
routes = zip.read('api/contract_routes.py').decode('utf-8')
print(routes)
with open('test_routes.py', 'w') as f:
    f.write(routes)
