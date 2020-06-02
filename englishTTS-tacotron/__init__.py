import threading, time, pathlib, pyaudio, wave

services = {}
plugin = {}
core = None
runThread = None
threadActive = False

moduleRoot = pathlib.PurePath(__file__[:-11])
modelsPath = moduleRoot / 'models'
modelName = 'tacotron-20180906'
modelPath = modelsPath / modelName / 'model.ckpt'

try:
    from .keithitoTacotron.synthesizer import Synthesizer
except ModuleNotFoundError:
    from keithitoTacotron.synthesizer import Synthesizer

synthesizer = Synthesizer()

def _register_(serviceList, pluginProperties):
    global services, plugin, core
    services = serviceList
    plugin = pluginProperties
    core = services["core"][0]
    synthesizer.load(str(modelPath))
    time.sleep(3)
    say("Scientists at the CERN laboratory say they have discovered a new particle.")
    #core.addStart(startThread)
    #core.addClose(closeThread)
    #core.addLoop(loopTask)

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

#===================================================================
#           Standard TTS functions
#===================================================================

def setProperty(prop, value):
    global q
    q.put([1, prop, value])

def setVolume(value):
    setProperty("volume", value)

def setRate(value):
    setProperty("rate", value)

def setVoice(value):
    setProperty("volume", value)

def say(text, notification="Open Assistant"):
    p = pyaudio.PyAudio()

    # open stream (2)
    stream = p.open(format=pyaudio.get_format_from_width(2),
                channels=1,
                rate=20000,
                output=True)
    data = synthesizer.synthesize(text)
    stream.write(data)
    stream.stop_stream()
    stream.close()

if __name__ == "__main__":
    synthesizer.load(str(modelPath))
    time.sleep(3)
    say("Scientists at the CERN laboratory say they have discovered a new particle.")
