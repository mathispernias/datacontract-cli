# Conversion ODCS → ODPS v3.0 : Guide de mapping

Ce document explique pas à pas comment transformer un `DataContractSpecification` (ODCS v3.x) en un document conforme à l’Open Data Product Specification v3.0 (ODPS).

---

## 1. Contexte

- **ODCS** : Open Data Contract Standard (v3.x). Structure riche pour décrire : info, serveurs, termes, SLA, schémas…
- **ODPS v3.0** : Open Data Product Specification. Standard centré sur les métadonnées produit, la qualité de service et l’accès.

Objectif : partir d’un objet `DataContractSpecification` et produire un dictionnaire (ou YAML) suivant le schéma ODPS v3.0.

---

## 2. Structure minimale ODPS v3.0

```yaml
$schema: https://opendataproducts.org/v3.0/schema/odps.yaml
version: "3.0"
product:
  details:
    en:
      name: <string>
      productID: <string>
      type: <string>
      visibility: <string>
      version: <string>     # facultatif
      tags: [<string>]     # facultatif
  links: { <clé>: <url> }  # facultatif
  dataOps: { … }          # ex. build.deploymentDocumentationURL
  dataAccess: { … }       # type, format, specification, documentationURL, authenticationMethod
  SLA:
    - dimension: <string>
      displaytitle:
        - en: <string>
      monitoring: { }
      objective: <number|string>
      unit: <string>
  metadata:
    schemas:   # description des modèles
      - name: <string>
        description: <string>
        fields:
          - name: <string>
            type: <string>
            description: <string>
    definitions:  # définitions réutilisables
      - name: <string>
        title: <string>
        type: <string>
        description: <string>
```  

---

## 3. Mapping détaillé

1. **Header**
   ```yaml
   $schema: "https://opendataproducts.org/v3.0/schema/odps.yaml"
   version: "3.0"
   ```

2. **`product.details.en`**
   | ODCS                                   | ODPS                          |
   |----------------------------------------|-------------------------------|
   | `spec.info.title`                     | `details.en.name`             |
   | `spec.id`                             | `details.en.productID`        |
   | `spec.dataContractSpecification`      | `details.en.type`             |
   | `spec.info.status`                    | `details.en.visibility`       |
   | `spec.info.version` (optionnel)       | `details.en.version`          |
   | `spec.tags` (optionnel)               | `details.en.tags`             |

3. **`product.links`** (optionnel)
   Copie directe de `spec.links: Dict[str,str]`.

4. **`product.dataOps`** (optionnel)
   Si `spec.terms.policies` existe :
   ```yaml
   dataOps:
     build:
       deploymentDocumentationURL: <première_policy.url>
   ```

5. **`product.dataAccess`** (optionnel)
   Sur le **premier** `Server` de `spec.servers.values()` :
   ```yaml
   dataAccess:
     type:              # server.type
     format:            # server.format
     specification:     # server.location
     documentationURL:  # server.description
     authenticationMethod: null
   ```

6. **`product.SLA`** (optionnel)
   Pour chaque dimension de `spec.servicelevels.*` (availability, retention, latency…) :
   ```yaml
   - dimension: <nom_dimension>
     displaytitle:
       - en: <nom_dimension>
     monitoring: { }
     objective: <threshold|percentage|period>
     unit: <unit>
   ```

7. **`product.metadata`**
   - **schemas** : pour chaque entrée `spec.models[name]` :
     ```yaml
     - name: <name>
       description: <model.description>
       fields:
         - name: <champ>
           type: <f.type>
           description: <f.description>
     ```

   - **definitions** : pour chaque `spec.definitions[name]` :
     ```yaml
     - name: <name>
       title: <d.title>
       type: <d.type>
       description: <d.description>
     ```

---

## 4. Extensions possibles

Selon vos besoins, vous pouvez compléter :
- **`recommendedDataProducts`**, **`pricingPlans`**
- **`support`**, **`dataQuality`**
- **`license`**, **`dataHolder`**, etc.

Il suffit d’ajouter les blocs correspondants en se basant sur le schéma ODPS (voir `odps.yaml`).

---

## 5. Exemple minimal généré

```yaml
$schema: https://opendataproducts.org/v3.0/schema/odps.yaml
version: "3.0"
product:
  details:
    en:
      name: my quantum
      productID: 53581432-6c55-4ba2-a65f-72344a91553a
      type: DataContract
      visibility: active
      version: 1.1.0
      tags:
        - transactions
  dataAccess:
    type: postgres
    format: null
    specification: null
    documentationURL: null
    authenticationMethod: null
  SLA:
    - dimension: generalAvailability
      displaytitle:
        - en: generalAvailability
      monitoring: {}
      objective: "2022-05-12T09:30:10-08:00"
      unit: ""
    - dimension: retention
      displaytitle:
        - en: retention
      monitoring: {}
      objective: 3
      unit: y
  metadata:
    schemas:
      - name: tbl
        description: Provides core payment metrics
        fields:
          - name: transaction_reference_date
            type: date
            description: Reference date for transaction
    definitions: []
```

---

*Ce fichier documente la transformation ODCS → ODPS v3.0.*
