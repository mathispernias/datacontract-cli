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
    # Create base ODPS structure according to schema v3.0+
    odps = {
        "version": "3.0",
        "schema": "https://opendataproducts.org/dev/schema/odps.yaml",
        "product": {
            # Embed the original data contract specification
            "contract": {
                "id": data_contract_spec.id if hasattr(data_contract_spec, 'id') else "",
                "type": "DCS",
                "contractVersion": "1.1.0",  # Data contract spec version
                "spec": data_contract_spec.to_dict() if hasattr(data_contract_spec, 'to_dict') else {}
            },
            # Details section with product metadata
            "details": {
                "en": {
                    "name": data_contract_spec.info.title or "",
                    "description": data_contract_spec.info.description or "",
                    "productVersion": data_contract_spec.info.version or "1.0.0",
                    "status": data_contract_spec.info.status if hasattr(data_contract_spec.info, 'status') else "active",
                    "visibility": "public",
                    "tags": data_contract_spec.tags if hasattr(data_contract_spec, 'tags') else [],
                    "categories": []
                }
            },
            # Data holder section (e.g., organization info)
            "dataHolder": {
                "description": data_contract_spec.info.owner if hasattr(data_contract_spec.info, 'owner') else ""
            }
        }
    }
    
    # Add contact information
    if hasattr(data_contract_spec.info, 'contact') and data_contract_spec.info.contact:
        odps["product"]["support"] = {
            "email": data_contract_spec.info.contact.email if hasattr(data_contract_spec.info.contact, 'email') else "",
            "documentationURL": data_contract_spec.info.contact.url if hasattr(data_contract_spec.info.contact, 'url') else ""
        }
    
    # Add data access info based on servers if available
    if hasattr(data_contract_spec, 'servers') and data_contract_spec.servers:
        # Use the first server as the data access point
        first_server = next(iter(data_contract_spec.servers.values()))
        odps["product"]["dataAccess"] = {
            "type": first_server.type if hasattr(first_server, 'type') else "API",
            "format": first_server.format if hasattr(first_server, 'format') else "JSON"
        }
    else:
        # Default data access info
        odps["product"]["dataAccess"] = {
            "type": "API",
            "format": "JSON"
        }
    
    # Add schema information (models)
    if hasattr(data_contract_spec, 'models') and data_contract_spec.models:
        schemas = []
        
        for model_name, model in data_contract_spec.models.items():
            fields = []
            for field_name, field in model.fields.items():
                field_info = {
                    "name": field_name,
                    "description": field.description if hasattr(field, 'description') else "",
                    "type": field.type if hasattr(field, 'type') else "string",
                }
                
                # Add format if available
                if hasattr(field, 'format') and field.format:
                    field_info["format"] = field.format
                
                fields.append(field_info)
            
            schemas.append({
                "name": model_name,
                "description": model.description if hasattr(model, 'description') else "",
                "fields": fields
            })
        
        # Store schemas in metadata
        if "metadata" not in odps["product"]["details"]["en"]:
            odps["product"]["details"]["en"]["metadata"] = {}
        
        odps["product"]["details"]["en"]["metadata"]["schemas"] = schemas
    
    # Add quality information if available
    if hasattr(data_contract_spec, 'quality') and data_contract_spec.quality:
        quality_items = []
        
        # Convert existing quality info to ODPS format
        if hasattr(data_contract_spec.quality, 'specification') and data_contract_spec.quality.specification:
            quality_items.append({
                "dimension": "Accuracy",
                "displaytitle": [{"en": "Data Quality"}],
                "monitoring": {
                    "type": data_contract_spec.quality.type if hasattr(data_contract_spec.quality, 'type') else "custom",
                    "spec": data_contract_spec.quality.specification
                }
            })
        
        if quality_items:
            odps["product"]["dataQuality"] = quality_items
        
    # Add SLAs if service levels are defined
    if hasattr(data_contract_spec, 'servicelevels') and data_contract_spec.servicelevels:
        sla_items = []
        
        # Check if servicelevels is a dictionary or direct object
        if hasattr(data_contract_spec.servicelevels, 'items'):
            # It's a dictionary-like object with items() method
            service_levels_dict = data_contract_spec.servicelevels
        else:
            # It's a single ServiceLevel object
            service_levels_dict = {'servicelevel': data_contract_spec.servicelevels}
        
        # Process each service level
        for sla_key, sla in service_levels_dict.items():
            sla_item = {
                "dimension": sla_key.capitalize(),
                "displaytitle": [{"en": f"{sla_key.capitalize()} SLA"}],
                "monitoring": {
                    "type": "custom",
                    "spec": sla.description if hasattr(sla, 'description') else ""
                }
            }
            
            # Add SLA metrics if available
            if hasattr(sla, 'percentage'):
                sla_item["objective"] = sla.percentage
                sla_item["unit"] = "percentage"
            elif hasattr(sla, 'threshold'):
                sla_item["objective"] = sla.threshold
                sla_item["unit"] = "hours"
            
            sla_items.append(sla_item)
        
        if sla_items:
            odps["product"]["SLA"] = sla_items
        
        # Return the dictionary
    return odps