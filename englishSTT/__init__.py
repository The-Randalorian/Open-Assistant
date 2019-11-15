import threading, time, deepspeech
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

    services["userInterface"][0].addCommands({"trigger": trigger})

    #core.addStart(trigger)
    #core.addStart(startThread)
    #core.addClose(closeThread)
    #core.addLoop(loopTask)

def trigger(*args):
    global services, plugin, core, audioRecorder, dsModel, audsrc, actions
    import wave, pyaudio
    #audioRecorder = services["audioRecorder"][0]
    #audsrc = audioRecorder.AudioSource()
    WAVE_OUTPUT_FILENAME = "englishSTT\lastRecord.wav"
    print("loading stream")
    stream = dsModel.setupStream()
    print("model loaded")
    audbuf = audsrc.getBuffer()
    print(audbuf)
    print("ready to record")
    Recordframes = []
    cnt = 0
    for i in range(0, int(16000 / 256 * 15)):
        print(cnt)
        cnt+=1
        sample = next(audbuf)
        print(sample)
        Recordframes.append(sample)
        dat = np.frombuffer(sample, np.int16)
        dsModel.feedAudioContent(stream, dat)
        #print(dat)
    audbuf.stopRecording()
    #next(audsrc)
    print("done 1")
    waveFile = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
    waveFile.setnchannels(1)
    waveFile.setsampwidth(2)
    waveFile.setframerate(16000)
    waveFile.writeframes(b''.join(Recordframes))
    waveFile.close()
    try:
        stt = dsModel.finishStream(stream)
        print(stt)
    except Exception as e:
        print(e)
    print("done 2")
    print(stt)
    print(type(stt))
    print("done 3")
    print("processing")
    if stt:
        actions.process_text(stt)

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
    
