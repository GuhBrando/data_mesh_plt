from typing import Any

import yaml

from backend.domain.entities.data_contract import DataContract


def assemble_yaml(contract: DataContract) -> str:
    models_data = dict(contract.models)
    quality_data = models_data.pop("quality", [])
    payload: dict[str, Any] = {
        "dataContractSpecification": "0.9.3",
        "id": str(contract.id),
        "info": {
            "title": contract.title,
            "version": contract.version,
            "owner": contract.owner,
            "domain": contract.domain,
            "status": contract.status,
        },
        "models": models_data,
        "servicelevels": contract.servicelevels,
        "x-tier": contract.tier,
    }
    if quality_data:
        payload["quality"] = quality_data
    return yaml.dump(
        payload, default_flow_style=False, allow_unicode=True, sort_keys=False
    )
