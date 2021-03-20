from numbers import Number

chunk_names = [ #if anyone wants to allow counting beyod ~999 Centillion, feel free to add suffixes here
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

place_names = [
    "",
    "^$",
    "hundred"
    ]

digit_names = [
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

multi_digit_names = {  # special digit names for multiple digit places, represented by carat
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

place_value_names = {  # special digit value names for when a name changes in a certain place value
    20: "twenty",
    30: "thirty",
    40: "fourty",
    50: "fifty",
    60: "sixty",
    70: "seventy",
    80: "eighty",
    90: "ninety"
    }

cardinal_ordinal_pairs = {
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


class NumberTooLargeError(Exception):
    def __init__(self, number, *args, **kwargs):
        self.number = number
        Exception.__init__(self, f"The number provided was too awesome to be handled. Please add additional chunk names"
                                 " to account for numbers larger than ~999 {chunk_names[-1]}.", *args, **kwargs)


def number_to_word(number: (str, Number), zero_valid: bool = True):
    number_string = str(number)
    number_string = number_string.replace(",", "")
    words = ""

    places_per_chunk = len(place_names)
    digits_per_place = len(digit_names)
    digits_per_chunk = digits_per_place ** places_per_chunk

    parts = number_string.split(".")
    integer = parts[0]
    if len(parts) > 1:
        decimal = parts[1]
    else:
        decimal = ""
    if len(integer) > places_per_chunk * len(chunk_names):
        raise NumberTooLargeError(number_string)
    if len(integer) > 0:
        integer = int(integer)
        int_chunks = []
        while integer > 0:
            int_chunks.append(integer % digits_per_chunk)
            integer = int(integer // digits_per_chunk)
        for chunkIndex in range(len(int_chunks) - 1, -1, -1):
            chunk = int_chunks[chunkIndex]
            if chunk == 0:
                continue
            skip_chunk = False
            for place_index in range(places_per_chunk - 1, -1, -1):
                p = place_names[place_index]
                pv = int(digits_per_place ** place_index)
                dig = int(chunk // pv)
                if dig != 0:
                    if len(p) <= 0 or (p[0] != "^" and p[0] != "$"):
                        words += digit_names[dig] + " "
                        if len(p) > 0:
                            words += p + " "
                    while len(p) > 0 and (p[0] == "^" or p[0] == "$"):
                        if p[0] == "^":
                            p = p[1:]
                            if chunk in multi_digit_names.keys():
                                words += multi_digit_names[chunk] + " "
                                skip_chunk = True
                                break
                            else:
                                continue
                        elif p[0] == "$":
                            p = p[1:]
                            if dig * pv in place_value_names.keys():
                                words += place_value_names[dig * pv] + " "
                                break
                            else:
                                continue
                if skip_chunk:
                    break
                chunk = chunk % (digits_per_place ** place_index)
            words += chunk_names[chunkIndex] + " "
        words = words.rstrip() + " "
    if len(decimal) != 0:
        words += "point "
        for word in [digit_names[int(dec)] + " " for dec in decimal]:
            words += word
    words = words.rstrip()
    if zero_valid and len(words) <= 0:
        words = digit_names[0]
    return words.rstrip()


def fraction_to_words(string):
    parts = string.split("/")
    if len(parts) == 2:
        words = number_to_word(parts[0]) + " " + number_to_word(parts[1])
        return words


def time_to_words(string):
    parts = string.split(":")
    if len(parts) == 2:
        words = number_to_word(parts[0], zero_valid=False) + " "
        if len(parts[1]) < 2 or int(parts[1]) < 10:
            words += "o "
        if int(parts[1]) == 0:
            words += "clock"
        else:
            words += number_to_word(parts[1], zero_valid=False)
        return words


def cardinal_to_ordinal(cardinal_string: str):
    """
    Convert a string of words from a cardinal number system to an ordinal system.  For example, "sixty five" will become
    "sixty fifth".
    """
    cardinal_string = cardinal_string.rstrip()
    words = cardinal_string.split()
    words[-1] = cardinal_ordinal_pairs.get(words[-1], words[-1] + cardinal_ordinal_pairs[None])
    ordinal_string = " ".join(words)
    return ordinal_string
    
    
if __name__ == "__main__":  # kill at 4
    '''
    print( number_to_word("12345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012"
                          "34567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234"
                          "56789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456"
                          "789012345678901234567890123456"))
    # '''
    print(number_to_word("9" * 306 + "." + "9" * 1017))
    print("-"*64)
    n = number_to_word("0")
    print(n)
    print(cardinal_to_ordinal(n))
    n = number_to_word("1")
    print(n)
    print(cardinal_to_ordinal(n))
    n = number_to_word("2")
    print(n)
    print(cardinal_to_ordinal(n))
    n = number_to_word("123456")
    print(n)
    print(cardinal_to_ordinal(n))
    print("-"*64)
    print(time_to_words("3:00"))
    print(time_to_words("7:15"))
    print(time_to_words("1:40"))
    print(time_to_words("12:16"))
