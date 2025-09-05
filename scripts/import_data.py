import json
import re
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
TXT_DIR = PROJECT_ROOT / "source_output_files"  # Fixed path
JSON_DIR = PROJECT_ROOT / "source_output_files" / "json"  # Store JSON files in source_output_files/json
JSON_SCHEMAS_DIR = PROJECT_ROOT / "source_input_files" / "json"  # JSON schema templates
ACORD_TEMPLATES_DIR = PROJECT_ROOT / "source_input_files" / "acord"

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def ensure_directories() -> None:
    """Ensure all necessary directories exist"""
    try:
        JSON_DIR.mkdir(parents=True, exist_ok=True)
        logger.info(f"✅ JSON output directory ensured: {JSON_DIR}")
    except Exception as e:
        logger.error(f"❌ Error creating JSON directory: {e}")
        raise

def load_acord_templates() -> Dict[str, Dict[str, Any]]:
    """Load ACORD form templates for field mapping"""
    templates = {}
    
    try:
        if ACORD_TEMPLATES_DIR.exists():
            for template_file in ACORD_TEMPLATES_DIR.glob("*.pdf"):
                template_name = template_file.stem
                templates[template_name] = {
                    'file_path': template_file,
                    'fields': get_acord_form_fields(template_name)
                }
                logger.info(f"📋 Loaded ACORD template: {template_name}")
        
        if not templates:
            logger.warning("⚠️  No ACORD templates found")
            
    except Exception as e:
        logger.error(f"❌ Error loading ACORD templates: {e}")
    
    return templates

def load_json_schemas() -> Dict[str, Dict[str, Any]]:
    """Load JSON schema templates from source_input_files/json"""
    schemas = {}
    
    try:
        if JSON_SCHEMAS_DIR.exists():
            for schema_file in JSON_SCHEMAS_DIR.glob("*.json"):
                schema_name = schema_file.stem
                try:
                    with open(schema_file, 'r', encoding='utf-8') as f:
                        schema_data = json.load(f)
                    schemas[schema_name] = schema_data
                    logger.info(f"📋 Loaded JSON schema: {schema_name}")
                except Exception as e:
                    logger.warning(f"⚠️  Failed to load schema {schema_name}: {e}")
                    continue
        else:
            logger.warning("⚠️  No JSON schema templates found")
            
    except Exception as e:
        logger.error(f"❌ Error loading JSON schemas: {e}")
    
    return schemas

def get_acord_form_fields(template_name: str) -> Dict[str, str]:
    """Get field definitions for specific ACORD form types"""
    # Define field mappings for different ACORD forms
    field_mappings = {
        'acord_1_propertyloss-notice': {
            'insured_name': r'insured|policyholder|name',
            'policy_number': r'policy\s*#|policy\s*number|policy\s*no',
            'date_of_loss': r'date\s*of\s*loss|loss\s*date',
            'property_address': r'property\s*address|location|address',
            'description_of_loss': r'description|details|what\s*happened',
            'estimated_loss': r'estimated\s*loss|damage\s*estimate|amount',
            'contact_phone': r'phone|telephone|contact',
            'email': r'email|e-mail'
        },
        'ACORD_101_(2008-01)Additional_Remarks_Schedule': {
            'additional_remarks': r'remarks|comments|additional|notes',
            'schedule_items': r'schedule|items|list|inventory',
            'values': r'value|cost|price|amount',
            'descriptions': r'description|details|specifications'
        },
        'ACORD-3 Liability-Notice-of-Occurence-': {
            'insured_name': r'insured|policyholder|name',
            'policy_number': r'policy\s*#|policy\s*number',
            'date_of_occurrence': r'date\s*of\s*occurrence|incident\s*date',
            'description': r'description|what\s*happened|incident\s*details',
            'location': r'location|where|address',
            'witnesses': r'witness|witnesses|eyewitness',
            'injuries': r'injury|injuries|damage|harm'
        }
    }
    
    return field_mappings.get(template_name, {})

def enhanced_field_parse(text: str, acord_fields: Dict[str, str] = None) -> Dict[str, Any]:
    """Enhanced field parsing with ACORD form field mapping"""
    fields = {}
    
    try:
        # Basic key-value extraction
        basic_fields = {}
        for line in text.splitlines():
            # Look for patterns like "Key: Value" or "Key - Value"
            patterns = [
                r'^\s*([^:]{1,100})\s*:\s*(.+)$',
                r'^\s*([^-]{1,100})\s*-\s*(.+)$',
                r'^\s*([^=]{1,100})\s*=\s*(.+)$'
            ]
            
            for pattern in patterns:
                match = re.match(pattern, line)
                if match:
                    key = match.group(1).strip()
                    val = match.group(2).strip()
                    if key and val:
                        basic_fields[key] = val
                        break
        
        # ACORD-specific field extraction
        if acord_fields:
            for field_name, pattern in acord_fields.items():
                matches = re.findall(pattern, text, re.IGNORECASE)
                if matches:
                    if len(matches) == 1:
                        fields[field_name] = matches[0].strip()
                    else:
                        fields[field_name] = [m.strip() for m in matches]
        
        # Merge basic fields with ACORD fields
        fields.update(basic_fields)
        
        # Extract common insurance-related information
        common_patterns = {
            'claim_number': r'claim\s*#?\s*(\w+)',
            'policy_type': r'(auto|home|business|liability|property)\s*insurance',
            'date_patterns': r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            'phone_patterns': r'(\(\d{3}\)\s*\d{3}-\d{4}|\d{3}-\d{3}-\d{4})',
            'email_patterns': r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
            'amount_patterns': r'\$?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
            'address_patterns': r'(\d+\s+[A-Za-z\s]+(?:Street|St|Avenue|Ave|Road|Rd|Lane|Ln|Drive|Dr|Boulevard|Blvd|Court|Ct|Place|Pl|Way|Circle|Cir))'
        }
        
        for field_name, pattern in common_patterns.items():
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                if field_name == 'date_patterns':
                    fields['dates_found'] = matches
                elif field_name == 'phone_patterns':
                    fields['phone_numbers'] = matches
                elif field_name == 'email_patterns':
                    fields['emails'] = matches
                elif field_name == 'amount_patterns':
                    fields['amounts'] = [float(m.replace(',', '')) for m in matches]
                elif field_name == 'address_patterns':
                    fields['addresses'] = matches
                else:
                    fields[field_name] = matches[0] if len(matches) == 1 else matches
        
        # If no structured fields found, create a summary
        if not fields:
            fields = {
                'raw_text': text[:1000] + "..." if len(text) > 1000 else text,
                'text_length': len(text),
                'word_count': len(text.split()),
                'extraction_method': 'fallback_summary'
            }
        
        # Add metadata
        fields['extraction_timestamp'] = datetime.now().isoformat()
        fields['extraction_method'] = 'enhanced_parsing'
        
    except Exception as e:
        logger.error(f"❌ Error in enhanced field parsing: {e}")
        fields = {
            'error': str(e),
            'raw_text': text[:500] + "..." if len(text) > 500 else text,
            'extraction_timestamp': datetime.now().isoformat()
        }
    
    return fields

def create_structured_json_from_schema(extracted_fields: Dict[str, Any], schema_template: Dict[str, Any], source_file: str) -> Dict[str, Any]:
    """Create structured JSON using the provided schema template"""
    try:
        # Start with the schema template
        structured_json = schema_template.copy()
        
        # Update with extracted data
        if 'fields' in structured_json:
            # Map extracted fields to schema structure
            for field_name, field_value in extracted_fields.items():
                if field_name in structured_json['fields']:
                    structured_json['fields'][field_name] = field_value
                else:
                    # Add new fields that weren't in the template
                    structured_json['fields'][field_name] = field_value
        
        # Update metadata
        if 'metadata' not in structured_json:
            structured_json['metadata'] = {}
        
        structured_json['metadata'].update({
            'extraction_date': datetime.now().isoformat(),
            'source_file': source_file,
            'confidence_score': calculate_confidence_score(extracted_fields),
            'processing_notes': f"Processed using {schema_template.get('schema_name', 'unknown')} template"
        })
        
        return structured_json
        
    except Exception as e:
        logger.error(f"❌ Error creating structured JSON: {e}")
        # Fallback to basic structure
        return {
            'schema_name': schema_template.get('schema_name', 'unknown'),
            'source_file': source_file,
            'extraction_date': datetime.now().isoformat(),
            'fields': extracted_fields,
            'error': f"Failed to apply schema template: {str(e)}"
        }

def create_acord_json_schema(extracted_fields: Dict[str, Any], template_name: str) -> Dict[str, Any]:
    """Create structured JSON schema for ACORD forms"""
    schema = {
        'form_type': template_name,
        'form_version': '1.0',
        'extraction_date': datetime.now().isoformat(),
        'status': 'extracted',
        'fields': extracted_fields,
        'metadata': {
            'source_files': [],
            'processing_notes': [],
            'confidence_score': calculate_confidence_score(extracted_fields)
        }
    }
    
    return schema

def calculate_confidence_score(fields: Dict[str, Any]) -> float:
    """Calculate confidence score based on field quality"""
    score = 0.0
    total_fields = 0
    
    for key, value in fields.items():
        if key in ['extraction_timestamp', 'extraction_method', 'error']:
            continue
            
        total_fields += 1
        
        if isinstance(value, str) and len(value.strip()) > 0:
            if len(value.strip()) > 10:  # Longer text usually means better extraction
                score += 1.0
            else:
                score += 0.5
        elif isinstance(value, (list, tuple)) and len(value) > 0:
            score += 0.8
        elif isinstance(value, (int, float)):
            score += 1.0
    
    if total_fields == 0:
        return 0.0
    
    return min(1.0, score / total_fields)

def main() -> None:
    """Main function with enhanced data processing"""
    logger.info("🚀 Enhanced Data Import and ACORD Form Processing")
    logger.info("=" * 60)
    
    try:
        ensure_directories()
        
        # Load ACORD templates
        acord_templates = load_acord_templates()
        logger.info(f"📋 Loaded {len(acord_templates)} ACORD templates")
        
        # Load JSON schema templates
        json_schemas = load_json_schemas()
        logger.info(f"📋 Loaded {len(json_schemas)} JSON schema templates")
        
        # Process text files
        text_files = list(TXT_DIR.glob("*.txt")) if TXT_DIR.exists() else []
        
        if not text_files:
            logger.warning("⚠️  No text files found in source_output_files")
            print("❌ No text files found. Please run text extraction first.")
            return
        
        logger.info(f"📝 Found {len(text_files)} text files to process")
        
        processed_count = 0
        acord_forms_created = 0
        
        for text_file in text_files:
            try:
                logger.info(f"\n🔄 Processing: {text_file.name}")
                
                # Read extracted text
                with open(text_file, 'r', encoding='utf-8', errors='ignore') as f:
                    text = f.read()
                
                # Extract fields using enhanced parsing
                extracted_fields = enhanced_field_parse(text)
                
                # Create basic JSON output
                basic_json = {
                    'source_file': text_file.name,
                    'extraction_date': datetime.now().isoformat(),
                    'fields': extracted_fields
                }
                
                # Save basic JSON
                json_path = JSON_DIR / f"{text_file.stem}.json"
                with open(json_path, 'w', encoding='utf-8') as jf:
                    json.dump(basic_json, jf, indent=2, ensure_ascii=False)
                
                logger.info(f"✅ Basic JSON created: {json_path.name}")
                processed_count += 1
                
                # Create JSON files using schema templates if available
                for schema_name, schema_template in json_schemas.items():
                    try:
                        # Create structured JSON using schema template
                        structured_json = create_structured_json_from_schema(
                            extracted_fields, schema_template, text_file.name
                        )
                        
                        # Save structured JSON
                        structured_json_path = JSON_DIR / f"{text_file.stem}_{schema_name}.json"
                        with open(structured_json_path, 'w', encoding='utf-8') as jf:
                            json.dump(structured_json, jf, indent=2, ensure_ascii=False)
                        
                        logger.info(f"✅ Structured JSON created: {structured_json_path.name}")
                        
                    except Exception as e:
                        logger.warning(f"⚠️  Failed to create structured JSON for {schema_name}: {e}")
                        continue
                
                # Create ACORD-specific forms if templates are available
                for template_name, template_info in acord_templates.items():
                    try:
                        # Create ACORD-specific schema
                        acord_schema = create_acord_json_schema(extracted_fields, template_name)
                        
                        # Save ACORD-specific JSON
                        acord_json_path = JSON_DIR / f"{text_file.stem}_{template_name}.json"
                        with open(acord_json_path, 'w', encoding='utf-8') as jf:
                            json.dump(acord_schema, jf, indent=2, ensure_ascii=False)
                        
                        logger.info(f"✅ ACORD form created: {acord_json_path.name}")
                        acord_forms_created += 1
                        
                    except Exception as e:
                        logger.warning(f"⚠️  Failed to create ACORD form for {template_name}: {e}")
                        continue
                
            except Exception as e:
                logger.error(f"❌ Error processing {text_file.name}: {e}")
                continue
        
        # Generate summary
        logger.info("=" * 60)
        logger.info("📊 IMPORT SUMMARY REPORT")
        logger.info("=" * 60)
        logger.info(f"📁 Text files processed: {processed_count}")
        logger.info(f"📋 ACORD forms created: {acord_forms_created}")
        logger.info(f"📋 JSON schema templates used: {len(json_schemas)}")
        logger.info(f"📁 Output directory: {JSON_DIR}")
        
        # Console summary
        print(f"\n🎉 Data import completed!")
        print(f"📊 Results: {processed_count} files processed, {acord_forms_created} ACORD forms created")
        print(f"📁 JSON output directory: {JSON_DIR}")
        
        if acord_forms_created > 0:
            print(f"📋 ACORD forms available for: {', '.join(acord_templates.keys())}")
        
        if json_schemas:
            print(f"📋 JSON schemas applied: {', '.join(json_schemas.keys())}")
        
    except Exception as e:
        logger.error(f"❌ Fatal error in data import: {e}")
        print(f"❌ Fatal error: {e}")
        return False
    
    return True

def process_single_file(file_path: str):
    """Process a single text file for testing or individual use"""
    try:
        ensure_directories()
        
        text_file = Path(file_path)
        if not text_file.exists():
            logger.error(f"❌ File not found: {file_path}")
            return False
        
        logger.info(f"🔄 Processing single file: {text_file.name}")
        
        # Read and process text
        with open(text_file, 'r', encoding='utf-8', errors='ignore') as f:
            text = f.read()
        
        # Extract fields
        extracted_fields = enhanced_field_parse(text)
        
        # Create JSON output
        json_path = JSON_DIR / f"{text_file.stem}.json"
        with open(json_path, 'w', encoding='utf-8') as jf:
            json.dump({
                'source_file': text_file.name,
                'extraction_date': datetime.now().isoformat(),
                'fields': extracted_fields
            }, jf, indent=2, ensure_ascii=False)
        
        logger.info(f"✅ Successfully processed: {text_file.name} -> {json_path.name}")
        print(f"✅ Success: {text_file.name} -> {json_path.name}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error processing single file: {e}")
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    main()
