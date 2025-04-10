import asyncio
import websockets
import json
import os
import soundfile as sf
import numpy as np
from openai import OpenAI
from dotenv import load_dotenv
import requests
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
api_key = os.getenv('OPENAI_API_KEY')
if not api_key:
    raise ValueError("OpenAI API key not found")
logger.info("API key loaded successfully")

client = OpenAI(api_key=api_key)

# Store conversation history for each connection
conversation_histories = {}

# NPC voice mapping
VOICE_MAPPING = {
    "HR": "alloy",
    "CEO": "echo",
    "default": "alloy"
}

# NPC personality prompts
NPC_PROMPTS = {
    "HR": """You are Sarah Chen, HR Director at Venture Builder AI. Core traits:
        - Warm but professional demeanor
        - Excellent emotional intelligence
        - Strong ethical boundaries
        Keep responses concise (2-3 sentences) and natural.""",

    "CEO": """You are Michael Chen, CEO of Venture Builder AI. Core traits:
        - Visionary yet approachable
        - Strategic thinker
        - Passionate about venture building
        Keep responses concise (2-3 sentences) and natural."""
}

async def process_audio(websocket):
    logger.info("Client connected")
    audio_buffer = []
    sample_rate = 16000
    connection_id = id(websocket)
    conversation_histories[connection_id] = []
    current_npc = None

    try:
        while True:
            try:
                message = await websocket.recv()
                data = json.loads(message)

                if data.get("type") == "audio_chunk":
                    logger.info("Received audio chunk")
                    audio_chunk = np.frombuffer(bytes.fromhex(data["chunk"]), dtype=np.float32)
                    logger.debug(f"Audio chunk size: {len(audio_chunk)}")
                    audio_buffer.append(audio_chunk)

                    # Update current NPC if provided
                    if "npc_role" in data:
                        current_npc = data["npc_role"]
                        logger.info(f"Updated current NPC to: {current_npc}")

                elif data.get("type") == "end_of_audio":
                    logger.info("Processing complete audio")
                    if audio_buffer:
                        try:
                            # Combine audio chunks and save
                            audio_data = np.concatenate(audio_buffer)
                            temp_file = "temp_audio.wav"
                            sf.write(temp_file, audio_data, sample_rate)

                            # Transcribe audio using Whisper
                            with open(temp_file, "rb") as audio_file:
                                transcript = client.audio.transcriptions.create(
                                    model="whisper-1",
                                    file=audio_file
                                )
                            user_input = transcript.text
                            logger.info(f"Transcribed text: {user_input}")

                            # Get NPC-specific prompt
                            system_prompt = NPC_PROMPTS.get(current_npc, NPC_PROMPTS["HR"])

                            # Prepare messages for chat
                            messages = [
                                {"role": "system", "content": system_prompt},
                                *conversation_histories[connection_id],
                                {"role": "user", "content": user_input}
                            ]

                            # Get AI response
                            response = client.chat.completions.create(
                                model="gpt-4-0125-preview",
                                messages=messages,
                                temperature=0.85,
                                max_tokens=150
                            )
                            ai_response = response.choices[0].message.content
                            logger.info(f"AI response: {ai_response}")

                            # Update conversation history
                            conversation_histories[connection_id].extend([
                                {"role": "user", "content": user_input},
                                {"role": "assistant", "content": ai_response}
                            ])

                            # Keep conversation history manageable
                            if len(conversation_histories[connection_id]) > 10:
                                conversation_histories[connection_id] = conversation_histories[connection_id][-10:]

                            # Select voice based on NPC role
                            voice = VOICE_MAPPING.get(current_npc, VOICE_MAPPING["default"])

                            # Convert to speech
                            tts_response = requests.post(
                                "https://api.openai.com/v1/audio/speech",
                                headers={
                                    "Authorization": f"Bearer {api_key}",
                                    "Content-Type": "application/json"
                                },
                                json={
                                    "model": "tts-1",
                                    "input": ai_response,
                                    "voice": voice
                                }
                            )

                            if tts_response.status_code == 200:
                                audio_data = tts_response.content
                                logger.info("TTS conversion successful")

                                # Send response with both text and audio
                                response_message = json.dumps({
                                    "type": "audio_response",
                                    "text": ai_response,
                                    "audio": audio_data.hex()
                                })
                                await websocket.send(response_message)
                                logger.info("Response sent to client")

                            # Cleanup
                            if os.path.exists(temp_file):
                                os.remove(temp_file)
                            audio_buffer = []

                        except Exception as e:
                            logger.error(f"Error processing audio: {e}", exc_info=True)
                            await websocket.send(json.dumps({
                                "type": "error",
                                "message": str(e)
                            }))

                elif data.get("type") == "interrupt":
                    logger.info("Received interrupt request")
                    audio_buffer = []
                    await websocket.send(json.dumps({
                        "type": "interrupted"
                    }))

            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error: {e}")

    except websockets.exceptions.ConnectionClosed:
        logger.info("Client disconnected")
        if connection_id in conversation_histories:
            del conversation_histories[connection_id]
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)

async def main():
    logger.info("Starting WebSocket server...")
    try:
        async with websockets.serve(process_audio, "localhost", 8765):
            logger.info("WebSocket server is running on ws://localhost:8765")
            await asyncio.Future()  # run forever
    except Exception as e:
        logger.error(f"Server error: {e}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(main())