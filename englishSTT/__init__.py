import threading, time, deepspeech, audioop, re, json
import numpy as np

services = {}
plugin = {}
core = None
audioRecorder = None
runThread = None
threadActive = False
dsModel = None
stream = None
audsrc = None
actions = None
working = False
with open(r"englishSTT\en_us_replacements.json") as f:
    replacements = json.load(f)
    replacements = dict((re.escape(k), v) for k, v in replacements.items())
    pattern = re.compile("|".join(replacements.keys()))

def _register_(serviceList, pluginProperties):
    global services, plugin, core, audioRecorder, dsModel, stream, audsrc, actions
    services = serviceList
    plugin = pluginProperties
    core = services["core"][0]
    audioRecorder = services["audioRecorder"][0]
    actions = services["actions"][0]

    audsrc = audioRecorder.AudioSource(device = 1)

    dsModel = deepspeech.Model(
        r"englishSTT\deepspeech-0.7.0-models\deepspeech-0.7.0-models.pbmm",
        ) # 500)
    #dsModel.enableDecoderWithLM(
    #    r"englishSTT\model\lm.binary",
    #    r"englishSTT\model\trie",
    #    0.75,
    #    1.85)

    # DeepSpeech locks up after the first few frames, this clears that up
    # THIS WAS ADDED WITH DEEPSPEECH 0.6.0, AND MAY NO LONGER BE NEEDED
    stream = dsModel.createStream()
    stream.feedAudioContent([0, 0, 0, 0, 65535, 65535, 65535, 65535] * 8192)
    stream.finishStream()

    services["userInterface"][0].addCommands({"trigger": trigger})

    #core.addStart(trigger)
    #core.addStart(startThread)
    #core.addClose(closeThread)
    #core.addLoop(loopTask)

def trigger(*args):
    global working
    if not working:
        working = True
        global services, plugin, core, audioRecorder, dsModel, audsrc, actions, pattern, replacements
        import wave, pyaudio
        #audioRecorder = services["audioRecorder"][0]
        #audsrc = audioRecorder.AudioSource()
        WAVE_OUTPUT_FILENAME = "englishSTT\lastRecord.wav"
        stream = dsModel.createStream()
        audbuf = audsrc.getBuffer()
        Recordframes = []
        cnt = 0
        vc = -1
        timeout = int(16000 * 10)
        while timeout > 0:
            cnt+=1
            sample = next(audbuf)
            #print(sample)
            vol = audioop.rms(sample,2)
            #print(vol)
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
            #print("#"*vol, end="")
            #print(sample)
            Recordframes.append(sample)
            dat = np.frombuffer(sample, np.int16)
            timeout -= len(dat)
            #print(timeout)
            stream.feedAudioContent(dat)
            #print(dat)
        audbuf.stopRecording()
        #next(audsrc)
        waveFile = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
        waveFile.setnchannels(1)
        waveFile.setsampwidth(2)
        waveFile.setframerate(16000)
        waveFile.writeframes(b''.join(Recordframes))
        waveFile.close()
        try:
            stt = stream.finishStream()
        except Exception as e:
            print(e)
        if stt:
            print(stt)
            stt = pattern.sub(lambda m: replacements[re.escape(m.group(0))], stt)
            print(stt)
            try:
                actions.process_text(stt)
            except Exception as e:
                print("Error Processing Audio")
                print(e)
                #raise(e)
        else:
            print("No intelligible audio heard.")
        working = False

def loopTask():
    pass

def startThread():
    global runThread
    threadActive = True
    runThread = threading.Thread(target = threadScript)
    runThread.start()

def closeThread():
    global runThread
    threadActive = False
    runThread.join()

def threadScript():
    global threadActive
    threadActive = False
