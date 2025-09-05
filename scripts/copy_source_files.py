import os
import shutil
import logging
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
DEST_DIR = PROJECT_ROOT / "source_input_files"

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def ensure_directories() -> None:
    """Ensure destination directory exists"""
    try:
        DEST_DIR.mkdir(parents=True, exist_ok=True)
        logger.info(f"✅ Destination directory ensured: {DEST_DIR}")
    except Exception as e:
        logger.error(f"❌ Error creating destination directory: {e}")
        raise

def copy_top_level_files_only() -> int:
    """Copy only top-level files from data directory, excluding subdirectories"""
    ensure_directories()
    files_copied = 0
    errors = []
    
    logger.info(f"🔄 Starting file copy from {DATA_DIR} to {DEST_DIR}")
    
    try:
        for entry in DATA_DIR.iterdir():
            if entry.is_file():
                try:
                    # Copy file with metadata preservation
                    shutil.copy2(entry, DEST_DIR / entry.name)
                    files_copied += 1
                    logger.info(f"✅ Copied: {entry.name}")
                except Exception as e:
                    error_msg = f"Failed to copy {entry.name}: {e}"
                    logger.error(f"❌ {error_msg}")
                    errors.append(error_msg)
            else:
                logger.info(f"📁 Skipping directory: {entry.name}")
        
        # Summary
        logger.info(f"📊 Copy operation completed:")
        logger.info(f"   ✅ Files copied: {files_copied}")
        logger.info(f"   ❌ Errors: {len(errors)}")
        
        if errors:
            logger.warning("⚠️  Some files failed to copy. Check logs for details.")
        
        return files_copied
        
    except Exception as e:
        logger.error(f"❌ Fatal error during copy operation: {e}")
        raise

def copy_with_file_type_filter(file_types=None):
    """Copy files with specific file type filtering"""
    if file_types is None:
        file_types = ['.pdf', '.txt', '.wav', '.mp3', '.mp4', '.avi', '.mov']
    
    ensure_directories()
    files_copied = 0
    filtered_out = 0
    
    logger.info(f"🔄 Copying files with type filter: {file_types}")
    
    try:
        for entry in DATA_DIR.iterdir():
            if entry.is_file():
                if entry.suffix.lower() in file_types:
                    try:
                        shutil.copy2(entry, DEST_DIR / entry.name)
                        files_copied += 1
                        logger.info(f"✅ Copied: {entry.name}")
                    except Exception as e:
                        logger.error(f"❌ Failed to copy {entry.name}: {e}")
                else:
                    filtered_out += 1
                    logger.info(f"🔍 Filtered out: {entry.name} (type: {entry.suffix})")
            else:
                logger.info(f"📁 Skipping directory: {entry.name}")
        
        logger.info(f"📊 Filtered copy completed:")
        logger.info(f"   ✅ Files copied: {files_copied}")
        logger.info(f"   🔍 Files filtered out: {filtered_out}")
        
        return files_copied
        
    except Exception as e:
        logger.error(f"❌ Error during filtered copy: {e}")
        raise

def cleanup_destination_directory():
    """Clean up destination directory before copying"""
    try:
        if DEST_DIR.exists():
            # Remove all files but keep the directory structure
            for item in DEST_DIR.iterdir():
                if item.is_file():
                    item.unlink()
                    logger.info(f"🗑️  Removed existing file: {item.name}")
                elif item.is_dir():
                    shutil.rmtree(item)
                    logger.info(f"🗑️  Removed existing directory: {item.name}")
            
            logger.info("✅ Destination directory cleaned")
        else:
            logger.info("📁 Destination directory doesn't exist, will be created")
    except Exception as e:
        logger.error(f"❌ Error cleaning destination directory: {e}")
        raise

def main():
    """Main function with enhanced functionality"""
    print("🔄 Enhanced File Copy Utility")
    print("=" * 50)
    
    try:
        # Ask user if they want to clean destination first
        clean_choice = input("🧹 Clean destination directory before copying? (y/n): ").lower().strip()
        if clean_choice in ['y', 'yes']:
            cleanup_destination_directory()
        
        # Ask user if they want to filter by file type
        filter_choice = input("🔍 Use file type filtering? (y/n): ").lower().strip()
        
        if filter_choice in ['y', 'yes']:
            print("\n📋 Available file types:")
            print("1. All supported types (default)")
            print("2. Documents only (.pdf, .txt)")
            print("3. Audio only (.wav, .mp3)")
            print("4. Video only (.mp4, .avi, .mov)")
            print("5. Custom types")
            
            filter_option = input("\n🎯 Select filter option (1-5): ").strip()
            
            if filter_option == "1":
                count = copy_top_level_files_only()
            elif filter_option == "2":
                count = copy_with_file_type_filter(['.pdf', '.txt'])
            elif filter_option == "3":
                count = copy_with_file_type_filter(['.wav', '.mp3'])
            elif filter_option == "4":
                count = copy_with_file_type_filter(['.mp4', '.avi', '.mov'])
            elif filter_option == "5":
                custom_types = input("Enter file extensions separated by commas (e.g., .pdf,.txt): ").strip()
                custom_types = [f".{ext.strip().lstrip('.')}" for ext in custom_types.split(',')]
                count = copy_with_file_type_filter(custom_types)
            else:
                print("❌ Invalid option, using default copy")
                count = copy_top_level_files_only()
        else:
            count = copy_top_level_files_only()
        
        print(f"\n✅ Successfully copied {count} file(s) to {DEST_DIR}")
        
        # List copied files
        if count > 0:
            print("\n📁 Copied files:")
            for file_path in DEST_DIR.iterdir():
                if file_path.is_file():
                    file_size = file_path.stat().st_size
                    size_str = f"{file_size / 1024:.1f} KB" if file_size < 1024*1024 else f"{file_size / (1024*1024):.1f} MB"
                    print(f"   📄 {file_path.name} ({size_str})")
        
    except Exception as e:
        logger.error(f"❌ Copy operation failed: {e}")
        print(f"❌ Error: {e}")
        return False
    
    return True

if __name__ == "__main__":
    main()
