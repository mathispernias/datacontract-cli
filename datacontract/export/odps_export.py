import logging
import yaml
from typing import Dict, Any, Optional
from datacontract.model.data_contract_specification import Quality

from datacontract.export.exporter import Exporter
from datacontract.model.data_contract_specification import DataContractSpecification

ODPS_SCHEMA = "https://opendataproducts.org/v3.1/schema/odps.yaml"
ODPS_VERSION = "3.1"

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
    
    





def get_sla_dimension(name: str, value: Any, unit: Optional[str] = None) -> Dict[str, Any]:
    return {
        "dimension": name,
        "displaytitle": [{"en": name.replace("_", " ").capitalize()}],
        "objective": value,
        "unit": unit
    }
    
    
def get_quality_dimension(model_name: str, field_name: str, q: Quality) -> Dict[str, Any]:
    dimension = q.type or "custom"
    return {
        "dimension": dimension,
        "displaytitle": [{"en": f"{dimension.capitalize()} ({model_name}.{field_name})"}],
        "description": [{"en": q.description}] if q.description else [],
        "objective": q.mustBe or q.mustBeGreaterThan or q.mustBeGreaterThanOrEqualTo or None,
        "unit": "number" if any([q.mustBe, q.mustBeGreaterThan, q.mustBeGreaterThanOrEqualTo]) else None,
    }

def convert_odcs_to_odps(spec: DataContractSpecification) -> Dict[str, Any]:
    print(spec)
    dq_declarative = []
    for model_name, model in spec.models.items():
        if model.quality:
            for q in model.quality:
                dq_declarative.append(get_quality_dimension(model_name, "*", q))
        for field_name, field in model.fields.items():
            if field.quality:
                for q in field.quality:
                    dq_declarative.append(get_quality_dimension(model_name, field_name, q))

    # Pricing parsing
    billing = spec.terms.billing if spec.terms and spec.terms.billing else ""
    print(f"Billing info: {billing}")
    billing_parts = billing.split() if billing else []

    # SLA parsing
    sla = []
    if spec.servicelevels:
        for attr in ["availability", "retention", "latency", "freshness", "frequency", "support", "backup"]:
            lvl = getattr(spec.servicelevels, attr)
            if lvl:
                print(f"Processing SLA attribute: {attr} with level: {lvl}")
                obj = getattr(lvl, "percentage", None) or getattr(lvl, "threshold", None)
                unit= getattr(lvl, "unit", None) or getattr(lvl, "interval", None)
                sla.append(get_sla_dimension(attr, obj, unit))
    # dataAccess mapping
    data_access = {}
    first_srv = next(iter(spec.servers.values()), None)
    if first_srv:
        data_access = {
            "authenticationMethod": first_srv.format,
            "documentationURL": first_srv.endpointUrl,
            "format": first_srv.format,
            "specification": first_srv.schema_,
            "type": first_srv.type
        }
    # placeholders/defaults
    data_holder = {}
    data_ops = {}
    recommended = getattr(spec, "recommendedDataProducts", [])
    support = {}
    if spec.servicelevels and spec.servicelevels.support:
        support = {
            "documentationURL": None,
            "email": None,
            "emailServiceHours": spec.servicelevels.support.time,
            "phoneNumber": None,
            "phoneServiceHours": spec.servicelevels.support.responseTime
        }

    return {
        "schema": ODPS_SCHEMA,
        "version": ODPS_VERSION,
        "product": {
                "en": {
                    "name": spec.info.title if spec.info.title != "" else (spec.info.dataProduct if hasattr(spec.info, "dataProduct") else None),
                    "productID": spec.id,
                    "valueProposition": getattr(spec.terms, "usage", None),
                    "description": getattr(spec.info, "description", None) if spec.info else None,
                    "visibility": "private",
                    "status": getattr(spec.info, "status", None) if spec.info else None,
                    "version": getattr(spec.info, "version", None) if spec.info else None,
                    "tags": getattr(spec, "tags", []),
                    "type": getattr(spec, "dataContractSpecification", None),
                    "metadata": {
                        "team": {
                            "owner": getattr(spec.info, "owner", None)
                        }
                    }
                },
            "dataQuality": dq_declarative,
            "pricingPlans": {
                "en": [
                    {
                        "name": "Pricing Plan",
                        "priceCurrency": billing_parts[1] if len(billing_parts) > 1 else None,
                        "price": billing_parts[0] if len(billing_parts) > 0 else None,
                        "billingDuration": "month",
                        "unit": billing_parts[2] if len(billing_parts) > 2 else None,
                        "maxTransactionQuantity": "unlimited",
                        "offering": []
                    }
                ]
            },
            "license": {
                "en": {
                    "scope": {
                        "definition": getattr(spec.terms, "usage", None),
                        "restrictions": getattr(spec.terms, "limitations", None),
                        "geographicalArea": [],
                        "permanent": None,
                        "exclusive": None,
                        "rights": []
                    },
                    "termination": {
                        "terminationConditions": None,
                        "continuityConditions": getattr(spec.terms, "noticePeriod", None)
                    },
                    "governance": {
                        "ownership": getattr(spec.info, "owner", None) if spec.info else None,
                        "damages": None,
                        "confidentiality": None,
                        "applicableLaws": None,
                        "warranties": None,
                        "audit": None,
                        "forceMajeure": None
                    }
                }
            },
            "SLA": sla,
            "dataAccess": data_access,
            "dataHolder": data_holder,
            "dataOps": data_ops,
            "recommendedDataProducts": recommended,
            "support": support
        }
    }
