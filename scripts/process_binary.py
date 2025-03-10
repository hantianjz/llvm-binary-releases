#!/usr/bin/env python3

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Set, Dict
import tarfile
import requests

class LLVMBinaryProcessor:
    def __init__(self, 
                 binary_url: str,
                 cache_dir: Path,
                 extract_dir: Path,
                 output_dir: Path,
                 binaries_file: Optional[Path] = None,
                 no_cache: bool = False):
        self.binary_url = binary_url
        self.cache_dir = cache_dir
        self.extract_dir = extract_dir
        self.output_dir = output_dir
        self.binaries_file = binaries_file
        self.binary_filter = self.load_binaries() if binaries_file else None
        self.no_cache = no_cache
        
        # Ensure directories exist
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.extract_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def load_binaries(self) -> Set[str]:
        """Load binary names from the binaries file."""
        if not self.binaries_file:
            return set()
            
        binaries = set()
        with open(self.binaries_file) as f:
            for line in f:
                # Skip comments and empty lines
                line = line.strip()
                if line and not line.startswith('#'):
                    binaries.add(line)
                    # Also add .exe version for Windows
                    binaries.add(f"{line}.exe")
        return binaries

    def get_cache_filename(self) -> Path:
        """Get the filename for caching the downloaded tarball."""
        return self.cache_dir / Path(self.binary_url).name

    def get_extract_dirname(self) -> Path:
        """Get the directory name for extracted files."""
        name = Path(self.binary_url).stem
        if name.endswith('.tar'):
            name = name[:-4]
        return self.extract_dir / name

    def extract_metadata(self) -> Dict:
        """Extract version and platform information from URL."""
        # Extract version (e.g., LLVM-19.1.2-macOS-ARM64.tar.xz)
        version_match = re.search(r'LLVM-(\d+\.\d+\.\d+)', self.binary_url)
        version = version_match.group(1) if version_match else "unknown"
        
        # Extract platform info
        url_upper = self.binary_url.upper()
        if 'ARM64' in url_upper:
            platform = 'arm64'
        elif 'X86_64' in url_upper or 'X64' in url_upper:
            platform = 'x86_64'
        else:
            platform = 'unknown'
        
        # Extract OS info
        url_lower = self.binary_url.lower()
        if 'macos' in url_lower:
            os_name = 'darwin'
        elif 'linux' in url_lower:
            os_name = 'linux'
        elif 'windows' in url_lower or 'win64' in url_lower:
            os_name = 'windows'
        else:
            os_name = 'unknown'
            
        return {
            "version": version,
            "platform": platform,
            "os": os_name,
            "release_tag": f"llvm-{version}-{platform}-{os_name}",
            "source_url": self.binary_url,
            "extraction_date": datetime.now(timezone.utc).isoformat()
        }

    def download_file(self) -> Path:
        """Download the file with caching support."""
        cache_path = self.get_cache_filename()
        
        if not self.no_cache and cache_path.exists():
            print(f"Cache hit! Using cached version from: {cache_path}")
            return cache_path
            
        print(f"{'Cache disabled, downloading' if self.no_cache else 'Cache miss. Downloading to cache'}: {cache_path}")
        
        response = requests.get(self.binary_url, stream=True)
        response.raise_for_status()
        
        with open(cache_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
                
        print("Download complete")
        return cache_path

    def extract_archive(self, tarball_path: Path) -> Path:
        """Extract the archive with caching support."""
        extract_path = self.get_extract_dirname()
        
        if not self.no_cache and extract_path.exists():
            print(f"Using cached extraction: {extract_path}")
            return extract_path
            
        print(f"Extracting archive to: {extract_path}")
        if extract_path.exists():
            shutil.rmtree(extract_path)
        extract_path.mkdir(parents=True)
        
        with tarfile.open(tarball_path) as tar:
            # Check if archive has a root directory
            members = tar.getmembers()
            if any('/' in m.name for m in members):
                # Has subdirectories, extract with strip components
                for member in members:
                    parts = Path(member.name).parts[1:]  # Skip first component
                    if parts:
                        member.name = str(Path(*parts))
                        tar.extract(member, extract_path)
            else:
                # No subdirectories, extract directly
                tar.extractall(extract_path)
                
        print("Extraction complete")
        return extract_path

    def is_binary_file(self, path: Path) -> bool:
        """Check if a file is a binary executable."""
        if not path.is_file():
            return False
            
        # For Windows executables
        if path.suffix.lower() == '.exe':
            return True
            
        # For Unix executables
        if not os.access(path, os.X_OK):
            return False
            
        # Use 'file' command to check if it's a binary
        result = subprocess.run(['file', path], capture_output=True, text=True)
        return 'text' not in result.stdout.lower()

    def matches_binary_filter(self, path: Path) -> bool:
        """Check if a binary matches our filter list."""
        if not self.binary_filter:
            return True
            
        name = path.name
        # Check both with and without .exe
        return (name in self.binary_filter or
                (name.endswith('.exe') and name[:-4] in self.binary_filter) or
                (not name.endswith('.exe') and f"{name}.exe" in self.binary_filter))

    def find_binaries(self, directory: Path) -> Set[Path]:
        """Find all binary files in the directory."""
        binaries = set()
        for item in directory.rglob('*'):
            if self.is_binary_file(item) and self.matches_binary_filter(item):
                binaries.add(item)
        return binaries

    def list_binaries(self, directory: Path):
        """List all available binaries."""
        print("Available binaries:")
        binaries = sorted(b.name for b in self.find_binaries(directory))
        for binary in binaries:
            # Strip .exe for display if present
            display_name = binary[:-4] if binary.lower().endswith('.exe') else binary
            print(f"  {display_name}")
            
        if self.binary_filter:
            print("\nFiltered binaries (from binaries.txt):")
            for binary in sorted(b for b in self.binary_filter if not b.endswith('.exe')):
                status = "✓" if binary in binaries or f"{binary}.exe" in binaries else "✗"
                print(f"  {status} {binary}")

    def process_binary(self, binary_path: Path):
        """Process a single binary file."""
        # Copy binary to output directory
        output_path = self.output_dir / binary_path.name
        shutil.copy2(binary_path, output_path)
        print(f"Copied {binary_path.name} to {output_path}")

    def process(self):
        """Main processing function."""
        try:
            # Download and extract
            tarball_path = self.download_file()
            extract_path = self.extract_archive(tarball_path)
            
            # Extract metadata
            metadata = self.extract_metadata()
            
            # List binaries if requested
            if self.list_only:
                self.list_binaries(extract_path)
                return
            
            # Process binaries
            print("Processing binaries...")
            binaries = self.find_binaries(extract_path)
            
            if not binaries:
                print("No matching binaries found!")
                if self.binary_filter:
                    print("\nRequested binaries (from binaries.txt):")
                    for binary in sorted(b for b in self.binary_filter if not b.endswith('.exe')):
                        print(f"  ✗ {binary}")
                return
                
            # Add processed binaries to metadata
            # Strip .exe from display names but keep original names in processing
            metadata["processed_binaries"] = sorted([
                b.name[:-4] if b.name.lower().endswith('.exe') else b.name 
                for b in binaries
            ])
            
            # Save metadata
            with open(self.output_dir / "metadata.json", "w") as f:
                json.dump(metadata, f, indent=2)
                
            for binary in sorted(binaries):
                self.process_binary(binary)
            
            # Final status
            print(f"\nExtraction complete! Files saved in {self.output_dir}")
            print(f"Release tag will be: {metadata['release_tag']}")
            print("\nCache locations:")
            print(f"  Downloaded tarballs: {self.cache_dir}")
            print(f"  Extracted files: {self.extract_dir}")
                
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description='Extract LLVM binaries from release packages')
    parser.add_argument('binary_url', help='URL to the LLVM binary tar file')
    parser.add_argument('-o', '--output-dir', type=Path, default=Path('./output'),
                      help='Directory to save extracted binaries (default: ./output)')
    parser.add_argument('-c', '--cache-dir', type=Path, 
                      default=Path.home() / '.cache' / 'llvm-binary-releases',
                      help='Directory to cache downloaded tarballs')
    parser.add_argument('-e', '--extract-dir', type=Path, default=Path('./extract-cache'),
                      help='Directory for extracted files cache')
    parser.add_argument('-f', '--binaries-file', type=Path, default=Path('./binaries.txt'),
                      help='File containing list of binaries to extract (default: ./binaries.txt)')
    parser.add_argument('--list-binaries', action='store_true',
                      help='List all available binaries in the tarball and exit')
    parser.add_argument('--clean-cache', action='store_true',
                      help='Clean the cache directories and exit')
    parser.add_argument('--no-cache', action='store_true',
                      help='Disable caching, always download fresh')
    
    args = parser.parse_args()
    
    # Handle cache cleaning
    if args.clean_cache:
        print("Cleaning cache directories:")
        if args.cache_dir.exists():
            print(f"Cleaning download cache: {args.cache_dir}")
            shutil.rmtree(args.cache_dir)
        if args.extract_dir.exists():
            print(f"Cleaning extract cache: {args.extract_dir}")
            shutil.rmtree(args.extract_dir)
        print("Cache cleaned successfully")
        return
    
    # Check if binaries file exists
    if not args.binaries_file.exists():
        print(f"Warning: Binaries file not found: {args.binaries_file}")
        print("Will process all binary files unless --list-binaries is specified")
    
    # Create processor instance
    processor = LLVMBinaryProcessor(
        binary_url=args.binary_url,
        cache_dir=args.cache_dir,
        extract_dir=args.extract_dir,
        output_dir=args.output_dir,
        binaries_file=args.binaries_file if args.binaries_file.exists() else None,
        no_cache=args.no_cache
    )
    
    # Set list_only flag
    processor.list_only = args.list_binaries
    
    # Process
    processor.process()

if __name__ == '__main__':
    main()