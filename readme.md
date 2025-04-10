# VBAIgame - Speech-to-Speech NPC Interaction

## Project Overview

A 3D adventure game featuring AI-powered NPCs that can engage in speech-to-speech conversations. Players can interact with NPCs (HR Director and CEO) using natural voice communication, and the NPCs respond both textually and audibly using OpenAI's APIs.

## Prerequisites

- Python 3.10 or higher
- OpenAI API key
- Operating System: Linux/Zorin OS (tested on)

## Installation

1. Clone the repository:

```bash
git clone https://github.com/ktscates/ai-assessment-.git
cd ai-assessment-
```

## Required Python Packages

- pygame
- PyOpenGL
- numpy
- openai
- python-dotenv
- websockets
- sounddevice
- soundfile
- langdetect

## Known Issues

- NPCs may not always respond to speech input
- Event loop conflicts in audio processing
- Occasional WebSocket connection issues

## Future Improvements

- Better error handling for audio processing
- Improved conversation history management
- Enhanced speech recognition accuracy
- Optimized WebSocket communication
- Code refactoring
