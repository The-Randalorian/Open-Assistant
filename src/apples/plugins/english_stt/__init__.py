#!/usr/bin/env python3

import logging
import json
import os
import re
import threading
import urllib.request
import wave

import audioop
import deepspeech
import numpy as np

from ... import plugins

core = plugins.services["core"][0]
terminal = plugins.services["terminal"][0]
audio_recorder = plugins.services["audio_recorder"][0]
actions = plugins.services["actions"][0]

_logger = logging.getLogger(f"{__name__}")

WAVE_OUTPUT_FILENAME = "apples/plugins/english_stt/lastRecord.wav"

default_audio_src = audio_recorder.get_audio_source(device=1)
working = False
AUTO = object()

with open(r"apples/plugins/english_stt/en_us_replacements.json") as f:
    replacements = json.load(f)
    replacements = dict((re.escape(k), v) for k, v in replacements.items())
    pattern = re.compile("|".join(replacements.keys()))

try:
    dsModel = deepspeech.Model(
        r"apples/plugins/english_stt/deepspeech-0.9.3-models/deepspeech-0.9.3-models.pbmm",
    )
    dsModel.enableExternalScorer(
        r"apples/plugins/english_stt/deepspeech-0.9.3-models/deepspeech-0.9.3-models.scorer"
    )
except RuntimeError:
    _logger.info("Downloading deepspeech models")
    os.makedirs(r"apples/plugins/english_stt/deepspeech-0.9.3-models")
    _logger.info("Downloading deepspeech .pbmm")
    urllib.request.urlretrieve(
        "https://github.com/mozilla/DeepSpeech/releases/download/v0.9.3/deepspeech-0.9.3-models.pbmm",
        r"apples/plugins/english_stt/deepspeech-0.9.3-models/deepspeech-0.9.3-models.pbmm"
    )
    _logger.info("Downloading deepspeech .scorer")
    urllib.request.urlretrieve(
        "https://github.com/mozilla/DeepSpeech/releases/download/v0.9.3/deepspeech-0.9.3-models.scorer",
        r"apples/plugins/english_stt/deepspeech-0.9.3-models/deepspeech-0.9.3-models.scorer"
    )
    dsModel = deepspeech.Model(
        r"apples/plugins/english_stt/deepspeech-0.9.3-models/deepspeech-0.9.3-models.pbmm",
    )
    dsModel.enableExternalScorer(
        r"apples/plugins/english_stt/deepspeech-0.9.3-models/deepspeech-0.9.3-models.scorer"
    )

# dsModel.enableDecoderWithLM(
#    r"english_stt\model\lm.binary",
#    r"english_stt\model\trie",
#    0.75,
#    1.85)

# DeepSpeech locks up after the first few frames, this clears that up
# THIS WAS ADDED WITH DEEPSPEECH 0.6.0, AND MAY NO LONGER BE NEEDED
temp_stream = dsModel.createStream()
temp_stream.feedAudioContent([0, 0, 0, 0, 65535, 65535, 65535, 65535] * 8192)
temp_stream.finishStream()

# services["userInterface"][0].addCommands({"trigger": trigger})

# core.addStart(trigger)
# core.addStart(start_thread)
# core.addClose(closeThread)
# core.addLoop(loopTask)


def trigger(audsrc=AUTO, *args):
    global working
    if not working:
        working = True
        global core, audio_recorder, dsModel, default_audio_src, actions, pattern, replacements
        if audsrc == AUTO:
            audsrc = default_audio_src
        # audio_recorder = services["audio_recorder"][0]
        # audsrc = audio_recorder.AudioSource()
        stream = dsModel.createStream()
        audbuf = audsrc.get_buffer()
        recorded_frames = []
        cnt = 0
        vc = -1
        timeout = int(16000 * 10)
        while timeout > 0:
            cnt += 1
            sample = next(audbuf)
            # print(sample)
            vol = audioop.rms(sample, 2)
            # print(vol)
            if vc < 0:
                if vol >= 800:
                    vc = 0
            else:
                if vol < 500:
                    vc += 1
                else:
                    vc = 0
            if vc > 128:
                break
            # print("#"*vol, end="")
            # print(sample)
            recorded_frames.append(sample)
            dat = np.frombuffer(sample, np.int16)
            timeout -= len(dat)
            # print(timeout)
            stream.feedAudioContent(dat)
            # print(dat)
        audbuf.stop_recording()
        # next(audsrc)
        wave_file = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
        wave_file.setnchannels(1)
        wave_file.setsampwidth(2)
        wave_file.setframerate(16000)
        wave_file.writeframes(b''.join(recorded_frames))
        wave_file.close()
        try:
            stt = stream.finishStream()
        except Exception as e:
            _logger.debug(e)
            stt = None
        if stt:
            _logger.debug(stt)
            stt = pattern.sub(lambda m: replacements[re.escape(m.group(0))], stt)
            _logger.debug(stt)
            try:
                actions.process_text(stt)
            except Exception as e:
                _logger.info("Error Processing Audio")
                print(e)
                # raise(e)
        else:
            _logger.info("No intelligible audio heard.")
        working = False


@terminal.command("english_stt.trigger")
@terminal.command("trigger")
def trigger_command(**kwargs):
    trigger()
