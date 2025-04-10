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

async def process_audio(websocket):
    logger.info("Client connected")
    audio_buffer = []
    sample_rate = 16000
    connection_id = id(websocket)
    conversation_histories[connection_id] = []

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

                            # Add to conversation history
                            conversation_histories[connection_id].append({
                                "role": "user",
                                "content": user_input
                            })

                            # Get AI response
                            response = client.chat.completions.create(
                                model="gpt-4-0125-preview",
                                messages=conversation_histories[connection_id],
                                temperature=0.85,
                                max_tokens=150
                            )
                            ai_response = response.choices[0].message.content
                            logger.info(f"AI response: {ai_response}")

                            # Add AI response to history
                            conversation_histories[connection_id].append({
                                "role": "assistant",
                                "content": ai_response
                            })

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
                                    "voice": "alloy"
                                }
                            )

                            if tts_response.status_code == 200:
                                audio_data = tts_response.content
                                logger.info("TTS conversion successful")

                                # Send response
                                response_message = json.dumps({
                                    "type": "audio_response",
                                    "audio": audio_data.hex()
                                })
                                await websocket.send(response_message)
                                logger.info("Audio response sent to client")

                            # Cleanup
                            if os.path.exists(temp_file):
                                os.remove(temp_file)
                            audio_buffer = []

                        except Exception as e:
                            logger.error(f"Error processing audio: {e}", exc_info=True)

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