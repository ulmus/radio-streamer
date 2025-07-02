# Testing Guide for Radio Streamer

This document describes the testing framework and how to run tests for the radio streamer project.

## Test Structure

The test suite is organized using pytest and follows a modular structure:

```
tests/
├── __init__.py                 # Test package initialization
├── conftest.py                 # Pytest configuration and fixtures
├── test_media_types.py         # Tests for media type models
├── test_media_player.py        # Tests for MediaPlayer class
├── test_media_modules.py       # Tests for modular media components
├── test_api.py                 # Tests for FastAPI endpoints
├── test_streamdeck.py          # Tests for StreamDeck functionality
├── test_configuration.py       # Tests for configuration management
├── test_integration_full.py    # Integration tests
└── test_legacy_compatibility.py # Converted legacy tests
```

## Test Categories

Tests are organized into several categories using pytest markers:

- **unit**: Unit tests for individual components
- **integration**: Integration tests for component interaction
- **api**: API endpoint tests
- **streamdeck**: StreamDeck hardware interface tests
- **hardware**: Tests requiring physical hardware
- **slow**: Tests that take longer to run

## Running Tests

### Prerequisites

Install test dependencies:
```bash
pip install -e .[test]
```

Or use the test runner:
```bash
python run_tests.py --install-deps
```

### Basic Test Execution

Run all tests:
```bash
pytest tests/
# or
python run_tests.py --all
```

Run specific test categories:
```bash
# Unit tests only
pytest tests/ -m unit
python run_tests.py --unit

# Integration tests
pytest tests/ -m integration
python run_tests.py --integration

# API tests
pytest tests/test_api.py
python run_tests.py --api

# StreamDeck tests (excluding hardware)
pytest tests/test_streamdeck.py -m "not hardware"
python run_tests.py --streamdeck

# Fast tests (exclude slow and hardware tests)
pytest tests/ -m "not slow and not hardware"
python run_tests.py --fast
```

### Test Options

#### Verbose Output
```bash
pytest tests/ -v
python run_tests.py --verbose
```

#### Coverage Report
```bash
pytest tests/ --cov=. --cov-report=term-missing --cov-report=html
python run_tests.py --coverage
```

#### Include Hardware Tests
```bash
pytest tests/
python run_tests.py --hardware
```

## Test Configuration

### Pytest Configuration

The `pytest.ini` file contains the main pytest configuration:

- Test discovery patterns
- Coverage settings
- Warning filters
- Custom markers

### Fixtures

Common fixtures are defined in `tests/conftest.py`:

- `temp_config_file`: Temporary configuration file for testing
- `temp_music_folder`: Temporary music folder with test albums
- `mock_vlc`: Mock VLC player for testing without audio
- `mock_streamdeck`: Mock StreamDeck device for testing without hardware
- `mock_media_player`: Configured mock media player
- `api_client`: FastAPI test client

### Mocking Strategy

The test suite uses extensive mocking to:

- **VLC Player**: Mock audio playback to avoid requiring audio hardware
- **StreamDeck**: Mock hardware interface to test logic without devices
- **File System**: Use temporary files and directories
- **Network**: Mock HTTP requests and responses

## Test Coverage

The test suite aims for comprehensive coverage of:

### Core Components
- ✅ Media types and models (`test_media_types.py`)
- ✅ MediaPlayer class (`test_media_player.py`)
- ✅ Modular media components (`test_media_modules.py`)
- ✅ Configuration management (`test_configuration.py`)

### API Layer
- ✅ FastAPI endpoints (`test_api.py`)
- ✅ Request/response handling
- ✅ Error handling
- ✅ CORS configuration

### Hardware Interfaces
- ✅ StreamDeck controller (`test_streamdeck.py`)
- ✅ Image creation and button management
- ✅ Hardware detection and fallbacks

### Integration
- ✅ Full system workflows (`test_integration_full.py`)
- ✅ Component interaction
- ✅ Error recovery
- ✅ Performance testing

### Legacy Compatibility
- ✅ Converted standalone tests (`test_legacy_compatibility.py`)
- ✅ Backward compatibility verification
- ✅ Migration testing

## Writing New Tests

### Test Structure

Follow this structure for new test files:

```python
"""
Tests for [component name]
"""

import pytest
from unittest.mock import Mock, patch

class TestComponentName:
    """Test [component] functionality"""
    
    def test_basic_functionality(self):
        """Test basic functionality"""
        # Arrange
        # Act
        # Assert
        pass
    
    @patch('module.dependency')
    def test_with_mocking(self, mock_dependency):
        """Test with mocked dependencies"""
        # Setup mocks
        mock_dependency.return_value = expected_value
        
        # Test code
        result = function_under_test()
        
        # Assertions
        assert result == expected_result
        mock_dependency.assert_called_once()
```

### Test Naming

- Test files: `test_[component].py`
- Test classes: `Test[ComponentName]`
- Test methods: `test_[specific_functionality]`

### Fixtures Usage

Use existing fixtures when possible:

```python
def test_with_config(self, temp_config_file):
    """Test using temporary config file"""
    config_manager = MediaConfigManager(temp_config_file)
    # Test code...

def test_with_media_player(self, mock_media_player):
    """Test using mock media player"""
    result = mock_media_player.get_status()
    # Test code...
```

### Markers

Add appropriate markers to tests:

```python
@pytest.mark.unit
def test_unit_functionality(self):
    """Unit test"""
    pass

@pytest.mark.integration
def test_integration_workflow(self):
    """Integration test"""
    pass

@pytest.mark.hardware
def test_with_hardware(self):
    """Test requiring hardware"""
    pass

@pytest.mark.slow
def test_performance(self):
    """Slow running test"""
    pass
```

## Continuous Integration

The test suite is designed to run in CI environments:

### Environment Requirements
- Python 3.13+
- No audio hardware required (mocked)
- No StreamDeck hardware required (mocked)
- Temporary file system access

### CI Configuration
```yaml
# Example GitHub Actions configuration
- name: Install dependencies
  run: pip install -e .[test]

- name: Run tests
  run: python run_tests.py --fast --coverage

- name: Upload coverage
  uses: codecov/codecov-action@v1
```

## Troubleshooting

### Common Issues

1. **VLC not available**: Tests should skip gracefully with mocking
2. **StreamDeck not available**: Hardware tests are automatically skipped
3. **Permission errors**: Use temporary directories provided by fixtures
4. **Import errors**: Check that all dependencies are installed

### Debug Mode

Run tests with debugging:
```bash
pytest tests/ -v -s --tb=long
python run_tests.py --verbose
```

### Specific Test Debugging

Run a single test:
```bash
pytest tests/test_media_player.py::TestMediaPlayerCore::test_get_status -v -s
```

## Legacy Test Migration

The old standalone test scripts have been converted to pytest:

- `test_spotify_integration.py` → `test_legacy_compatibility.py::TestSpotifyIntegration`
- `test_streamdeck_modular.py` → `test_legacy_compatibility.py::TestStreamDeckModular`
- `test_now_playing_button.py` → `test_legacy_compatibility.py::TestNowPlayingButton`
- `test_overlay_baking.py` → `test_legacy_compatibility.py::TestOverlayBaking`
- `test_streamdeck_abbey_road.py` → `test_legacy_compatibility.py::TestStreamDeckAbbeyRoad`
- `test_api.py` → `test_legacy_compatibility.py::TestAPICompatibility`

The original files can be removed after verifying the new test suite works correctly.

## Performance Benchmarks

The test suite includes performance tests to ensure:

- Startup time < 5 seconds
- API response time < 1 second
- Memory usage within reasonable bounds
- No memory leaks in long-running tests

Run performance tests:
```bash
pytest tests/ -m "not slow" --durations=10
```