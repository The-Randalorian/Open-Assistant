import math

chunkNames = [ #if anyone wants to allow counting beyod ~999 Centillion, feel free to add suffixes here
    "",
    "thousand",
    "million",
    "billion",
    "trillion",
    "quadrillion",
    "quintillion",
    "sextillion",
    "septillion",
    "octillion",
    "nonillion",
    "decillion",
    "undecillion",
    "duodecillion",
    "tredecillion",
    "quattuordecillion",
    "quindecillion",
    "sexdicillion",
    "septendecillion",
    "octodecillion",
    "novemdecillion",
    "vigintillion",
    "unvigintillion",
    "duovigintillion",
    "tresvigintillion",
    "quatvigintillion",
    "quinvigintillion",
    "sesvigintillion",
    "septemvigintillion",
    "octovigintillion",
    "novemvigintillion",
    "trigintillion",
    "untrigintillion",
    "duotrigintillion",
    "trestrigintillion",
    "quattrigintillion",
    "quintrigintillion",
    "sestrigintillion",
    "septentrigintillion",
    "octotrigintillion",
    "noventrigintillion",
    "quadragintillion",
    "unquadragintillion",
    "duoquadragintillion",
    "tresquadragintillion",
    "quatquadragintillion",
    "quinquadragintillion",
    "sesquadragintillion",
    "septemquadragintillion",
    "octoquadragintillion",
    "novemquadragintillion",
    "quinquagintillion",
    "unquinquagintillion",
    "duoquinquagintillion",
    "tresquinquagintillion",
    "quatquinquagintillion",
    "quinquinquagintillion",
    "sesquinquagintillion",
    "septemquinquagintillion",
    "octoquinquagintillion",
    "novemquinquagintillion",
    "sexagintillion",
    "unsexagintillion",
    "duosexagintillion",
    "tressexagintillion",
    "quatsexagintillion",
    "quinsexagintillion",
    "sessexagintillion",
    "septemsexagintillion",
    "octosexagintillion",
    "novemsexagintillion",
    "septuagintillion",
    "unseptuagintillion",
    "duoseptuagintillion",
    "tresseptuagintillion",
    "quatseptuagintillion",
    "quinseptuagintillion",
    "sesseptuagintillion",
    "septemseptuagintillion",
    "octoseptuagintillion",
    "novemseptuagintillion",
    "octogintillion",
    "unoctogintillion",
    "duooctogintillion",
    "tresoctogintillion",
    "quatoctogintillion",
    "quinoctogintillion",
    "sesoctogintillion",
    "septemoctogintillion",
    "octooctogintillion",
    "novemoctogintillion",
    "nonagintillion",
    "unnonagintillion",
    "duononagintillion",
    "tresnonagintillion",
    "quatnonagintillion",
    "quinnonagintillion",
    "sesnonagintillion",
    "septemnonagintillion",
    "octononagintillion",
    "novemnonagintillion",
    "centillion"
    ]

placeNames = [
    "",
    "^$",
    "hundred"
    ]

digitNames = [
    "zero",
    "one",
    "two",
    "three",
    "four",
    "five",
    "six",
    "seven",
    "eight",
    "nine"
    ]

caratNames = { # special digit names for multiple digit places
    10: "ten",
    11: "eleven",
    12: "twelve",
    13: "thirteen",
    14: "fourteen",
    15: "fifteen",
    16: "sixteen",
    17: "seventeen",
    18: "eighteen",
    19: "nineteen"
    }

dollarNames = { # special digit value names for when a name changes in a certain place value
    20: "twenty",
    30: "thirty",
    40: "fourty",
    50: "fifty",
    60: "sixty",
    70: "seventy",
    80: "eighty",
    90: "ninety"
    }

class NumberTooLargeError(Exception):
    def __init__(self, number, *args, **kwargs):
        self.number = number
        Exception.__init__(self, "The number provided was too awesome to be handled. Please add additional chunk names to account for numbers larger than ~999 " + chunkNames[-1] + ".", *args,**kwargs)

def nums2Wrds(string, zeroValid = True):
    string = string.replace(",", "")
    words = ""

    placesPerChunk = len(placeNames)
    digitsPerPlace = len(digitNames)
    digitsPerChunk = digitsPerPlace ** placesPerChunk

    parts = string.split(".")
    integer = parts[0]
    if len(parts) > 1:
        decimal = parts[1]
    else:
        decimal = ""
    if len(integer) > placesPerChunk * len(chunkNames):
        raise NumberTooLargeError(string)
    if len(integer) > 0:
        integer = int(integer)
        intChunks = []
        while integer > 0:
            intChunks.append(integer % digitsPerChunk)
            integer = int(integer // digitsPerChunk)
        for chunkIndex in range(len(intChunks) - 1, -1, -1):
            chunk = intChunks[chunkIndex]
            if chunk == 0:
                continue
            skipChunk = False
            for placeIndex in range(placesPerChunk - 1, -1, -1):
                p = placeNames[placeIndex]
                pv = int(digitsPerPlace ** (placeIndex))
                dig = int(chunk // pv)
                if dig != 0:
                    if len(p) <= 0 or (p[0] != "^" and p[0] != "$"):
                        words += digitNames[dig] + " "
                        if len(p) > 0:
                            words += p + " "
                    while len(p) > 0 and (p[0] == "^" or p[0] == "$"):
                        if p[0] == "^":
                            p = p[1:]
                            if chunk in caratNames.keys():
                                words += caratNames[chunk] + " "
                                skipChunk = True
                                break
                            else:
                                continue
                        elif p[0] == "$":
                            p = p[1:]
                            if dig * pv in dollarNames.keys():
                                words += dollarNames[dig * pv] + " "
                                break
                            else:
                                continue
                if skipChunk:
                    break
                chunk = chunk % (digitsPerPlace ** placeIndex)
            words += chunkNames[chunkIndex] + " "
        words = words.rstrip() + " "
    if len(decimal) != 0:
        words += "point "
        for word in [digitNames[int(dec)] + " " for dec in decimal]:
            words += word
    words = words.rstrip()
    if zeroValid and len(words) <= 0:
        words = digitNames[0]
    return words.rstrip()

def frac2Wrds(string):
    parts = string.split("/")
    if len(parts) == 2:
        words = nums2Wrds(parts[0]) + " " + nums2Wrds(parts[1])
        return words
            
def time2Wrds(string):
    parts = string.split(":")
    if len(parts) == 2:
        words = nums2Wrds(parts[0], zeroValid = False) + " "
        if len(parts[1]) < 2 or int(parts[1]) < 10:
            words += "o "
        if int(parts[1]) == 0:
            words += "clock"
        else:
            words += nums2Wrds(parts[1], zeroValid = False)
        return words

crdnlOrdnlPairs = {
    None: "th",
    "one": "first",
    "two": "second",
    "three": "third",
    "five": "fifth",
    "eight": "eighth",
    "nine": "ninth",
    "twenty": "twentieth",
    "thirty": "thirtieth",
    "fourty": "fourtieth",
    "fifty": "fiftieth",
    "sixty": "sixtieth",
    "seventy": "seventieth",
    "eighty": "eightieth",
    "ninety": "ninetieth"
    }
    

def crdnl2Ordnl(string):
    string = string.rstrip()
    words = string.split()
    words[-1] = crdnlOrdnlPairs.get(words[-1], words[-1] + crdnlOrdnlPairs[None])
    string = " ".join(words)
    return string
    
    
if __name__ == "__main__": #kill at 4
    #print( nums2Wrds("123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456") )
    print( nums2Wrds("9" * 306 + "." + "9" * 1017) )
    print( "-"*64 )
    n = nums2Wrds("0")
    print( n )
    print( crdnl2Ordnl(n) )
    n = nums2Wrds("1")
    print( n )
    print( crdnl2Ordnl(n) )
    n = nums2Wrds("2")
    print( n )
    print( crdnl2Ordnl(n) )
    n = nums2Wrds("123456")
    print( n )
    print( crdnl2Ordnl(n) )
    print( "-"*64 )
    print( time2Wrds("3:00") )
    print( time2Wrds("7:15") )
    print( time2Wrds("1:40") )
    print( time2Wrds("12:16") )
