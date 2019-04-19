import threading, time
import spacy
import englishActions.vbf as vbf

services = {}
plugin = {}
core = None
tts = None
runThread = None
threadActive = False
conversing = True
nlp = spacy.load("en_core_web_sm")
name = "Olivia"

def _register_(serviceList, pluginProperties):
    global services, plugin, core, tts
    services = serviceList
    plugin = pluginProperties
    core = services["core"][0]
    tts = services["tts"][0]
    services["userInterface"][0].addCommands({"converse": textConverse, "actions":{"converse": textConverse}})
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

def textConverse(arguments):
    """
INFO
    Starts up a conversation using the terminal

USAGE
    {0}
    """
    global name
    conversing = True
    while conversing:
        t = input("USER:> ")
        if t:
            process_text(t)
        else:
            break

def process_text(text):
    global tts, nlp
    vbf._open()
    
    doc = nlp(text)
    root = None

    #identify main roots, or active ideas
    
    for token in doc:
        if token.dep_ == u'ROOT':
            root = token
    roots = getConjuncts(root)

    for token in roots:
        processStatement(root, token)
    
    vbf._close()

def processStatement(root, head):
    global name
    #print(head.text)
    #print(head.tag_)
    #print(head.lemma_)
    nsubjects = getDepAndConj(head, u'nsubj')
    if nsubjects == ():
        nsubjects = getDepAndConj(root, u'nsubj')
    if nsubjects == ():
        nsubjects = ((name,),)
        #print("forced self")
    nsubjectnames = []
    for tup in nsubjects:
        nsubjectnames.append([])
        for item in tup:
            if isinstance(item, str):
                nsubjectnames[-1].append(item)
            else:
                if item.lemma_[0] != "-":
                    nsubjectnames[-1].append(item.lemma_)
                else:
                    nsubjectnames[-1].append(item.text)
    #print(nsubjectnames)
    text = vbf.vbz[root.lemma_](root, nsubjects)
    if text == None:
        text = "sorry, I didn't catch that."
    print("ASSIST:> " + text)
    tts.say(text)
    
    

def getDependency(head, dependency):
    matches = []
    for token in head.children:
        if token.dep_ == dependency:
            matches.append(token)
    return matches

def getConjuncts(primary):
    conjuncts = [primary]
    conjuncts += getDependency(primary, u'conj')
    return conjuncts

def getDepAndConj(head, dependency):
    '''Gets all dependencies and their conjuncts of a certain type'''
    primaries = getDependency(head, dependency)
    associations = []
    for primary in primaries:
        associations.append(tuple(getConjuncts(primary)))
    return tuple(associations)
    
