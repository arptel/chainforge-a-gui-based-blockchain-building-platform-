class SmartContract {
    constructor(contractId, apiKey, baseUrl) {
        this.contractId = contractId;
        this.apiKey = apiKey;
        this.baseUrl = `${baseUrl}/api/v1/contracts/execute/${contractId}`;
    }

    async _call(method, args = {}) {
        const response = await fetch(`${this.baseUrl}/${method}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'x-api-key': this.apiKey
            },
            body: JSON.stringify({ args: args })
        });
        
        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`Error ${response.status}: ${errorText}`);
        }
        
        const data = await response.json();
        return data.result;
    }
}

function createContractProxy(contractId, apiKey, baseUrl) {
    const contract = new SmartContract(contractId, apiKey, baseUrl);
    return new Proxy(contract, {
        get(target, prop) {
            if (prop in target) {
                return target[prop];
            }
            return async (args = {}) => {
                return await target._call(prop, args);
            };
        }
    });
}

export class ChainForgeClient {
    constructor(baseUrl = "http://localhost:8000") {
        this.baseUrl = baseUrl;
        this.Token = createContractProxy("c1", "test-key", this.baseUrl);
        this.DataStore = createContractProxy("sys_datastore", "sk_sys_datastore", this.baseUrl);
        this.Governance = createContractProxy("sys_governance", "sk_sys_governance", this.baseUrl);
    }
}
