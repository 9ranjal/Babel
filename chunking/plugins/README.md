# Plugin Architecture for Chunking Pipeline

This directory contains the plugin-based architecture for the chunking pipeline, allowing for dynamic processing of different file types.

## Overview

The plugin architecture provides:
- **Extensibility**: Easy addition of new file type processors
- **Modularity**: Each processor is self-contained
- **Dynamic Discovery**: Plugins are automatically discovered and registered
- **Configuration**: Flexible configuration per processor type
- **Validation**: Maintains schema compatibility

## Architecture

### Core Components

1. **`base.py`** - Abstract base class `ChunkProcessor`
2. **`manager.py`** - `PluginManager` for orchestration
3. **`markdown.py`** - Markdown file processor
4. **`excel.py`** - Excel/CSV file processor

### Plugin Interface

All processors must implement the `ChunkProcessor` interface:

```python
class ChunkProcessor(ABC):
    def process(self, file_path: str) -> List[Dict[str, Any]]:
        """Process a file and return chunks."""
        pass
    
    def can_process(self, file_path: str) -> bool:
        """Check if this processor can handle the file."""
        pass
```

## Usage

### Basic Usage

```python
from chunking.plugins import plugin_manager

# Process a single file
chunks = plugin_manager.process_file("data/sample.md")

# Process a directory
chunks = plugin_manager.process_directory("data/furnace/")
```

### With Configuration

```python
config = {
    "MarkdownProcessor": {
        "chunk_size": 100,
        "overlap": 0.3
    },
    "ExcelProcessor": {
        "chunk_size": 50,
        "text_columns": ["Question", "Answer"]
    }
}

plugin_manager.set_config(config)
chunks = plugin_manager.process_file("data/questions.xlsx")
```

### Using the Plugin Runner

```bash
# Process markdown files
python chunking/runners/plugin_runner.py \
    --source data/furnace \
    --out output/chunks.json \
    --validate

# Process with custom config
python chunking/runners/plugin_runner.py \
    --source data/furnace \
    --out output/chunks.json \
    --config config.json \
    --limit 100
```

## Available Processors

### MarkdownProcessor

- **File Types**: `.md`, `.markdown`
- **Features**:
  - Parses markdown sections
  - Extracts metadata from filename
  - Chunks content with overlap
  - Maintains document structure

### ExcelProcessor

- **File Types**: `.xlsx`, `.xls`, `.csv`
- **Features**:
  - Reads structured data
  - Converts rows to text chunks
  - Configurable text columns
  - Handles missing data gracefully

## Configuration

Each processor supports configuration:

```json
{
  "MarkdownProcessor": {
    "chunk_size": 100,
    "overlap": 0.3,
    "min_chunk_size": 10,
    "max_chunk_size": 500
  },
  "ExcelProcessor": {
    "chunk_size": 50,
    "overlap": 0.2,
    "text_columns": ["Question", "Answer", "Explanation"],
    "separator": " | "
  }
}
```

## Adding New Processors

To add a new processor:

1. Create a new file in `chunking/plugins/`
2. Inherit from `ChunkProcessor`
3. Implement required methods
4. The processor will be auto-discovered

Example:

```python
from .base import ChunkProcessor

class PDFProcessor(ChunkProcessor):
    def can_process(self, file_path: str) -> bool:
        return file_path.endswith('.pdf')
    
    def process(self, file_path: str) -> List[Dict[str, Any]]:
        # Implementation here
        pass
```

## Testing

Run the test suite:

```bash
# Test plugin architecture
python test_plugin_architecture.py

# Test full pipeline
python test_plugin_full_pipeline.py

# Test with runner
python chunking/runners/plugin_runner.py \
    --source data/furnace \
    --out test_output.json \
    --validate
```

## Output Schema

All processors maintain the same output schema:

```json
{
  "chunk_id": "unique_identifier",
  "chunk_text": "processed text content",
  "chunk_word_count": 150,
  "chunk_type": "markdown|excel",
  "topic": "extracted topic",
  "author": "extracted author",
  "embedding": null,
  "semantic_type": {...},
  "retrieval_score": null,
  "quality_flag": null,
  "source_chunk": "file_path#section",
  "source_id": "source_identifier"
}
```

## Benefits

1. **Scalability**: Easy to add new file types
2. **Maintainability**: Each processor is isolated
3. **Flexibility**: Configurable per processor type
4. **Reliability**: Consistent schema across all processors
5. **Testability**: Each processor can be tested independently

## Future Enhancements

- PDF processor
- Web scraper processor
- Audio transcription processor
- Image caption processor
- Multi-language support
- Parallel processing
- Progress tracking
- Error recovery 