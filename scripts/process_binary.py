#!/usr/bin/env python3

import argparse
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Set
import tarfile
import requests

class LLVMBinaryProcessor:
    def __init__(self, 
                 binary_url: str,
                 cache_dir: Path,
                 extract_dir: Path,
                 output_dir: Path,
                 binary_filter: Optional[List[str]] = None,
                 dry_run: bool = True,
                 no_cache: bool = False):
        self.binary_url = binary_url
        self.cache_dir = cache_dir
        self.extract_dir = extract_dir
        self.output_dir = output_dir
        self.binary_filter = set(binary_filter) if binary_filter else None
        self.dry_run = dry_run
        self.no_cache = no_cache
        self.list_only = False
        
        # Ensure directories exist
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.extract_dir.mkdir(parents=True, exist_ok=True)
        if dry_run:
            self.output_dir.mkdir(parents=True, exist_ok=True)

    def get_cache_filename(self) -> Path:
        """Get the filename for caching the downloaded tarball."""
        return self.cache_dir / Path(self.binary_url).name

    def get_extract_dirname(self) -> Path:
        """Get the directory name for extracted files."""
        name = Path(self.binary_url).stem
        if name.endswith('.tar'):
            name = name[:-4]
        return self.extract_dir / name

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
        if not path.is_file() or not os.access(path, os.X_OK):
            return False
            
        # Use 'file' command to check if it's a binary
        result = subprocess.run(['file', path], capture_output=True, text=True)
        return 'text' not in result.stdout.lower()

    def find_binaries(self, directory: Path) -> Set[Path]:
        """Find all binary files in the directory."""
        binaries = set()
        for item in directory.rglob('*'):
            if self.is_binary_file(item):
                if not self.binary_filter or item.name in self.binary_filter:
                    binaries.add(item)
        return binaries

    def list_binaries(self, directory: Path):
        """List all available binaries."""
        print("Available binaries:")
        binaries = sorted(b.name for b in self.find_binaries(directory))
        for binary in binaries:
            print(f"  {binary}")

    def get_version(self) -> str:
        """Extract version from the URL."""
        import re
        match = re.search(r'LLVM-(\d+\.\d+\.\d+)', self.binary_url)
        return match.group(1) if match else "unknown"

    def get_platform_info(self) -> tuple:
        """Get platform and OS information."""
        platform = subprocess.check_output(['uname', '-m']).decode().strip()
        os_name = subprocess.check_output(['uname', '-s']).decode().strip().lower()
        return platform, os_name

    def process_binary(self, binary_path: Path, extract_path: Path, tarball_path: Path):
        """Process a single binary file."""
        version = self.get_version()
        platform, os_name = self.get_platform_info()
        
        release_name = f"{binary_path.name}-{version}-{platform}-{os_name}"
        print(f"Found binary: {binary_path.name}")
        print(f"Release name would be: {release_name}")
        
        if self.dry_run:
            release_dir = self.output_dir / release_name
            release_dir.mkdir(parents=True, exist_ok=True)
            
            # Copy binary
            shutil.copy2(binary_path, release_dir)
            
            # Create metadata
            metadata = {
                "name": release_name,
                "version": version,
                "platform": platform,
                "os": os_name,
                "source_url": self.binary_url,
                "binary_name": binary_path.name,
                "release_notes": f"Binary extracted from {self.binary_url}",
                "file_type": subprocess.check_output(['file', '-b', binary_path]).decode().strip(),
                "cache_info": {
                    "cached_tarball": str(tarball_path),
                    "cached_extract": str(extract_path),
                    "cache_date": datetime.now(timezone.utc).isoformat()
                }
            }
            
            with open(release_dir / 'metadata.json', 'w') as f:
                json.dump(metadata, f, indent=4)
                
            print(f"Saved binary and metadata to {release_dir}")
            
        elif 'GITHUB_TOKEN' in os.environ:
            print(f"Creating release {release_name}")
            subprocess.run([
                'gh', 'release', 'create', release_name,
                '--title', release_name,
                '--notes', f"Binary extracted from {self.binary_url}",
                str(binary_path)
            ], check=True)
        else:
            print("GITHUB_TOKEN not set - skipping release creation")
            print(f"Would create release with binary: {binary_path}")

    def process(self):
        """Main processing function."""
        try:
            # Download and extract
            tarball_path = self.download_file()
            extract_path = self.extract_archive(tarball_path)
            
            # List binaries if requested
            if self.list_only:
                self.list_binaries(extract_path)
                return
            
            # Process binaries
            print("Processing binaries...")
            binaries = self.find_binaries(extract_path)
            
            if not binaries:
                print("No matching binaries found!")
                return
                
            for binary in sorted(binaries):
                self.process_binary(binary, extract_path, tarball_path)
            
            # Final status
            if self.dry_run:
                print(f"\nDry run complete! Files saved in {self.output_dir}")
                print("Each release directory contains:")
                print("  - The extracted binary")
                print("  - metadata.json with release information")
                print("\nCache locations:")
                print(f"  Downloaded tarballs: {self.cache_dir}")
                print(f"  Extracted files: {self.extract_dir}")
            else:
                print("Processing complete!")
                
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description='Process LLVM binaries and create releases')
    parser.add_argument('binary_url', help='URL to the LLVM binary tar file')
    parser.add_argument('-d', '--dry-run', action='store_true', 
                      help="Don't create GitHub release, save files locally")
    parser.add_argument('-o', '--output-dir', type=Path, default=Path('./output'),
                      help='Directory to save files in dry run mode (default: ./output)')
    parser.add_argument('-c', '--cache-dir', type=Path, 
                      default=Path.home() / '.cache' / 'llvm-binary-releases',
                      help='Directory to cache downloaded tarballs')
    parser.add_argument('-e', '--extract-dir', type=Path, default=Path('./extract-cache'),
                      help='Directory for extracted files cache')
    parser.add_argument('-b', '--binaries', type=str,
                      help='Comma-separated list of binary names to extract')
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
    
    # Create processor instance
    processor = LLVMBinaryProcessor(
        binary_url=args.binary_url,
        cache_dir=args.cache_dir,
        extract_dir=args.extract_dir,
        output_dir=args.output_dir,
        binary_filter=args.binaries.split(',') if args.binaries else None,
        dry_run=args.dry_run,
        no_cache=args.no_cache
    )
    
    # Set list_only flag
    processor.list_only = args.list_binaries
    
    # Process
    processor.process()

if __name__ == '__main__':
    main()
