<!-- Use this file to provide workspace-specific custom instructions to Copilot. For more details, visit https://code.visualstudio.com/docs/copilot/copilot-customization#_use-a-githubcopilotinstructionsmd-file -->

# AI SVN Code Review Tool - Copilot Instructions

This is a Python-based AI code review tool that monitors SVN commits and provides automated code analysis.

## Project Overview

- **Purpose**: Monitor SVN commits, analyze code changes using AI, and send notifications via DingTalk
- **Language**: Python 3.7+
- **Platform**: Windows
- **Architecture**: Modular design with separate components for SVN monitoring, AI analysis, and DingTalk integration

## Key Components

1. **config_manager.py**: Configuration management with YAML support
2. **svn_monitor.py**: SVN repository monitoring and commit tracking
3. **ai_reviewer.py**: AI-powered code analysis using OpenAI-compatible APIs
4. **dingtalk_bot.py**: DingTalk bot integration for notifications
5. **main.py**: Main application entry point with scheduling

## Coding Guidelines

- Follow PEP 8 style guidelines
- Use type hints for better code documentation
- Implement proper error handling and logging
- Use dataclasses for structured data
- Maintain modular architecture
- Support both direct execution and Windows service deployment

## Configuration

- Use YAML files for configuration management
- Support environment-specific settings
- Provide example configurations
- Implement user mapping for SVN to DingTalk users

## Dependencies

- requests: HTTP API calls
- pyyaml: Configuration file parsing
- schedule: Task scheduling
- pywin32: Windows service integration (optional)
- svn: SVN command line integration

## Error Handling

- Implement comprehensive logging
- Graceful error recovery
- User-friendly error messages
- Service health monitoring
