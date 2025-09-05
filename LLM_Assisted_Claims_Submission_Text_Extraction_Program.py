#!/usr/bin/env python3
"""
LLM Assisted Claims Submission Text Extraction Program
Master Script - Orchestrates the entire workflow

This script coordinates all phases of the claims submission text extraction process:
1. Copy Source File Phase
2. Extract Text Phase  
3. Import Data Phase
4. ACORD Form Population Phase

Author: LLM Claims Processing Team
Version: 1.0
"""

import os
import sys
import time
import logging
from pathlib import Path
from datetime import datetime
import traceback

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Import our custom modules
from lib.file_text_extractor import FileTextExtractor
from lib.audio_splitter import split_audio_file, process_long_audio_with_segments

# Import script modules
from scripts.copy_source_files import copy_top_level_files_only
from scripts.extract_text_batch import main as extract_text_batch_main
from scripts.import_data import main as import_data_main

# Configure logging
def setup_logging():
    """Setup comprehensive logging for the program"""
    log_dir = PROJECT_ROOT / "logs"
    log_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"llm_extraction_{timestamp}.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    return logging.getLogger(__name__)

class LLMClaimsExtractionProgram:
    """Main orchestrator class for the LLM Claims Extraction Program"""
    
    def __init__(self):
        self.logger = setup_logging()
        self.project_root = PROJECT_ROOT
        self.data_dir = self.project_root / "data"
        self.source_input_dir = self.project_root / "source_input_files"
        self.source_output_dir = self.project_root / "source_output_files"
        self.acord_output_dir = self.source_output_dir / "acord"
        self.json_output_dir = self.source_output_dir / "json"
        
        # Initialize components
        self.text_extractor = FileTextExtractor()
        
        self.logger.info("🚀 LLM Assisted Claims Submission Text Extraction Program Initialized")
        self.logger.info(f"Project Root: {self.project_root}")
        
    def ensure_directories(self):
        """Ensure all necessary directories exist"""
        directories = [
            self.source_input_dir,
            self.source_output_dir,
            self.acord_output_dir,
            self.json_output_dir,
            self.source_output_dir / "json"  # Ensure JSON subdirectory exists
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            self.logger.info(f"✅ Directory ensured: {directory}")
    
    def phase_1_copy_source_files(self):
        """Phase 1: Copy source files from data to source_input_files"""
        self.logger.info("=" * 80)
        self.logger.info("📋 PHASE 1: COPY SOURCE FILES")
        self.logger.info("=" * 80)
        
        try:
            self.logger.info("🔄 Copying files from 'data' to 'source_input_files'...")
            files_copied = copy_top_level_files_only()
            self.logger.info(f"✅ Successfully copied {files_copied} files")
            
            # List copied files
            copied_files = list(self.source_input_dir.glob("*"))
            self.logger.info("📁 Files in source_input_files:")
            for file in copied_files:
                if file.is_file():
                    self.logger.info(f"   📄 {file.name}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error in Phase 1: {str(e)}")
            self.logger.error(traceback.format_exc())
            return False
    
    def phase_2_extract_text(self):
        """Phase 2: Extract text from all source files"""
        self.logger.info("=" * 80)
        self.logger.info("📋 PHASE 2: EXTRACT TEXT FROM FILES")
        self.logger.info("=" * 80)
        
        try:
            self.logger.info("🔄 Starting text extraction process...")
            
            # Process each file in source_input_files
            source_files = list(self.source_input_dir.glob("*"))
            processed_count = 0
            
            for file_path in source_files:
                if not file_path.is_file():
                    continue
                    
                self.logger.info(f"\n🔄 Processing: {file_path.name}")
                
                try:
                    # Extract text using our enhanced extractor
                    file_name, file_type, extracted_text = self.text_extractor.process_file(str(file_path))
                    
                    if extracted_text and not extracted_text.startswith("Error"):
                        # Save extracted text to output directory
                        output_file = self.source_output_dir / f"{file_path.stem}.txt"
                        
                        with open(output_file, 'w', encoding='utf-8') as f:
                            f.write(extracted_text)
                        
                        self.logger.info(f"✅ Extracted text saved to: {output_file.name}")
                        processed_count += 1
                        
                        # Show preview
                        preview = extracted_text[:200] + "..." if len(extracted_text) > 200 else extracted_text
                        self.logger.info(f"📝 Preview: {preview}")
                    else:
                        self.logger.warning(f"⚠️  Failed to extract text from {file_path.name}: {extracted_text}")
                        
                except Exception as e:
                    self.logger.error(f"❌ Error processing {file_path.name}: {str(e)}")
                    continue
            
            self.logger.info(f"\n✅ Phase 2 Complete: Processed {processed_count} files")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error in Phase 2: {str(e)}")
            self.logger.error(traceback.format_exc())
            return False
    
    def phase_3_populate_acord_forms(self):
        """Phase 3: Populate ACORD forms with extracted text data"""
        self.logger.info("=" * 80)
        self.logger.info("📋 PHASE 3: POPULATE ACORD FORMS")
        self.logger.info("=" * 80)
        
        try:
            # Get ACORD form templates
            acord_templates = list((self.source_input_dir / "acord").glob("*.pdf"))
            extracted_texts = list(self.source_output_dir.glob("*.txt"))
            
            if not acord_templates:
                self.logger.warning("⚠️  No ACORD form templates found")
                return False
            
            if not extracted_texts:
                self.logger.warning("⚠️  No extracted text files found")
                return False
            
            self.logger.info(f"📋 Found {len(acord_templates)} ACORD form templates")
            self.logger.info(f"📝 Found {len(extracted_texts)} extracted text files")
            
            # Process each ACORD form template
            for template in acord_templates:
                self.logger.info(f"\n🔄 Processing ACORD template: {template.name}")
                
                try:
                    # Extract text from ACORD template
                    template_text = self.text_extractor.extract_text_from_pdf(str(template))
                    
                    if template_text and not template_text.startswith("Error"):
                        # Create populated form content
                        populated_content = self.create_populated_acord_form(template_text, extracted_texts)
                        
                        # Save populated form
                        output_file = self.acord_output_dir / f"populated_{template.stem}.txt"
                        with open(output_file, 'w', encoding='utf-8') as f:
                            f.write(populated_content)
                        
                        self.logger.info(f"✅ Populated ACORD form saved: {output_file.name}")
                    else:
                        self.logger.warning(f"⚠️  Failed to extract text from ACORD template: {template.name}")
                        
                except Exception as e:
                    self.logger.error(f"❌ Error processing ACORD template {template.name}: {str(e)}")
                    continue
            
            self.logger.info(f"\n✅ Phase 3 Complete: ACORD forms populated")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error in Phase 3: {str(e)}")
            self.logger.error(traceback.format_exc())
            return False
    
    def create_populated_acord_form(self, template_text, extracted_texts):
        """Create a populated ACORD form by merging template with extracted data"""
        populated_content = f"POPULATED ACORD FORM\n"
        populated_content += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        populated_content += "=" * 80 + "\n\n"
        
        # Add template content
        populated_content += "ORIGINAL TEMPLATE CONTENT:\n"
        populated_content += "-" * 40 + "\n"
        populated_content += template_text + "\n\n"
        
        # Add extracted data
        populated_content += "EXTRACTED DATA FOR POPULATION:\n"
        populated_content += "-" * 40 + "\n"
        
        for text_file in extracted_texts:
            try:
                with open(text_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                populated_content += f"\n📄 Source: {text_file.stem}\n"
                populated_content += f"📝 Content: {content[:300]}...\n" if len(content) > 300 else f"📝 Content: {content}\n"
                populated_content += "-" * 30 + "\n"
                
            except Exception as e:
                populated_content += f"\n❌ Error reading {text_file.name}: {str(e)}\n"
        
        return populated_content
    
    def phase_4_import_data_to_json(self):
        """Phase 4: Import extracted data to JSON schemas"""
        self.logger.info("=" * 80)
        self.logger.info("📋 PHASE 4: IMPORT DATA TO JSON SCHEMAS")
        self.logger.info("=" * 80)
        
        try:
            self.logger.info("🔄 Starting JSON data import process...")
            
            # Run the import data script
            import_data_main()
            
            self.logger.info("✅ Phase 4 Complete: Data imported to JSON schemas")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error in Phase 4: {str(e)}")
            self.logger.error(traceback.format_exc())
            return False
    
    def run_complete_workflow(self):
        """Run the complete workflow through all phases"""
        self.logger.info("🚀 STARTING COMPLETE LLM CLAIMS EXTRACTION WORKFLOW")
        self.logger.info(f"⏰ Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Ensure directories exist
        self.ensure_directories()
        
        # Track phase results
        phase_results = {}
        
        # Phase 1: Copy Source Files
        phase_results['phase_1'] = self.phase_1_copy_source_files()
        if not phase_results['phase_1']:
            self.logger.error("❌ Phase 1 failed. Stopping workflow.")
            return False
        
        # Phase 2: Extract Text
        phase_results['phase_2'] = self.phase_2_extract_text()
        if not phase_results['phase_2']:
            self.logger.error("❌ Phase 2 failed. Stopping workflow.")
            return False
        
        # Phase 3: Populate ACORD Forms
        phase_results['phase_3'] = self.phase_3_populate_acord_forms()
        if not phase_results['phase_3']:
            self.logger.error("❌ Phase 3 failed. Stopping workflow.")
            return False
        
        # Phase 4: Import Data to JSON
        phase_results['phase_4'] = self.phase_4_import_data_to_json()
        if not phase_results['phase_4']:
            self.logger.error("❌ Phase 4 failed. Stopping workflow.")
            return False
        
        # Workflow Summary
        self.logger.info("=" * 80)
        self.logger.info("🎉 WORKFLOW COMPLETED SUCCESSFULLY!")
        self.logger.info("=" * 80)
        self.logger.info("📊 Phase Results Summary:")
        for phase, result in phase_results.items():
            status = "✅ PASSED" if result else "❌ FAILED"
            self.logger.info(f"   {phase.replace('_', ' ').title()}: {status}")
        
        self.logger.info(f"\n⏰ End Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.logger.info("🎯 All phases completed successfully!")
        
        return True
    
    def run_individual_phase(self, phase_number):
        """Run a specific phase of the workflow"""
        phase_functions = {
            1: self.phase_1_copy_source_files,
            2: self.phase_2_extract_text,
            3: self.phase_3_populate_acord_forms,
            4: self.phase_4_import_data_to_json
        }
        
        if phase_number not in phase_functions:
            self.logger.error(f"❌ Invalid phase number: {phase_number}. Valid phases: 1-4")
            return False
        
        self.logger.info(f"🔄 Running Phase {phase_number} only...")
        return phase_functions[phase_number]()

def main():
    """Main function with user interaction"""
    print("🚀 LLM Assisted Claims Submission Text Extraction Program")
    print("=" * 80)
    print("This program automates the extraction and processing of claims data")
    print("from various file formats and populates ACORD forms and JSON schemas.")
    print()
    
    # Initialize the program
    program = LLMClaimsExtractionProgram()
    
    while True:
        print("\n📋 Available Options:")
        print("1. Run Complete Workflow (All Phases)")
        print("2. Run Phase 1: Copy Source Files")
        print("3. Run Phase 2: Extract Text")
        print("4. Run Phase 3: Populate ACORD Forms")
        print("5. Run Phase 4: Import Data to JSON")
        print("6. Exit")
        
        choice = input("\n🎯 Select an option (1-6): ").strip()
        
        if choice == "1":
            print("\n🔄 Starting complete workflow...")
            program.run_complete_workflow()
            break
        elif choice == "2":
            program.run_individual_phase(1)
            break
        elif choice == "3":
            program.run_individual_phase(2)
            break
        elif choice == "4":
            program.run_individual_phase(3)
            break
        elif choice == "5":
            program.run_individual_phase(4)
            break
        elif choice == "6":
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice. Please select 1-6.")

if __name__ == "__main__":
    main()
