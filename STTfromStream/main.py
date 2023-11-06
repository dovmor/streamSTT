"""
DISCLAIMER:

This code is provided as-is without any express or implied warranties or guarantees of any kind. 
The author of this code takes no responsibility for any damage or harm that may occur as a result of using this code. 
This includes, but is not limited to, damage to hardware, software, data, or any other assets.

This code is intended for educational purposes only and was not designed for use in a production environment. 
It has not been tested in a production environment and its suitability for such use has not been evaluated. 
Use of this code in a production environment is at your own risk.

By using this code, you understand and agree to these terms.
"""

import os
from datetime import datetime
import azure.cognitiveservices.speech as speechsdk
import requests
from pydub import AudioSegment
import io 


# This is a set of words that we want to find in the audio stream. You can replace these words with your own.
find_words = {'שלום', 'אקדח', 'אחרת'}  # replace with your words


# Define a class that inherits from PullAudioInputStreamCallback, which is a callback class provided by Azure's speech SDK.
# This class will handle the pulling of audio data from an input stream.
class RawStream(speechsdk.audio.PullAudioInputStreamCallback):
    def __init__(self, url):
        super().__init__()

        # Open a raw stream to the URL. This will be used to pull the audio data.
        self.stream = requests.get(url, stream=True).raw

    def read(self, buffer):
        # Read raw audio data
        raw_data = self.stream.read(len(buffer) * 2 * 2)  # 2 for stereo, 2 for 16-bit

        # Convert raw audio data to an AudioSegment
        audio = AudioSegment.from_raw(io.BytesIO(raw_data),
                                      sample_width=2,  # 16-bit
                                      channels=2,  # stereo
                                      frame_rate=44100)  # 44.1 kHz

        # Convert audio to mono and 16 kHz
        audio = audio.set_channels(1).set_frame_rate(16000)

        # Convert audio back to raw data
        data = audio.raw_data

        buffer[:len(data)] = data
        return len(data)

def recognize_from_stream(url):
    # Create an audio stream from the network stream
    stream = RawStream(url)
    audio_input = speechsdk.audio.PullAudioInputStream(stream)

    # Create an audio configuration from the audio stream
    audio_config = speechsdk.audio.AudioConfig(stream=audio_input)

    # Use the audio configuration in the speech recognizer
    speech_config = speechsdk.SpeechConfig(subscription="[Enter Your Key HERE]", region="westeurope")
    speech_config.speech_recognition_language="he-IL"
    speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)


    done = False

    def stop_cb(evt):
        """callback that stops continuous recognition upon receiving an event `evt`"""
        print('CLOSING on {}'.format(evt))
        nonlocal done
        done = True

    def recognized_cb(evt):
        """callback that prints recognized speech in red if any specific word is recognized"""
        if any(word in evt.result.text for word in find_words):
            print("word found:" + '\033[91m {}\033[0m'.format(evt.result.text[::-1]) + " at: " + str(datetime.now()))
        else:
            print('RECOGNIZED: {}'.format(evt.result.text[::-1]))

    speech_recognizer.recognized.connect(recognized_cb)
    speech_recognizer.session_stopped.connect(stop_cb)
    speech_recognizer.canceled.connect(lambda evt: print('CANCELED: {}'.format(evt)))

    # Start continuous speech recognition
    speech_recognizer.start_continuous_recognition()
    while not done:
        pass

    speech_recognizer.stop_continuous_recognition()

recognize_from_stream('http://[Hostname or IP]:5000/audio')