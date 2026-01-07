# Changelog

## [2.1.0] - 2026-01-07

### Added
- **LFM2.5 support** - Just released Jan 5, 2026!
  - `ollama/lfm2.5:1.2b` - General purpose (28T tokens training)
  - `ollama/lfm2.5-audio` - 8x faster audio on mobile CPUs
  - `ollama/lfm2.5-vl:1.6b` - Vision-language model
- **Qwen 3 family** - 0.6B, 1.7B, 4B, 8B models
- **Production setup** - Complete .gitignore, test suite, production guide
- **Test scripts** - Automated testing for LFM2.5 and Qwen 3
- **Multi-provider APIs** - Z.AI GLM-4.7, MiniMax M2.1 support

### Changed
- Default tiny model: `ollama/lfm2.5:1.2b` (was `ollama/lfm2:1.2b`)
- Standard model: `minimax-m2.1` (10B active, great for coding)
- Improved model registry with parameter counts

### Fixed
- Proper TypeScript compilation
- Production build configuration
- Test suite with proper error handling

## [2.0.0] - 2026-01-06

### Added
- Initial unified RLM MCP server
- Multi-provider support (OpenAI, Anthropic, Google, DeepSeek, xAI, Ollama)
- Budget tracking and auto-model switching
- Two-tool architecture (`rlm` and `state`)

