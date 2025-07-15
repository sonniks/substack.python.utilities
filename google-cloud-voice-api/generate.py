# generate.py

import argparse
import os
from google.cloud import texttospeech


"""
Use this to quickly test Google Cloud Text-to-Speech API with Despina HD voice using natural text from file input.
see requirements.txt for dependencies (google-cloud-texttospeech)
Browse voices here: https://cloud.google.com/text-to-speech/docs/chirp3-hd
"""


def synthesize_speech_from_text(text: str, voice_name: str, output_file: str):
    """
    Synthesize speech from the input string of text.
    :param text:
    :param voice_name:
    :param output_file:
    :return:
    """
    client = texttospeech.TextToSpeechClient()
    synthesis_input = texttospeech.SynthesisInput(text=text)
    voice = texttospeech.VoiceSelectionParams(
        language_code="en-US",
        name=voice_name,
        ssml_gender=texttospeech.SsmlVoiceGender.FEMALE
    )
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3
    )
    response = client.synthesize_speech(
        input=synthesis_input,
        voice=voice,
        audio_config=audio_config
    )
    with open(output_file, "wb") as out:
        out.write(response.audio_content)
    print(f"Audio content written to '{output_file}'")


def parse_arguments():
    """
    Parse command line arguments.
    :return:
    """
    parser = argparse.ArgumentParser(description="Convert plain text file to speech using Google Cloud Text-to-Speech API.")
    parser.add_argument("--credentials", required=True, help="Path to your Google Cloud JSON key file.")
    parser.add_argument("--output", required=True, help="Output MP3 file path.")
    parser.add_argument("--input", required=True, help="Path to plain text file containing input.")
    parser.add_argument("--voice", default="en-US-Chirp3-HD-Despina", help="Voice name (e.g., en-US-Chirp3-HD-Despina).")
    return parser.parse_args()


def main():
    """
    Main function to parse arguments and call the synthesis function.
    :return:
    """
    args = parse_arguments()
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = args.credentials
    with open(args.input, "r", encoding="utf-8") as f:
        text_content = f.read()
    synthesize_speech_from_text(text=text_content, voice_name=args.voice, output_file=args.output)


if __name__ == "__main__":
    main()
