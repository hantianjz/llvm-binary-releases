# LLVM Binary Releases

This repository provides individual LLVM binaries extracted from official LLVM releases. Instead of downloading the complete LLVM distribution (which can be several gigabytes), you can download just the specific binary tools you need.

## Currently Available Binaries

### Analysis tools
- `clang-format` - Code formatting tool for C/C++/Java/JavaScript/Objective-C/Protobuf/C#
- `clang-tidy` - Clang-based C++ linter tool with various checks

## Request Additional Binaries

If you need other LLVM binaries that aren't currently included in the releases, please [open an issue](../../issues) with:
1. The name of the binary
2. A brief description of what it does
3. Why you need it as a standalone binary

## Project Creation

This project was entirely created by [Goose](https://github.com/block/goose), an AI assistant developed by Block. The entire implementation including:
- Python script for binary extraction
- GitHub workflow for releases
- Documentation and project structure

was generated through conversation with Goose using the Claude-3 Sonnet model (claude-3-sonnet@20240229) as of March 2024.

The human involvement was limited to providing the initial concept and reviewing/approving the generated code. This serves as an interesting example of AI-assisted repository creation and maintenance.

## License

This repository is under the Apache 2.0 License. Note that the LLVM binaries themselves are subject to the LLVM License.