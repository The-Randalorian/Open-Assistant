import json, linecache, os
from itertools import (takewhile,repeat)


root = __file__[:-11]
thesaurus_file = root + "zaibacu-thesaurus" + os.sep + "en_thesaurus.jsonl"


def count_lines(filename):
    with open(filename, 'rb') as f:
        bufgen = takewhile(lambda x: x, (f.raw.read(1024*1024) for _ in repeat(None)))
        return sum(buf.count(b'\n') for buf in bufgen )


linecount = count_lines(thesaurus_file)


def find(word, lo=0, hi=linecount, count=0, clear_when_done=True):
    word = word.lower()
    test_index = (hi - lo) // 2 + lo
    #print(test_index, count + 1)
    line = json.loads(linecache.getline(thesaurus_file, test_index))
    search = line["word"].lower()
    if search == word:
        found = (test_index, line)
    else:
        if lo + 1 == hi:
            return (None, {"word": word})
        elif search > word:
            found = find(word, lo, test_index, count + 1)
        elif search < word:
            found = find(word, test_index, hi, count + 1)
    if count <= 0:
        found = group_words(*found)
        if clear_when_done:
            linecache.clearcache()
    return found

def find_several(words, clear_when_done=True):
    groups = []
    for word in words:
        groups.append(find(word, clear_when_done=False))
    if clear_when_done:
        linecache.clearcache()

def group_words(line_number, line):
    word = line["word"]
    group = {
        "word": word,
        "pos": {}
    }
    if line_number is None:
        return group
    test_index = line_number - int(line["key"].split("_")[1]) + 1
    test_line = json.loads(linecache.getline(thesaurus_file, test_index))
    while test_line["word"] == line["word"]:
        pos = group["pos"].setdefault(test_line["pos"], set())
        pos.update(test_line["synonyms"])
        test_index = test_index + 1
        test_line = json.loads(linecache.getline(thesaurus_file, test_index))
    return group