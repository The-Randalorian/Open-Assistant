import threading, time, deepspeech, audioop
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

def _register_(serviceList, pluginProperties):
    global services, plugin, core, audioRecorder, dsModel, stream, audsrc, actions
    services = serviceList
    plugin = pluginProperties
    core = services["core"][0]
    audioRecorder = services["audioRecorder"][0]
    actions = services["actions"][0]

    audsrc = audioRecorder.AudioSource()
    
    dsModel = deepspeech.Model(
        r"englishSTT\models\output_graph.pbmm",
        26,
        9,
        r"englishSTT\models\alphabet.txt",
        500)
    dsModel.enableDecoderWithLM(
        r"englishSTT\models\alphabet.txt",
        r"englishSTT\models\lm.binary",
        r"englishSTT\models\trie",
        0.75,
        1.85)

    # DeepSpeech locks up after the first few frames, this clears that up
    stream = dsModel.setupStream()
    dsModel.feedAudioContent(stream, [0, 0, 0, 0, 65535, 65535, 65535, 65535] * 8192)
    dsModel.finishStream(stream)

    services["userInterface"][0].addCommands({"trigger": trigger})

    #core.addStart(trigger)
    #core.addStart(startThread)
    #core.addClose(closeThread)
    #core.addLoop(loopTask)

def trigger(*args):
    global working
    if not working:
        working = True
        global services, plugin, core, audioRecorder, dsModel, audsrc, actions
        import wave, pyaudio
        #audioRecorder = services["audioRecorder"][0]
        #audsrc = audioRecorder.AudioSource()
        WAVE_OUTPUT_FILENAME = "englishSTT\lastRecord.wav"
        stream = dsModel.setupStream()
        audbuf = audsrc.getBuffer()
        Recordframes = []
        cnt = 0
        vc = -1
        #for i in range(0, int(16000 / 256 * 10)):
        while True:
            cnt+=1
            sample = next(audbuf)
            vol = audioop.rms(sample,2)
            #print(vol)
            if vc < 0:
                if vol >= 400:
                    vc = 0
            else:
                if vol < 20:
                    vc += 1
                else:
                    vc = 0
            if vc > 32:
                break
            #print("#"*vol, end="")
            #print(sample)
            Recordframes.append(sample)
            dat = np.frombuffer(sample, np.int16)
            dsModel.feedAudioContent(stream, dat)
            #print(dat)
        print()
        audbuf.stopRecording()
        #next(audsrc)
        waveFile = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
        waveFile.setnchannels(1)
        waveFile.setsampwidth(2)
        waveFile.setframerate(16000)
        waveFile.writeframes(b''.join(Recordframes))
        waveFile.close()
        try:
            stt = dsModel.finishStream(stream)
        except Exception as e:
            print(e)
        if stt:
            print(stt)
            try:
                actions.process_text(stt)
            except:
                print("Error Processing Audio")
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
    
