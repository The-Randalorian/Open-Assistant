import pyaudio
import numpy

FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
CHUNK = 320
DEVICE = 3
 
audio = pyaudio.PyAudio()
print(audio.get_device_info_by_index(DEVICE))
 
# start Recording
stream = audio.open(format=FORMAT, channels=CHANNELS,
                rate=RATE, input=True,
                frames_per_buffer=CHUNK,
                input_device_index=DEVICE)
print("recording...")
frames = []
 
#for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
#    data = stream.read(CHUNK)
#    frames.append(data)
import matplotlib.pyplot as plt
while True:
    data = numpy.frombuffer(stream.read(CHUNK), dtype=numpy.uint16)
    fft = numpy.fft.rfft(data)
    #fft = numpy.absolute(fft)
    fft = numpy.clip(fft, 0, 10000000)
    fft[0] = 10000000
    freq = numpy.fft.rfftfreq(data.size, d=1.0/RATE)
    plt.plot(freq, fft.real, freq, numpy.zeros(freq.size))
    plt.draw()
    plt.pause(0.01)
    plt.clf()
    #print(numpy.fft.fft(data))
print("finished recording")
print(frames[:2048])
 
 
# stop Recording
stream.stop_stream()
stream.close()
audio.terminate()
