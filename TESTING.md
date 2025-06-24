# Testing Guide for Marbitz Battlebot

This document provides an overview of the testing framework and guidelines for writing tests for the Marbitz Battlebot project.

## Testing Structure

The project uses pytest as the testing framework with the following structure:

- `tests/` - Main test directory
  - `conftest.py` - Common test fixtures and utilities
  - `unit/` - Unit tests for individual modules
    - `test_storage.py` - Tests for storage module
    - `test_state.py` - Tests for state management
    - `test_leaderboard.py` - Tests for leaderboard functionality
    - `test_battle.py` - Tests for battle mechanics
  - `integration/` - Integration tests
    - `test_handlers.py` - Tests for command handlers

## Running Tests

You can run the tests in several ways:

```bash
# Run all tests
pytest

# Run tests with coverage report
pytest --cov=marbitz_battlebot

# Run specific test file
pytest tests/unit/test_storage.py

# Run a specific test
pytest tests/unit/test_storage.py::TestStorage::test_load_json_file_success

# Or use the run_tests.bat script (Windows)
run_tests.bat

# Or use the run_tests.py script (cross-platform)
python run_tests.py
```

## Test Coverage

The current test coverage is around 27%, which is a good starting point. The goal is to increase this to at least 80% for critical modules.

Areas that need more test coverage:
- `bot.py` (0% coverage)
- `handlers.py` (11% coverage)
- `leaderboard.py` (28% coverage)

## Writing New Tests

When writing new tests, follow these guidelines:

1. **Test Naming**: Use descriptive names that indicate what is being tested
2. **Arrange-Act-Assert**: Structure tests with clear setup, action, and verification
3. **Mocking**: Use mocks for external dependencies (e.g., Telegram API)
4. **Fixtures**: Use fixtures for common setup and teardown
5. **Isolation**: Tests should be independent and not rely on the state from other tests

Example test structure:

```python
def test_some_function():
    # Arrange - set up test data and conditions
    test_data = {"key": "value"}
    
    # Act - call the function being tested
    result = some_function(test_data)
    
    # Assert - verify the results
    assert result == expected_result
```

## Continuous Integration

The project uses GitHub Actions for continuous integration. Tests are automatically run on every push to the main branch and on pull requests.

The workflow configuration is in `.github/workflows/tests.yml`.

## Adding More Tests

To improve test coverage, focus on adding tests for:

1. **Critical Paths**: Core functionality that must work correctly
2. **Edge Cases**: Boundary conditions and error handling
3. **User Interactions**: Command handlers and user flows
4. **Data Persistence**: Storage and retrieval operations

## Test Fixtures

Common test fixtures are defined in `conftest.py` and include:

- `temp_dir`: Creates a temporary directory for test files
- `mock_update`: Creates a mock Telegram Update object
- `mock_context`: Creates a mock Context object for handlers

Use these fixtures to simplify test setup and ensure consistency across tests.