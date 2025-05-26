import logging
import yaml
from typing import Dict, Any

from datacontract.export.exporter import Exporter
from datacontract.model.data_contract_specification import DataContractSpecification


class OdpsExporter(Exporter):
    """Exporter for Open Data Product Specification (ODPS) format."""
    
    def export(self, data_contract, model, server, sql_server_type, export_args) -> str:
        """
        Export the data contract as ODPS format in YAML.
        
        Returns:
            A YAML string representation of the ODPS format
        """
        odps_dict = convert_odcs_to_odps(data_contract)
        return yaml.dump(odps_dict, sort_keys=False, default_flow_style=False)
    
    
# class DataContractSpecification(pyd.BaseModel):
#     dataContractSpecification: str | None = None
#     id: str | None = None
#     info: Info | None = None
#     servers: Dict[str, Server] = {}
#     terms: Terms | None = None
#     models: Dict[str, Model] = {}
#     definitions: Dict[str, Definition] = {}
#     examples: List[Example] = pyd.Field(
#         default_factory=list,
#         deprecated="Removed in Data Contract Specification " "v1.1.0. Use models.examples instead.",
#     )
#     quality: DeprecatedQuality | None = pyd.Field(
#         default=None,
#         deprecated="Removed in Data Contract Specification v1.1.0. Use " "model-level and field-level quality instead.",
#     )
#     servicelevels: ServiceLevel | None = None
#     links: Dict[str, str] = {}
#     tags: List[str] = []

#     def to_yaml(self) -> str:
#         return yaml.dump(
#             self.model_dump(exclude_defaults=True, exclude_none=True,
#                             by_alias=True),
#             sort_keys=False,
#             allow_unicode=True,
#         )

#     @classmethod
#     def from_file(cls, file_path: str) -> "DataContractSpecification":
#         if not os.path.exists(file_path):
#             raise FileNotFoundError(f"The file '{file_path}' does not exist.")
#         with open(file_path, "r", encoding="utf-8") as file:
#             file_content = file.read()
#         return cls.from_string(file_content)

#     @classmethod
#     def from_string(cls, data_contract_str: str) -> "DataContractSpecification":
#         data = yaml.safe_load(data_contract_str)
#         return cls(**data)

#     @classmethod
#     def json_schema(cls):
#         package_name = __package__
#         json_schema = "schema.json"
#         with impresources.open_text(package_name,
#                                     json_schema) as file:
#             return file.read()


import yaml
from datacontract.model.data_contract_specification import DataContractSpecification

# URL of the ODPS YAML Schema for v3.0
ODPS_SCHEMA = "https://opendataproducts.org/v3.0/schema/odps.yaml"
ODPS_VERSION = "3.0"

def convert_odcs_to_odps(spec: DataContractSpecification) -> Dict[str, Any]:
    """
    Map a DataContractSpecification instance to an ODPS v3.1 document and return as dict.
    """
    odps: Dict[str, Any] = {
        "$schema": ODPS_SCHEMA,
        "version": ODPS_VERSION,
        "product": {},
    }

    # product details per ODPS v3.0
    info = spec.info or None
    details_en = {
        "name": getattr(info, "title", None),
        "productID": spec.id,
        "visibility": getattr(info, "status", None),
        "type": spec.dataContractSpecification,
        **({"version": info.version} if info and info.version else {}),
        **({"tags": spec.tags} if spec.tags else {}),
    }
    odps["product"]["details"] = {"en": details_en}

    # optional top-level links
    if spec.links:
        odps["product"]["links"] = spec.links

    # dataOps from first terms policy
    policies = getattr(spec.terms, "policies", None)
    if policies:
        first = policies[0]
        odps["product"]["dataOps"] = {
            "build": {"deploymentDocumentationURL": getattr(first, "url", None)}
        }

    # dataAccess from first server
    if spec.servers:
        srv = next(iter(spec.servers.values()))
        odps["product"]["dataAccess"] = {
            "type": srv.type,
            "format": srv.format,
            "specification": srv.location,
            "documentationURL": srv.description,
            "authenticationMethod": None,
        }

    # SLA array from servicelevels
    if spec.servicelevels:
        sla = []
        svc = spec.servicelevels.model_dump(exclude_none=True)
        for dim, params in svc.items():
            if params:
                objective = params.get("threshold") or params.get("percentage") or params.get("period")
                sla.append({
                    "dimension": dim,
                    "displaytitle": [{"en": dim}],
                    "monitoring": {},
                    "objective": objective,
                    "unit": params.get("unit", ""),
                })
        if sla:
            odps["product"]["SLA"] = sla

    # metadata: schemas and definitions
    metadata = {"schemas": [], "definitions": []}
    for name, m in spec.models.items():
        fld = []
        for k, f in m.fields.items():
            fld.append({
                "name": k,
                "type": f.type,
                "description": f.description,
            })
        metadata["schemas"].append({
            "name": name,
            "description": m.description,
            "fields": fld,
        })
    for name, d in spec.definitions.items():
        metadata["definitions"].append({
            "name": name,
            "title": d.title,
            "type": d.type,
            "description": d.description,
        })
    odps["product"]["metadata"] = metadata

    return odps

