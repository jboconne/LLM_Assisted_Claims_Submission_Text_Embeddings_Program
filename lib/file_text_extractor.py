import os
import mimetypes
import speech_recognition as sr
from pydub import AudioSegment
import PyPDF2
import pdfplumber  # Alternative to PyMuPDF - more Windows-friendly
import cv2
import pytesseract
from PIL import Image
import tempfile
import wave
import json
import shutil

class FileTextExtractor:
    def __init__(self):
        self.supported_extensions = {
            '.wav': 'audio',
            '.mp3': 'audio', 
            '.mpeg': 'audio',
            '.mp4': 'video',
            '.avi': 'video',
            '.mov': 'video',
            '.mkv': 'video',
            '.txt': 'text',
            '.pdf': 'pdf'
        }
        
        # Create necessary directories
        self.ensure_directories()
        
    def ensure_directories(self):
        """Create necessary directories for processing"""
        dirs = ['extracted_audio', 'video_audio_segments', 'video_audio_results']
        for dir_name in dirs:
            if not os.path.exists(dir_name):
                os.makedirs(dir_name)
        
    def detect_file_type(self, file_path):
        """Detect file type based on extension and MIME type"""
        file_ext = os.path.splitext(file_path)[1].lower()
        
        if file_ext in self.supported_extensions:
            return self.supported_extensions[file_ext]
        
        # Fallback to MIME type detection
        mime_type, _ = mimetypes.guess_type(file_path)
        if mime_type:
            if mime_type.startswith('audio/'):
                return 'audio'
            elif mime_type.startswith('video/'):
                return 'video'
            elif mime_type == 'text/plain':
                return 'text'
            elif mime_type == 'application/pdf':
                return 'pdf'
        
        return 'unknown'
    
    def extract_text_from_audio(self, file_path):
        """Extract text from audio files using speech recognition with enhanced handling"""
        temp_files = []
        try:
            # Load audio file
            audio = AudioSegment.from_file(file_path)
            
            # Check if audio is too long (Google API has limits)
            duration_seconds = len(audio) / 1000
            if duration_seconds > 300:  # 5 minutes limit
                print(f"⚠️  Audio is {duration_seconds:.1f} seconds long (exceeds 5-minute limit)")
                print("🔄 Attempting to split and process in segments...")
                return self.process_long_audio(file_path, audio)
            
            # Create a temporary WAV file with optimized parameters for speech recognition
            temp_wav = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
            temp_files.append(temp_wav.name)
            
            # Export with speech recognition optimized parameters
            audio.export(
                temp_wav.name, 
                format='wav',
                parameters=[
                    '-ar', '16000',      # Sample rate: 16kHz (optimal for speech)
                    '-ac', '1',          # Mono channel (better for speech recognition)
                    '-f', 'wav',         # Force WAV format
                    '-acodec', 'pcm_s16le'  # PCM 16-bit little-endian
                ]
            )
            
            # Close the file to ensure it's written completely
            temp_wav.close()
            
            # Initialize recognizer with optimized settings
            recognizer = sr.Recognizer()
            recognizer.energy_threshold = 300
            recognizer.dynamic_energy_threshold = True
            recognizer.pause_threshold = 0.8
            
            with sr.AudioFile(temp_wav.name) as source:
                # Read audio data
                audio_data = recognizer.record(source)
                
                # Perform speech recognition with comprehensive error handling
                try:
                    text = recognizer.recognize_google(audio_data)
                    return text
                except sr.RequestError as e:
                    if "Bad Request" in str(e):
                        return "Speech recognition failed: Audio format may not be suitable for speech recognition. The file might be music, noise, or in an unsupported format."
                    else:
                        return f"Speech recognition service error: {str(e)}"
                except sr.UnknownValueError:
                    return "Speech recognition could not understand the audio. The file might be silent, contain only music/noise, or have unclear speech."
                
        except Exception as e:
            # Try alternative approach with different audio parameters
            try:
                # Clean up first temp file
                for temp_file in temp_files:
                    if os.path.exists(temp_file):
                        try:
                            os.unlink(temp_file)
                        except:
                            pass
                temp_files.clear()
                
                # Try with more basic export parameters
                audio = AudioSegment.from_file(file_path)
                temp_wav2 = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
                temp_files.append(temp_wav2.name)
                
                # Export with basic parameters
                audio.export(temp_wav2.name, format='wav')
                temp_wav2.close()
                
                recognizer = sr.Recognizer()
                with sr.AudioFile(temp_wav2.name) as source:
                    audio_data = recognizer.record(source)
                    try:
                        text = recognizer.recognize_google(audio_data)
                        return text
                    except sr.RequestError as e:
                        if "Bad Request" in str(e):
                            return "Speech recognition failed: Audio format may not be suitable for speech recognition. The file might be music, noise, or in an unsupported format."
                        else:
                            return f"Speech recognition service error: {str(e)}"
                    except sr.UnknownValueError:
                        return "Speech recognition could not understand the audio. The file might be silent, contain only music/noise, or have unclear speech."
                    
            except Exception as e2:
                return f"Error extracting audio text: {str(e)} (Alternative method also failed: {str(e2)})"
                
        finally:
            # Clean up temporary files
            for temp_file in temp_files:
                if os.path.exists(temp_file):
                    try:
                        os.unlink(temp_file)
                    except:
                        pass
    
    def process_long_audio(self, file_path, audio):
        """Process long audio files by splitting into segments"""
        try:
            print("🔄 Splitting audio into segments...")
            
            # Split audio into 5-minute segments
            segment_length = 300000  # 5 minutes in milliseconds
            segments = []
            
            for i in range(0, len(audio), segment_length):
                segment = audio[i:i + segment_length]
                segments.append(segment)
            
            print(f"✅ Created {len(segments)} segments")
            
            # Process each segment
            results = []
            for i, segment in enumerate(segments, 1):
                print(f"📝 Processing segment {i}/{len(segments)}...")
                
                # Create temporary file for segment
                temp_segment = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
                segment.export(temp_segment.name, format='wav')
                temp_segment.close()
                
                # Process segment
                segment_text = self.extract_text_from_audio(temp_segment.name)
                
                # Clean up temp file
                try:
                    os.unlink(temp_segment.name)
                except:
                    pass
                
                if not segment_text.startswith("Error") and not segment_text.startswith("Speech recognition"):
                    results.append(f"Segment {i}: {segment_text}")
                else:
                    results.append(f"Segment {i}: [No speech detected]")
            
            if results:
                return "\n\n".join(results)
            else:
                return "No speech detected in any audio segments"
                
        except Exception as e:
            return f"Error processing long audio: {str(e)}"
    
    def extract_text_from_text_file(self, file_path):
        """Extract text from plain text files"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()
        except UnicodeDecodeError:
            try:
                with open(file_path, 'r', encoding='latin-1') as file:
                    return file.read()
            except Exception as e:
                return f"Error reading text file: {str(e)}"
        except Exception as e:
            return f"Error reading text file: {str(e)}"
    
    def extract_text_from_pdf(self, file_path):
        """Extract text from PDF files using pdfplumber"""
        try:
            with pdfplumber.open(file_path) as doc:
                text = ""
                
                for page in doc.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
                
                return text.strip()
            
        except Exception as e:
            return f"Error extracting PDF text: {str(e)}"
    
    def extract_text_from_video(self, file_path):
        """Extract text from video files with enhanced audio extraction option"""
        try:
            # Check if file exists
            if not os.path.exists(file_path):
                return "Error: Video file not found"
            
            # Get file info
            file_size = os.path.getsize(file_path)
            file_ext = os.path.splitext(file_path)[1].lower()
            
            print(f"🎬 Processing video: {os.path.basename(file_path)}")
            print(f"📊 File size: {file_size / (1024*1024):.1f} MB")
            print(f"🎥 Format: {file_ext}")
            
            # First, try to extract audio from video (more reliable for spoken content)
            print("🔊 Attempting audio extraction from video...")
            audio_result = self.extract_audio_from_video(file_path)
            
            if audio_result and not audio_result.startswith("Error"):
                print("✅ Audio extraction successful, processing with speech recognition...")
                return audio_result
            
            # If audio extraction fails, fall back to OCR method
            print("🔄 Audio extraction failed, falling back to OCR method...")
            return self.extract_text_from_video_frames(file_path)
                
        except Exception as e:
            return f"Error extracting video text: {str(e)}"
    
    def extract_audio_from_video(self, file_path):
        """Extract audio from video files and process with speech recognition"""
        try:
            # Extract audio using pydub
            video = AudioSegment.from_file(file_path)
            
            # Get audio properties
            duration_seconds = len(video) / 1000
            channels = video.channels
            sample_rate = video.frame_rate
            
            print(f"🔊 Audio duration: {duration_seconds:.1f} seconds")
            print(f"🔊 Audio channels: {channels}")
            print(f"🔊 Sample rate: {sample_rate} Hz")
            
            # Check if audio is too long
            if duration_seconds > 300:  # 5 minutes limit
                print("⚠️  Audio is too long, splitting into segments...")
                return self.process_long_audio(file_path, video)
            
            # Create temporary WAV file
            temp_wav = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
            temp_wav.close()
            
            # Export audio with optimized parameters
            video.export(temp_wav.name, format='wav')
            
            # Process with speech recognition
            result = self.extract_text_from_audio(temp_wav.name)
            
            # Clean up
            try:
                os.unlink(temp_wav.name)
            except:
                pass
            
            return result
            
        except Exception as e:
            return f"Error extracting audio from video: {str(e)}"
    
    def extract_text_from_video_frames(self, file_path):
        """Extract text from video files using OCR on frames (fallback method)"""
        try:
            # Try to open video file with OpenCV
            cap = cv2.VideoCapture(file_path)
            
            if not cap.isOpened():
                return f"Error: Could not open video file '{os.path.basename(file_path)}'. This may be due to missing video codecs. Try installing additional codecs or converting the video to a different format."
            
            # Get video properties
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            duration = total_frames / fps if fps > 0 else 0
            
            print(f"🎬 Video properties: {total_frames} frames, {fps:.1f} fps, {duration:.1f} seconds")
            
            if total_frames == 0:
                cap.release()
                return "Error: Video file appears to be empty or corrupted"
            
            text_frames = []
            frame_count = 0
            sample_rate = max(1, total_frames // 100)  # Process ~100 frames total
            
            print(f"🔄 Processing every {sample_rate}th frame...")
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Process every nth frame
                if frame_count % sample_rate == 0:
                    try:
                        # Convert frame to PIL Image
                        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                        pil_image = Image.fromarray(frame_rgb)
                        
                        # Extract text using OCR
                        frame_text = pytesseract.image_to_string(pil_image)
                        if frame_text.strip():
                            # Clean up the text
                            cleaned_text = ' '.join(frame_text.strip().split())
                            if len(cleaned_text) > 10:  # Only keep meaningful text
                                text_frames.append(f"Frame {frame_count}: {cleaned_text}")
                    except Exception as e:
                        print(f"⚠️  Warning: Error processing frame {frame_count}: {e}")
                        continue
                
                frame_count += 1
                
                # Progress indicator
                if frame_count % (total_frames // 10) == 0:
                    progress = (frame_count / total_frames) * 100
                    print(f"📊 Progress: {progress:.1f}% ({frame_count}/{total_frames} frames)")
            
            cap.release()
            
            if text_frames:
                result = f"Video text extraction completed successfully.\n"
                result += f"Processed {frame_count} frames, found text in {len(text_frames)} frames.\n\n"
                result += "Extracted text:\n" + "\n".join(text_frames)
                return result
            else:
                return "No text found in video frames. The video might not contain readable text, or the text might be too small/blurry for OCR."
                
        except Exception as e:
            return f"Error extracting video text from frames: {str(e)}"
    
    def process_file(self, file_path):
        """Process a single file and extract text"""
        if not os.path.exists(file_path):
            return None, None, "File not found"
        
        file_name = os.path.basename(file_path)
        file_type = self.detect_file_type(file_path)
        
        if file_type == 'unknown':
            return file_name, file_type, "Unsupported file type"
        
        print(f"\n🔄 Processing: {file_name} ({file_type.upper()})")
        
        # Extract text based on file type
        if file_type == 'audio':
            extracted_text = self.extract_text_from_audio(file_path)
        elif file_type == 'text':
            extracted_text = self.extract_text_from_text_file(file_path)
        elif file_type == 'pdf':
            extracted_text = self.extract_text_from_pdf(file_path)
        elif file_type == 'video':
            extracted_text = self.extract_text_from_video(file_path)
        else:
            extracted_text = "Unsupported file type"
        
        return file_name, file_type, extracted_text
    
    def process_folder(self, folder_path):
        """Process all supported files in a folder"""
        if not os.path.exists(folder_path):
            print(f"❌ Error: Folder '{folder_path}' does not exist")
            return
        
        results = []
        supported_files = []
        
        # First, identify supported files
        for filename in os.listdir(folder_path):
            file_path = os.path.join(folder_path, filename)
            if os.path.isfile(file_path):
                file_type = self.detect_file_type(file_path)
                if file_type != 'unknown':
                    supported_files.append((filename, file_path, file_type))
        
        if not supported_files:
            print("❌ No supported files found in the folder.")
            return results
        
        print(f"📁 Found {len(supported_files)} supported files to process")
        print("=" * 60)
        
        # Process each supported file
        for i, (filename, file_path, file_type) in enumerate(supported_files, 1):
            print(f"\n📄 File {i}/{len(supported_files)}: {filename}")
            print(f"🎯 Type: {file_type.upper()}")
            print("-" * 40)
            
            file_name, file_type, extracted_text = self.process_file(file_path)
            
            if file_name:
                results.append({
                    'filename': file_name,
                    'type': file_type,
                    'text': extracted_text
                })
                
                # Show preview of extracted text
                if extracted_text and not extracted_text.startswith("Error"):
                    preview = extracted_text[:200] + "..." if len(extracted_text) > 200 else extracted_text
                    print(f"✅ Extracted: {preview}")
                else:
                    print(f"❌ {extracted_text}")
            
            print("=" * 60)
        
        return results
    
    def display_results(self, results):
        """Display extraction results in a formatted way"""
        if not results:
            print("❌ No supported files found in the folder.")
            return
        
        print("\n" + "=" * 80)
        print("🎉 FILE TEXT EXTRACTION RESULTS")
        print("=" * 80)
        print()
        
        for i, result in enumerate(results, 1):
            print(f"📄 File {i}: {result['filename']}")
            print(f"🎯 Type: {result['type'].upper()}")
            print("-" * 40)
            
            # Truncate long text for display
            text = result['text']
            if len(text) > 500:
                text = text[:500] + "...\n[Text truncated for display]"
            
            print(f"📝 Extracted Text:\n{text}")
            print("=" * 80)
            print()

def main():
    """Main function to run the text extractor"""
    print("🚀 File Text Extractor - Enhanced Version")
    print("📁 Extracts text from audio, text, PDF, and video files")
    print("🎬 Now with enhanced video processing and long audio support!")
    print()
    
    # Get folder path from user
    #folder_path = input("Enter the folder path containing your files: ").strip()
    folder_path = "./data".strip()
    
    if not folder_path:
        print("❌ No folder path provided. Exiting.")
        return
    
    # Create extractor instance
    extractor = FileTextExtractor()
    
    print(f"\n📂 Processing files in: {folder_path}")
    print("⏱️  This may take a while depending on file sizes and types...")
    print()
    
    try:
        # Process the folder
        results = extractor.process_folder(folder_path)
        
        if results:
            # Display results
            extractor.display_results(results)
            
            # Option to save results to file
            save_option = input("\n💾 Would you like to save results to a file? (y/n): ").lower().strip()
            if save_option in ['y', 'yes']:
                output_file = "extraction_results.txt"
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write("FILE TEXT EXTRACTION RESULTS\n")
                    f.write("=" * 50 + "\n\n")
                    
                    for result in results:
                        f.write(f"File: {result['filename']}\n")
                        f.write(f"Type: {result['type']}\n")
                        f.write("-" * 30 + "\n")
                        f.write(f"Extracted Text:\n{result['text']}\n")
                        f.write("=" * 50 + "\n\n")
                
                print(f"✅ Results saved to: {output_file}")
        else:
            print("❌ No supported files found in the specified folder.")
            
    except Exception as e:
        print(f"❌ An error occurred: {str(e)}")

if __name__ == "__main__":
    main()
