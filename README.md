# Open Assistant
A work-in-progress open source python assistant, which will, hopefully, turn out similar to alexa, siri, cortana, and others.

# Installation
Install the required packages (see below) then download `apples.py` and `open_assistant_en_us.apc` from here. Run apples.py and it will download every required package automatically. Everything 'should' automatically update as well.
Currently, a few smart home devices are supported, and must be installed separately. To install them, copy the specified file to the root directory on your local machine. and run the command specified to install necessary addons.
*yeelight `yeelight.apm` `pip install yeelight`
*


# Required Packages
The following is a list of libraries required for open assistant:
```
spacy
pywin32
pyttsx3
pyaudio
numpy
jsons
tensorflow
deepspeech
yeelight
```
These can be installed by opening up the command line and running:
```
python -m pip install spacy pywin32 pyttsx3 pyaudio numpy jsons tensorflow deepspeech yeelight
```
Also you will need python 3.__6__. Currently, pyaudio and some other dependencies have issues with 3.7. This version has been developed with python 3.6.8 for windows amd64, but other versions of python 3 prior to 3.7 __should__ work (no guarantees though).

# Usage
Press the trigger button or type `trigger` in the terminal to make the system listen for your speech. (CURRENTLY VERY BUGGY)
Alternatively, type `converse` to begin a text based "conversation" with the assistant.
Then just talk with it. Currently sentences with the following verbs will work. Verbs not listed here will probably not work, and could potentially cause a crash.
```
is - as in 'my name is bob' or 'what is my name'
like - as in 'i like minecraft' or 'what do i like'
need - as in 'i need food' or 'what do i need'
want - as in 'i want a car' or 'what do i want'
```
If you find a bug with any of these verbs, please feel free to copy the full program output into an issue so I can figure out what grammar rules have not been accounted for. Alternatively feel free to add any verbs of your own, then submit a pull request for testing.
