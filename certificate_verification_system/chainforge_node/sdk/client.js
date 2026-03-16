import { SPVLightClient } from './base_client.js';

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

export class ChainForgeClient extends SPVLightClient {
    constructor(spvNodeUrls = ["http://localhost:8080"], restBaseUrl = "http://localhost:8000") {
        super(spvNodeUrls);
        this.restBaseUrl = restBaseUrl;
        this.DataStore = createContractProxy("1000", "sys_key_datastore", this.restBaseUrl);
        this.Validation = createContractProxy("1001", "sys_key_validation", this.restBaseUrl);
        this.AccessControl = createContractProxy("1002", "sys_key_accesscontrol", this.restBaseUrl);
        this.IdentityRegistry = createContractProxy("1003", "sys_key_identityregistry", this.restBaseUrl);
        this.AuditLog = createContractProxy("1004", "sys_key_auditlog", this.restBaseUrl);
        this.ValidatorCouncil = createContractProxy("1005", "sys_key_validatorcouncil", this.restBaseUrl);
        this.MultiSig = createContractProxy("1006", "sys_key_multisig", this.restBaseUrl);
        this.CertificateAuthority = createContractProxy("1007", "sys_key_certificateauthority", this.restBaseUrl);
        this.AccessControl = createContractProxy("h4hscfu", "sk_9he4zo5b82ovje5nlwiui", this.restBaseUrl);
        this.CertificateRegistry = createContractProxy("7vjd6ku", "sk_9r9suqrmwe4e0ar5gvbe", this.restBaseUrl);
    }
}
