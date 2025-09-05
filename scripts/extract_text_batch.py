import os
import sys
import traceback
import logging
from pathlib import Path
from datetime import datetime
import time

# Ensure project root is on sys.path for 'lib' imports
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Reuse existing extractor logic where possible
from lib.file_text_extractor import FileTextExtractor

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

SRC_DIR = PROJECT_ROOT / "source_input_files"
OUT_DIR = PROJECT_ROOT / "source_output_files"

def ensure_directories() -> None:
    """Ensure output directory exists"""
    try:
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        logger.info(f"✅ Output directory ensured: {OUT_DIR}")
    except Exception as e:
        logger.error(f"❌ Error creating output directory: {e}")
        raise

def write_text(output_path: Path, text: str) -> None:
    """Write extracted text to output file with error handling"""
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(text if text else "")
        logger.info(f"✅ Text written to: {output_path.name}")
    except Exception as e:
        logger.error(f"❌ Error writing to {output_path.name}: {e}")
        raise

def get_supported_files():
    """Get list of supported files for processing"""
    supported_extensions = {'.pdf', '.txt', '.wav', '.mp3', '.mp4', '.avi', '.mov', '.mpeg', '.mkv'}
    supported_files = []
    
    for entry in SRC_DIR.iterdir():
        if entry.is_file() and entry.suffix.lower() in supported_extensions:
            supported_files.append(entry)
    
    return supported_files

def process_file_with_retry(extractor, file_path, max_retries=2):
    """Process a file with retry logic for robustness"""
    for attempt in range(max_retries + 1):
        try:
            file_name, file_type, extracted_text = extractor.process_file(str(file_path))
            return file_name, file_type, extracted_text
        except Exception as e:
            if attempt == max_retries:
                logger.error(f"❌ Failed to process {file_path.name} after {max_retries + 1} attempts: {e}")
                return file_path.name, "unknown", f"Error: {str(e)}"
            else:
                logger.warning(f"⚠️  Attempt {attempt + 1} failed for {file_path.name}, retrying...")
                time.sleep(1)  # Brief pause before retry
    
    return file_path.name, "unknown", "Error: Max retries exceeded"

def main() -> None:
    """Main function with enhanced processing and reporting"""
    logger.info("🚀 Enhanced Text Extraction Batch Processor")
    logger.info("=" * 60)
    
    try:
        ensure_directories()
        extractor = FileTextExtractor()
        
        # Get supported files
        supported_files = get_supported_files()
        
        if not supported_files:
            logger.warning("⚠️  No supported files found in source directory")
            print("❌ No supported files found. Please ensure files are copied to source_input_files first.")
            return
        
        logger.info(f"📁 Found {len(supported_files)} supported files to process")
        print(f"🔄 Processing {len(supported_files)} files...")
        
        # Process files with progress tracking
        processed_count = 0
        success_count = 0
        error_count = 0
        results = []
        
        for i, file_path in enumerate(supported_files, 1):
            logger.info(f"\n🔄 Processing file {i}/{len(supported_files)}: {file_path.name}")
            print(f"📄 [{i}/{len(supported_files)}] Processing: {file_path.name}")
            
            start_time = time.time()
            
            try:
                # Process file with retry logic
                file_name, file_type, extracted_text = process_file_with_retry(extractor, file_path)
                
                # Determine output filename
                out_name = f"{file_path.stem}.txt"
                out_path = OUT_DIR / out_name
                
                # Write extracted text
                write_text(out_path, extracted_text or "")
                
                # Track results
                processing_time = time.time() - start_time
                result = {
                    'filename': file_name,
                    'type': file_type,
                    'success': not extracted_text.startswith("Error"),
                    'processing_time': processing_time,
                    'output_file': out_name
                }
                results.append(result)
                
                if result['success']:
                    success_count += 1
                    logger.info(f"✅ {file_name} -> {out_name} ({file_type}) - {processing_time:.2f}s")
                    print(f"   ✅ Success ({processing_time:.2f}s)")
                else:
                    error_count += 1
                    logger.warning(f"⚠️  {file_name} failed: {extracted_text}")
                    print(f"   ❌ Failed: {extracted_text[:100]}...")
                
                processed_count += 1
                
            except Exception as e:
                error_count += 1
                logger.error(f"❌ Failed to process {file_path.name}: {e}")
                print(f"   ❌ Error: {str(e)}")
                traceback.print_exc()
                
                # Add error result
                results.append({
                    'filename': file_path.name,
                    'type': 'unknown',
                    'success': False,
                    'processing_time': time.time() - start_time,
                    'output_file': None,
                    'error': str(e)
                })
        
        # Generate summary report
        logger.info("=" * 60)
        logger.info("📊 EXTRACTION SUMMARY REPORT")
        logger.info("=" * 60)
        logger.info(f"📁 Total files processed: {processed_count}")
        logger.info(f"✅ Successful extractions: {success_count}")
        logger.info(f"❌ Failed extractions: {error_count}")
        logger.info(f"📈 Success rate: {(success_count/processed_count*100):.1f}%" if processed_count > 0 else "N/A")
        
        # Save detailed results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = OUT_DIR / f"extraction_results_{timestamp}.txt"
        
        with open(results_file, 'w', encoding='utf-8') as f:
            f.write("TEXT EXTRACTION RESULTS REPORT\n")
            f.write("=" * 50 + "\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total files: {processed_count}\n")
            f.write(f"Successful: {success_count}\n")
            f.write(f"Failed: {error_count}\n\n")
            
            for result in results:
                f.write(f"File: {result['filename']}\n")
                f.write(f"Type: {result['type']}\n")
                f.write(f"Success: {'Yes' if result['success'] else 'No'}\n")
                f.write(f"Processing Time: {result['processing_time']:.2f}s\n")
                if result['output_file']:
                    f.write(f"Output: {result['output_file']}\n")
                if 'error' in result:
                    f.write(f"Error: {result['error']}\n")
                f.write("-" * 30 + "\n")
        
        logger.info(f"📄 Detailed results saved to: {results_file.name}")
        
        # Console summary
        print(f"\n🎉 Extraction completed!")
        print(f"📊 Results: {success_count} successful, {error_count} failed")
        print(f"📁 Output directory: {OUT_DIR}")
        print(f"📄 Results report: {results_file.name}")
        
        if error_count > 0:
            print(f"⚠️  {error_count} files failed. Check logs for details.")
        
    except Exception as e:
        logger.error(f"❌ Fatal error in batch processing: {e}")
        print(f"❌ Fatal error: {e}")
        traceback.print_exc()
        return False
    
    return True

def process_single_file(file_path):
    """Process a single file for testing or individual use"""
    try:
        ensure_directories()
        extractor = FileTextExtractor()
        
        logger.info(f"🔄 Processing single file: {file_path}")
        
        file_name, file_type, extracted_text = extractor.process_file(str(file_path))
        
        if extracted_text and not extracted_text.startswith("Error"):
            out_name = f"{Path(file_path).stem}.txt"
            out_path = OUT_DIR / out_name
            write_text(out_path, extracted_text)
            
            logger.info(f"✅ Successfully processed: {file_name} -> {out_name}")
            print(f"✅ Success: {file_name} -> {out_name}")
            return True
        else:
            logger.error(f"❌ Failed to extract text: {extracted_text}")
            print(f"❌ Failed: {extracted_text}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error processing single file: {e}")
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    main()
