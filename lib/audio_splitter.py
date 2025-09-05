#!/usr/bin/env python3
"""
Audio file splitter utility for long audio files
"""

import os
from pydub import AudioSegment
import tempfile

def split_audio_file(input_file, output_dir, segment_length=300000):
    """
    Split audio file into smaller segments
    
    Args:
        input_file: Path to input audio file
        output_dir: Directory to save segments
        segment_length: Length of each segment in milliseconds (default: 5 minutes)
    """
    print(f"Splitting: {input_file}")
    print(f"Output directory: {output_dir}")
    print(f"Segment length: {segment_length/1000:.1f} seconds")
    print("=" * 60)
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    try:
        # Load audio file
        audio = AudioSegment.from_file(input_file)
        duration = len(audio)
        
        print(f"Total duration: {duration/1000:.1f} seconds")
        print(f"Number of segments: {duration // segment_length + 1}")
        
        segments = []
        for i in range(0, duration, segment_length):
            # Extract segment
            segment = audio[i:i + segment_length]
            
            # Create filename
            base_name = os.path.splitext(os.path.basename(input_file))[0]
            segment_name = f"{base_name}_segment_{i//segment_length + 1:03d}.wav"
            segment_path = os.path.join(output_dir, segment_name)
            
            # Export segment
            segment.export(
                segment_path,
                format='wav',
                parameters=[
                    '-ar', '16000',      # 16kHz sample rate
                    '-ac', '1',          # Mono channel
                    '-f', 'wav',         # WAV format
                    '-acodec', 'pcm_s16le'  # PCM 16-bit
                ]
            )
            
            segments.append(segment_path)
            print(f"Created: {segment_name} ({len(segment)/1000:.1f}s)")
        
        print(f"\n✅ Successfully created {len(segments)} segments")
        return segments
        
    except Exception as e:
        print(f"❌ Error splitting audio: {e}")
        return []

def process_long_audio_with_segments(input_file, output_dir="./audio_segments"):
    """
    Split long audio file and process each segment
    """
    print("Audio File Splitter and Processor")
    print("=" * 60)
    
    # Split the audio file
    segments = split_audio_file(input_file, output_dir)
    
    if not segments:
        print("❌ Failed to split audio file")
        return
    
    print(f"\n📁 Segments saved to: {output_dir}")
    print("\n💡 Next steps:")
    print("1. Process each segment individually with your text extractor")
    print("2. Combine the results from all segments")
    print("3. Each segment is now under 5 minutes and suitable for speech recognition")
    
    return segments

if __name__ == "__main__":
    # Example usage
    input_audio = './data/ACORD1_ACORD101_CPP-456789123_04072025.wav'
    process_long_audio_with_segments(input_audio)
