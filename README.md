# Open Assistant
A work-in-progress open source python assistant, which will, hopefully, turn out similar to alexa, siri, cortana, and others.

## Installation
Install the required packages (see below) then download `apples.py` and `open_assistant_en_us.apc` from here. Run apples.py and it will download every required plugin automatically. Everything 'should' automatically update as well.
Currently, a few smart home devices are supported, and must be installed separately. To install them, copy the specified file to the APPLES directory on your local machine and run the command specified to install necessary addons.
*yeelight `yeelight.apm` `pip install yeelight`


## Required Packages
The following is a list of libraries required for open assistant:
```
stanza - Language processing.
pywin32 - WINDOWS ONLY; Special weird windows fixes.
pyttsx3 - Text to speech.
pyaudio - Audio recording and playback.
numpy - Fast number processing.
deepspeech - Speech to text.
pytorch - Machine learning (required for stanza).
tensorflow - Machine learning (required for deepspeech).
```
First you will need to install PyTorch and Tensorflow. These libraries have different installation instructions depending on your system, such as whether you have an NVIDIA GPU or not. The instructions can be found at [https://pytorch.org/](https://pytorch.org/) and [https://www.tensorflow.org/install](https://www.tensorflow.org/install). Once this is done, the rest of the libraries are fairly easy.
If you have python version 3.__6__ or __older__ run the following command in a command line.
```
python -m pip install spacy pywin32 pyttsx3 pyaudio numpy tensorflow deepspeech -U
```
If you have python version 3.__7__ or 3.__8__ run the following command in the command line.
```
python -m pip install stanza pywin32 pyttsx3 numpy tensorflow deepspeech -U
```
You will then have to install pyaudio manually. First download it from [here](https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio), then install it with:
```
python -m pip install <downloaded file path>
```
Python 3.8 is the newest version at time of writing. Any later versions may or may not work.

## Usage
Press the trigger button or type `trigger` in the terminal to make the system listen for your speech. (CURRENTLY VERY BUGGY)
Alternatively, type `converse` to begin a text based "conversation" with the assistant.
Then just talk with it. Currently sentences with the following verbs will work. Verbs not listed here will probably not work, and could potentially cause a crash.
```
like, dislike, love, hate - as in 'i like minecraft' or 'do i hate mushrooms'
turn, toggle, switch - as in 'turn on the Lights' or 'switch off the fan'
set - as in 'set the lights to green' or 'set the lights to 50 percent'
```
If you find a bug with any of these verbs, please feel free to copy the full program output into an issue so I can figure out what grammar rules have not been accounted for. Alternatively feel free to add any verbs of your own, then submit a pull request for testing.
