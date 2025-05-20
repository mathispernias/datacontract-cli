
import logging
from typing import Dict, Any

from datacontract.export.exporter import Exporter
from datacontract.model.data_contract_specification import DataContractSpecification


class OdpsExporter(Exporter):
    """Exporter for Open Data Product Specification (ODPS) format."""
    
    def export(self, data_contract, model, server, sql_server_type, export_args) -> dict:
        return to_odps(data_contract)


def to_odps(data_contract_spec: DataContractSpecification) -> Dict[str, Any]:
    """
    Convert a Data Contract Specification to Open Data Product Specification format.
    
    Args:
        data_contract_spec: The data contract specification object
        
    Returns:
        Dictionary representing the ODPS format
    """
    # Start with basic metadata
    odps = {
        "name": data_contract_spec.info.title or "",
        "description": data_contract_spec.info.description or "",
        "version": data_contract_spec.info.version or "1.0.0",
        "dataProductOwner": data_contract_spec.info.contact.name if data_contract_spec.info.contact else "",
        "dataProductOwnerEmail": data_contract_spec.info.contact.email if data_contract_spec.info.contact else "",
    }
    
    # Add schema information
    if data_contract_spec.models:
        odps["schema"] = []
        for model_name, model in data_contract_spec.models.items():
            fields = []
            for field_name, field in model.fields.items():
                field_info = {
                    "name": field_name,
                    "description": field.description or "",
                    "type": field.type,
                }
                
                # Add physical type if available in config
                if field.config and "physical_type" in field.config:
                    field_info["physicalType"] = field.config.get("physical_type")
                
                # Add format if available
                if field.format:
                    field_info["format"] = field.format
                
                fields.append(field_info)
            
            odps["schema"].append({
                "name": model_name,
                "description": model.description or "",
                "fields": fields
            })
    
    # Add quality information if available
    if data_contract_spec.quality:
        odps["dataQuality"] = {
            "type": data_contract_spec.quality.type,
            "specification": data_contract_spec.quality.specification
        }
    
    return odps