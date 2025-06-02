import logging
import yaml
from typing import Dict, Any, Optional
from datacontract.model.data_contract_specification import Quality

from datacontract.export.exporter import Exporter
from datacontract.model.data_contract_specification import DataContractSpecification

# URL of the ODPS YAML Schema for v3.0
ODPS_SCHEMA = "https://opendataproducts.org/v3.0/schema/odps.yaml"
ODPS_VERSION = "3.0"

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
    sla_declarative = []

    if hasattr(spec, "servicelevels") and spec.servicelevels:
        sl = spec.servicelevels
        if sl.availability:
            sla_declarative.append(get_sla_dimension("Availability", sl.availability.percentage, "percent"))
        if sl.retention:
            sla_declarative.append(get_sla_dimension("Retention", sl.retention.period, "period"))
        if sl.latency:
            sla_declarative.append(get_sla_dimension("Latency", sl.latency.threshold, "duration"))
        if sl.freshness:
            sla_declarative.append(get_sla_dimension("Freshness", sl.freshness.threshold, "duration"))
        if sl.frequency:
            sla_declarative.append(get_sla_dimension("Frequency", sl.frequency.interval, "interval"))
        if sl.support:
            sla_declarative.append(get_sla_dimension("Support", sl.support.responseTime, "duration"))
        if sl.backup:
            sla_declarative.append(get_sla_dimension("Backup", sl.backup.recoveryTime, "duration"))

    dq_declarative = []
    for model_name, model in spec.models.items():
        if model.quality:
            for q in model.quality:
                dq_declarative.append(get_quality_dimension(model_name, "*", q))
        for field_name, field in model.fields.items():
            if field.quality:
                for q in field.quality:
                    dq_declarative.append(get_quality_dimension(model_name, field_name, q))

    return {
        "schema": ODPS_SCHEMA,
        "version": ODPS_VERSION,
        "product": {
            "contract": {
                "id": spec.id,
                "type": "ODCS",
                "contractVersion": spec.dataContractSpecification,
                "spec": spec.model_dump(exclude_none=True, by_alias=True),
            },
            "details": {
                "en": {
                    "name": spec.info.title if spec.info else None,
                    "productID": spec.id,
                    "valueProposition": getattr(spec.terms, "usage", None),
                    "description": getattr(spec.info, "description", None) if spec.info else None,
                    "visibility": "private",
                    "status": getattr(spec.info, "status", None) if spec.info else None,
                    "productVersion": getattr(spec.info, "version", None) if spec.info else None,
                    "tags": getattr(spec, "tags", []),
                    "type": getattr(spec, "dataContractSpecification", None),
                    "metadata": {
                        "team": {
                            "owner": getattr(spec.info, "owner", None)
                        }
                    }
                }
            },
            "SLA": {
                "declarative": sla_declarative
            },
            "support": {
                "email": getattr(spec.info.contact, "email", None) if spec.info and spec.info.contact else None,
                "documentationURL": None
            },
            "pricingPlans": {
                "en": [
                    {  #   price:
  # priceAmount: 9.95
  # priceCurrency: USD
  # priceUnit: megabyte
                        "name": "Default Plan",
                        "priceCurrency": (spec.terms.billing.split()[1] if spec.terms and spec.terms.billing else None),
                        "price": (spec.terms.billing.split()[0] if spec.terms and spec.terms.billing else None),
                        "billingDuration": "month",
                        "unit": (spec.terms.billing.split()[2] if spec.terms and spec.terms.billing else None),
                        "maxTransactionQuantity": "unlimited",
                        "offering": []
                    }
                ]
            },
            "dataQuality": {
                "declarative": dq_declarative
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
            "dataHolder": {
                "en": {
                    "description": getattr(spec.info, "owner", None),
                    "URL": getattr(spec.info.contact, "url", None) if spec.info and spec.info.contact else None,
                    "telephone": None,
                    "addressCountry": None
                }
            }
        }
    }
