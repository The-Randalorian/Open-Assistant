#!/usr/bin/env python3

import time
import pyaudio
import logging
# import numpy

from ... import plugins

core = plugins.services["core"][0]

_logger = logging.getLogger(f"{__name__}")

audio = pyaudio.PyAudio()

sources = {}


class AudioBuffer:
    def __init__(self, src, **kwargs):
        self.settings = {
            "format": pyaudio.paInt16,
            "channels": 1,
            "rate": 16000,
            "chunk": 256,
            "device": 0,
            "checkInterval": 0.01,
            "strict": True,
            "maxLength": 65535
            }
        self.settings.update(kwargs)
        self.source = src
        self.recording = True
        self._r = True
        self._buffer = b''

    def clear_buffer(self):
        b = self._buffer
        self._buffer = b''
        return b

    def __iter__(self):
        return self

    def __next__(self):
        if self.recording:
            while len(self._buffer) < self.settings["chunk"]:
                time.sleep(self.settings["checkInterval"])
            if self.settings["strict"]:
                b = self._buffer[:self.settings["chunk"]]
                self._buffer = self._buffer[self.settings["chunk"]:]
            else:
                b = self._buffer
                self._buffer = b''
            return b
        else:
            self.stop_recording()
            raise StopIteration

    def stop_recording(self):
        self.recording = False
        if self._r:
            self._r = False
            self.source.remove_buffer(self)

    def append(self, data):
        # print(data)
        self._buffer += data
        if self.settings["maxLength"] > 0:
            if len(self._buffer) > self.settings["maxLength"]:
                self._buffer = (self._buffer[-self.settings["maxLength"]:])


class AudioSource:
    def __init__(self, *args, **kwargs):
        global audio
        self.settings = {
            "format": pyaudio.paInt16,
            "channels": 1,
            "rate": 16000,
            "chunk": 256,
            "device": 0,
            "checkInterval": 0.01,
            "strict": True
            }
        self.settings.update(kwargs)
        self.stream = audio.open(
            format=self.settings["format"],
            channels=self.settings["channels"],
            rate=self.settings["rate"],
            input=True,
            frames_per_buffer=self.settings["chunk"],
            input_device_index=self.settings["device"],
            stream_callback=self._get_recording_callback())
        self.stream.start_stream()
        self.recording = True
        self._r = True
        self._buffers = []
        # self._buffer = b''

    def get_buffer(self):
        ab = AudioBuffer(src=self, **self.settings)
        self._buffers.append(ab)
        return ab

    def _get_recording_callback(self):
        def callback(in_data, _, __, ___):
            # print(in_data)
            self._buffer = in_data
            for buffer in self._buffers:
                buffer.append(in_data)
            # print(self._buffer)
            # print(self._buffers)
            return in_data, pyaudio.paContinue
        return callback

    def stop_recording(self):
        self.recording = False
        if self._r:
            self.stream.stop_stream()
            self.stream.close()
            self._r = False

    def remove_buffer(self, buffer):
        self._buffers.remove(buffer)


class VirtualAudioSource(AudioSource):
    def __init__(self, file_object, **kwargs):
        global audio
        self._data = file_object
        self.settings = {
            "format": pyaudio.paInt16,
            "channels": 1,
            "rate": 16000,
            "chunk": 256,
            "device": 0,
            "checkInterval": 0.01,
            "strict": True
            }
        self.settings.update(kwargs)
        self._r = True
        self._buffers = []
        # self._buffer = b''

    def update_buffers(self):
        data = self._data.read()
        for buffer in self._buffers:
            buffer.append(data)

    def get_buffer(self):
        self.update_buffers()
        self._data.seek(0)
        ab = AudioBuffer(src=self, maxLength=0, **self.settings)
        self._buffers.append(ab)
        ab.append(self._data.read())
        return ab

    def stop_recording(self):
        self.recording = False
        if self._r:
            self.stream.stop_stream()
            self.stream.close()
            self._r = False


def get_audio_source(device_type='pyaudio', *args, **kwargs):
    if device_type.strip().lower() == "pyaudio":
        return AudioSource(*args, **kwargs)
    elif device_type.strip().lower() == "virtual":
        return VirtualAudioSource(*args, **kwargs)


'''
audio = pyaudio.PyAudio()
src = AudioSource()
buf = src.getBuffer()
cntr = 0
while True:
    print(next(buf))
    cntr += 1
    print(cntr) #'''


@core.cleanup_task
def shutdown():
    audio.terminate()
