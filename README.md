# LLVM Binary Releases

This repository hosts individual LLVM binaries extracted from the official LLVM releases. It provides a way to access specific LLVM binaries without downloading the complete LLVM distribution.

## Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/llvm-binary-releases.git
   cd llvm-binary-releases
   ```

2. Run the setup script:
   ```bash
   ./setup.sh
   ```
   This will:
   - Create a virtual environment using uv
   - Install required dependencies

3. Activate the virtual environment:
   ```bash
   source .venv/bin/activate
   ```

## Usage

### Command Line Options

```bash
Usage: ./scripts/process_binary.py [options] <binary_url>
Options:
  -d, --dry-run      Don't create GitHub release, save files locally
  -o, --output-dir   Directory to save files in dry run mode (default: ./output)
  -c, --cache-dir    Directory to cache downloaded tarballs (default: ~/.cache/llvm-binary-releases)
  -e, --extract-dir  Directory for extracted files cache (default: ./extract-cache)
  -b, --binaries     Comma-separated list of binary names to extract (e.g., 'llvm-ar,llvm-nm')
  --list-binaries    List all available binaries in the tarball and exit
  --clean-cache      Clean the cache directories and exit
  --no-cache         Disable caching, always download fresh
  -h, --help         Show this help message
```

### Examples

1. List available binaries in a tarball:
   ```bash
   ./scripts/process_binary.py --list-binaries \
     "https://github.com/llvm/llvm-project/releases/download/llvmorg-19.1.2/LLVM-19.1.2-macOS-ARM64.tar.xz"
   ```

2. Extract specific binaries (dry run):
   ```bash
   ./scripts/process_binary.py --dry-run \
     -b 'llvm-ar,llvm-nm' \
     "https://github.com/llvm/llvm-project/releases/download/llvmorg-19.1.2/LLVM-19.1.2-macOS-ARM64.tar.xz"
   ```

3. Clean the cache:
   ```bash
   ./scripts/process_binary.py --clean-cache
   ```

4. Create actual GitHub releases:
   ```bash
   export GITHUB_TOKEN="your-token-here"
   ./scripts/process_binary.py \
     -b 'llvm-ar,llvm-nm' \
     "https://github.com/llvm/llvm-project/releases/download/llvmorg-19.1.2/LLVM-19.1.2-macOS-ARM64.tar.xz"
   ```

### Caching

The script implements caching for both downloaded tarballs and extracted files:

- Downloaded tarballs are cached in `~/.cache/llvm-binary-releases` by default
- Extracted files are cached in `./extract-cache` by default
- Use `--no-cache` to force fresh downloads and extractions
- Use `--clean-cache` to clear both caches

### Output Format

In dry-run mode, for each binary the script creates:
1. A directory named `{binary}-{version}-{platform}-{os}`
2. The extracted binary file
3. A metadata.json file containing:
   - Release information
   - Source details
   - Cache locations
   - File type information

## GitHub Workflow

When not in dry-run mode and with a valid GITHUB_TOKEN, the script will:
1. Create a new GitHub release for each binary
2. Upload the binary as a release asset
3. Add appropriate tags and metadata

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a new Pull Request

## License

This repository is under the Apache 2.0 License. Note that the LLVM binaries themselves are subject to the LLVM License.