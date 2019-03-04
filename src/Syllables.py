import re


# Read in all our dipthongs, digraphs, prefixes, and suffixes from our rules.txt file.
with open("rules.txt") as f:
    rules = f.read().split()
    diphthongs = rules[0].split(',')
    digraphs = rules[1].split(',')
    onePrefixes = rules[2].split(',')
    twoPrefixes = rules[3].split(',')
    oneSuffixes = rules[4].split(',')
    twoSuffixes = rules[5].split(',')
consonants = "bcdfghjklmnpqrstvwxyz"
vowels = "aeiouy"


# This function simply returns the number of vowels in a string.
def countVowels(part):
    count = 0
    for ch in part:
        if ch in vowels:
            count += 1
    return count


# This function attempts to count the number of syllables in a part.
def syllablesInPart(part):
    # Start with a base score of how many vowels are in the part,
    count = countVowels(part)
    # Then subtract one for a silent 'e',
    if part[-1] == 'e':
        part = part[:-1]
        if len(part) > 1 and part[-2:] == 'et':
            pass
        else:
            count -= 1
    # And subtract one for each dipthong.
    for dip in diphthongs:
        if dip in part:
            count -= countVowels(dip) - 1
    # Return the count, with a minimum of 0.
    return max(0, count)


# This functions attempts to count the number of syllables in a word, and is the function most called.
def syllablesInWord(word):
    # Strip all nun alphabetic characters from the word.
    word = word.lower()
    regex = re.compile('[^a-zA-Z]')
    word = regex.sub('', word)
    # If there is no longer a word, return 0.
    if len(word) == 0:
        return 0
    if word in ['dr', 'mr', 'mrs', 'tv', 'ok']:
        return 2
    if word in ['cia', 'fbi', 'area']:
        return 3
    # Initialize parts, counts, and split.
    parts = []
    count = 0
    # Split is used to decide when to stop iterating through our previously loaded prefixes and suffixes.
    split = True
    # If the word ends in s, remove the s.
    if word[-1] == 's':
        word = word[:-1]
        # Some special cases where we need to add a syllable.
        if len(word) >= 4 and word[-4:] in ['tche', 'ysse', 'esse', 'asse', 'ishe', 'ashe', 'ange', 'orce', 'ince', 'ence', 'eeze', 'boxe'] or word[-3:] in ['ace', 'ase']:
            count += 1
    # If the word ends in 'le', add 1 to the count and remove the 'le'.
    if len(word) > 3 and word[-2:] == 'le' and word[-3] in consonants:
        count += 1
        word = word[:-3]
    # There are a few exceptions where the ending should not add a syllable.
    if len(word) >= 5 and word[-4:] in ['shed', 'ried', 'fied', 'lied', 'ssed', 'lked', 'lled', 'wled', 'bled', 'nked', 'cked', 'rmed', 'rked', 'died', 'nged', 'ssed', 'ghed', 'sked', 'gged', 'cied', 'reed', 'ched', 'ised', 'thed', 'amed']:
        count -= 1
    if len(word) >= 5 and word[-4] in 'aeiouy' and word[-3] in 'rsncglykv' and word[-2] in 'aeiouy' and word[-1] == 'd':
        count -= 1
    # This loop will run until it goes through once without separating the word.
    while split:
        split = False
        # Iterate through all the double prefixes,
        for twoPre in twoPrefixes:
            if len(twoPre) < len(word):
                # If the word starts with the prefix, remove it from the word and add 2 to the count.
                if word[:len(twoPre)] == twoPre:
                    word = word[len(twoPre):]
                    count += 2
                    split = True
        # Iterate through all the single prefixes,
        for onePre in onePrefixes:
            if len(onePre) < len(word):
                # If the word starts with the prefix, remove it from the word and add 1 to the count.
                if word[:len(onePre)] == onePre:
                    word = word[len(onePre):]
                    count += 1
                    split = True
        # Iterate through all the double suffixes,
        for twoSuf in twoSuffixes:
            if len(twoSuf) <= len(word):
                # If the word ends with the prefix, remove it from the word and add 2 to the count.
                if word[-len(twoSuf):] == twoSuf:
                    word = word[:-len(twoSuf)]
                    count += 2
                    split = True
        # Iterate through all the single suffixes,
        for suf in oneSuffixes:
            if len(suf) < len(word):
                # If the word ends with the prefix, remove it from the word and add 1 to the count.
                if word[-len(suf):] == suf:
                    word = word[:-len(suf)]
                    count += 1
                    split = True
    # Calculate whether the word is odd and the middle position of the word.
    odd = len(word) % 2 == 1
    mid = len(word) // 2
    # If it is even,
    if not odd and len(word) >= 4:
        # And the middle of the word is vowel + consonant + consonant + vowel, excluding digraphs,
        if countVowels(word[mid - 1:mid + 1]) == 0 and word[mid - 1:mid + 1] not in digraphs and countVowels(word[mid - 2:mid + 2]) == 2:
            parts.append(word[:mid])
            parts.append(word[mid:])
            word = ''
        elif countVowels(word[mid - 1:mid + 2]) == 2 and word[mid] in consonants and word[mid - 1] != 'e':
            parts.append(word[:mid])
            parts.append(word[mid:])
            word = ''
    elif odd and len(word) >= 5:
        if countVowels(word[mid - 1:mid + 1]) == 0 and word[mid - 1:mid + 1] not in digraphs and countVowels(word[mid - 2:mid + 2]) == 2:
            parts.append(word[:mid])
            parts.append(word[mid:])
            word = ''
        elif countVowels(word[mid:mid + 3]) == 2 and word[mid + 1] in consonants:
            parts.append(word[:mid + 1])
            parts.append(word[mid + 1:])
            word = ''
    if word != '':
        parts.append(word)
    for part in parts:
        count += syllablesInPart(part)
    return max(count, 1)


def syllablesInString(text):
    count = 0
    for word in text.split():
        count += syllablesInWord(word)
    return count


if __name__ == '__main__':
    for word in "loud proud".split():
        print(word, syllablesInWord(word))
