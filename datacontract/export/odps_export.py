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
        odps_dict = to_odps(data_contract)
        return yaml.dump(odps_dict, sort_keys=False, default_flow_style=False)


def to_odps(data_contract_spec: DataContractSpecification) -> Dict[str, Any]:
    """
    Convert a Data Contract Specification to Open Data Product Specification format.
    
    Args:
        data_contract_spec: The data contract specification object
        
    Returns:
        Dictionary representing the ODPS format
    """
    # Create ODPS structure according to schema
    odps = {
        "version": "3.1",  # ODPS schema version
        "schema": "source/schema/odps.yaml",
        "product": {
            "en": {
                "name": data_contract_spec.info.title or "",
                "description": data_contract_spec.info.description or "",
                "version": data_contract_spec.info.version or "1.0.0",
                "tags": data_contract_spec.info.tags if hasattr(data_contract_spec.info, 'tags') else [],
                "categories": [],
                "status": "active",
                "visibility": "public"
            },
            "dataHolder": {}
        },
        "details": {
            "summary": data_contract_spec.info.summary if hasattr(data_contract_spec.info, 'summary') else "",
            "description": data_contract_spec.info.description or "",
            "language": "en"
        }
    }
    
    # Add contact information
    if data_contract_spec.info.contact:
        odps["product"]["support"] = {
            "email": data_contract_spec.info.contact.email or "",
            "documentationURL": data_contract_spec.info.contact.url or ""
        }
        
        odps["product"]["dataHolder"] = {
            "description": data_contract_spec.info.contact.name or ""
        }
    
    # Add data access
    odps["product"]["dataAccess"] = {
        "type": "API",
        "format": "JSON"
    }
    
    # Add schema information
    if data_contract_spec.models:
        # Add schema structure as URI reference pointing to models section
        field_schemas = []
        
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
            
            field_schemas.append({
                "name": model_name,
                "description": model.description or "",
                "fields": fields
            })
        
        # Store schema definitions in details metadata
        odps["details"]["metadata"] = {
            "schemas": field_schemas
        }
    
    # Add quality information if available
    if data_contract_spec.quality:
        quality_items = []
        
        # Try to convert existing quality info to ODPS format
        if data_contract_spec.quality.specification:
            quality_items.append({
                "dimension": "Accuracy",
                "displaytitle": [{"en": "Data Quality"}],
                "monitoring": {
                    "type": data_contract_spec.quality.type or "custom",
                    "spec": data_contract_spec.quality.specification or ""
                }
            })
        
        if quality_items:
            odps["product"]["dataQuality"] = quality_items
    
    # Return the dictionary directly, not a string
    return odps