# Open Assistant
A work-in-progress open source python assistant, which will, hopefully, turn out similar to alexa, siri, cortana, and others.

# Tutorial
To start, type `converse` to begin talking with the assistant.
Then just talk with it. Currently sentences with the following verbs will work. ANY SENTENCE WITH A DIFFERENT VERB WILL CAUSE THE PROGRAM TO CRASH.
```
is - as in 'my name is bob' or 'what is my name'
like - as in 'i like minecraft' or 'what do i like'
need - as in 'i need food' or 'what do i need'
want - as in 'i want a car' or 'what do i want'
```
If you find a bug with any of these verbs, please feel free to copy the full program output into an issue so I can figure out what grammar rules I failed to account for. Alternatively feel free to add any verbs of your own, then submit a pull request for testing.

# Required Packages
The following is a list of libraries required for open assistant:
```
spacy
pythoncom
pyttsx3
pyaudio
numpy
jsons
```
Also you will need python 3.__6__. Currently, pyaudio and some other dependencies have issues with 3.7. This version has been developed with python 3.6.8 for windows amd64, but other versions of python 3 prior to 3.7 __should__ work (no guarantees though).
