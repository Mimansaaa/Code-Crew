import openai

openai.api_key = ""

audio_file = open("audiofile.mp3", "rb")
transcript = openai.Audio.translate("whisper-1", audio_file)
transcribed_text = transcript['text']

print(transcribed_text)
