# LLVM Binary Extractor

This tool extracts individual LLVM binaries from official LLVM release packages. It provides a way to access specific LLVM binaries without downloading the complete LLVM distribution.

## Local Usage

### Setup

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

### Command Line Options

```bash
Usage: ./scripts/process_binary.py [options] <binary_url>
Options:
  -o, --output-dir   Directory to save extracted binaries (default: ./output)
  -c, --cache-dir    Directory to cache downloaded tarballs (default: ~/.cache/llvm-binary-releases)
  -e, --extract-dir  Directory for extracted files cache (default: ./extract-cache)
  -f, --binaries-file File containing list of binaries to extract (default: ./binaries.txt)
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

2. Extract binaries specified in binaries.txt:
   ```bash
   ./scripts/process_binary.py \
     "https://github.com/llvm/llvm-project/releases/download/llvmorg-19.1.2/LLVM-19.1.2-macOS-ARM64.tar.xz"
   ```

## GitHub Workflow

The repository includes a GitHub workflow that can automatically create releases from extracted binaries.

### Using the Workflow

1. Go to the Actions tab in your repository
2. Select "Create LLVM Binary Releases"
3. Click "Run workflow"
4. Enter:
   - **Binary URL**: URL to the LLVM release package
   - **Tag Prefix**: Tag for the release (e.g., "llvm-19.1.2")
5. Click "Run workflow"

The workflow will:
1. Run on Ubuntu Linux (GitHub's standard runner)
2. Extract the specified binaries
3. Create a GitHub release
4. Upload the binaries as release assets

### Release Structure

The workflow creates a release with:
- Tag: The specified tag prefix
- Release notes containing:
  - Source URL
  - Workflow reference
- All extracted binaries as release assets

## Binaries File Format

The `binaries.txt` file specifies which binaries to extract. The file format:
- One binary name per line
- Lines starting with # are comments
- Empty lines are ignored

Example `binaries.txt`:
```txt
# Core binutils replacements
llvm-ar
llvm-nm
llvm-objcopy

# Debug tools
lldb
dsymutil

# Compiler tools
clang
clang++
```

### Caching

The script implements caching for both downloaded tarballs and extracted files:

- Downloaded tarballs are cached in `~/.cache/llvm-binary-releases` by default
- Extracted files are cached in `./extract-cache` by default
- Use `--no-cache` to force fresh downloads and extractions
- Use `--clean-cache` to clear both caches

## LLVM Binary Categories

The default `binaries.txt` includes the following categories:

### Core Tools
- `llvm-ar` - Archive manager for creating and modifying static libraries
- `llvm-nm` - List symbols from object files
- `llvm-objcopy` - Object copying and binary translation tool
- `llvm-objdump` - Object file dumping tool
- `llvm-ranlib` - Generate index for archives
- `llvm-readelf` - Display information about ELF files
- `llvm-size` - Print size information from object files
- `llvm-strings` - Print strings from binary files
- `llvm-strip` - Remove symbols and sections from files

### Debug Tools
- `lldb` - LLVM debugger
- `lldb-server` - Debug server for remote debugging
- `dsymutil` - Manipulate archived DWARF debug symbols

### Compiler Tools
- `clang` - C/C++/Objective-C compiler
- `clang++` - C++ compiler
- `lld` - LLVM linker
- `llvm-config` - Get information about LLVM compilation
- `llvm-cov` - Code coverage tool
- `llvm-profdata` - Profile data tool

### Analysis Tools
- `scan-build` - Static analyzer
- `clang-format` - Code formatting tool
- `clang-tidy` - Code linting tool
- `llvm-addr2line` - Convert addresses into file names and line numbers
- `llvm-symbolizer` - Convert addresses into source code locations

### Optimization Tools
- `opt` - LLVM optimizer
- `llvm-as` - LLVM assembler
- `llvm-dis` - LLVM disassembler
- `llvm-link` - LLVM bitcode linker

## License

This repository is under the Apache 2.0 License. Note that the LLVM binaries themselves are subject to the LLVM License.