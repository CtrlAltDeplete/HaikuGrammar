from constants import *
from random import randint, choice


class ExhaustedVocabulary(Exception):
    pass


class GrammarModel:
    """
    A class to hold all the necessary elements of a grammar and vocabulary for generating a Haiku.

    ...

    Attributes
    ----------
    vocabulary : dict
        A dictionary containing all the possible words used in the model, as well as their appropriate tags
    global_tags : tuple
        Tags that COULD be applied to every call to pick_word()
    current_tags : list
        Tags that SHOULD be applied to every call to pick_word() based on previously used words

    Methods
    -------
    add_word(word, syllables, tags)
        Adds a word to the vocabulary with the appropriate tags and syllables
    pick_word(min_syllables, max_syllables, tags)
        Chooses a word at "random" from the vocabulary that matches the tag and syllabic restrictions
    clear_tags()
        Resets all the current global tags (used in between clauses/phrases)
    create_participle_phrase(syllables, gerund=False)
        Creates a participle phrase with the given number of syllables (if gerund, it is a gerund phrase)
    create_noun_phrase(syllables)
        Creates a noun phrase with the given number of syllables
    create_prepositional_phrase(syllables)
        Creates a prepositional phrase with the given number of syllables
    create_clause(syllables)
        Creates a clause (subject and participle) with the given number of syllables
    """

    def __init__(self, vocabulary: dict=None):
        """
        Parameters
        ----------
        vocabulary : dict
            The words used for this grammar model, along with their tags and syllable count
        """

        self.vocabulary = vocabulary
        if vocabulary is None:
            self.vocabulary = {}
        self.global_tags = (FIRST, SECOND, THIRD, SINGULAR, PLURAL)
        self.current_tags = []

    def add_word(self, word: str, syllables: int, tags: list):
        """
        Adds a word with the syllable count and tags passed to the current vocabulary.

        Parameters
        ----------
        word : str
            The word to be added to the vocabulary (can also be a phrase in special cases)
        syllables : int
            How many syllables the word has
        tags : list
            The appropriate tags for the syllable
        """

        for key in self.vocabulary[syllables].keys():
            if set(key) == set(tags):
                if word not in self.vocabulary[syllables][key]:
                    self.vocabulary[syllables][key].append(word)
                return
        self.vocabulary[syllables][tags] = [word]

    def pick_word(self, min_syllables: int, max_syllables: int, tags: list) -> tuple:
        """
        Returns a word at random that matches the requirements passed.

        Parameters
        ----------
        min_syllables : int
            The minimum number of syllables needed
        max_syllables : int
            The maximum number of syllables needed
        tags : list
            The tags required for the word to be returned (can have additional tags)

        Returns
        -------
        tuple
            A tuple with the syllable count, applicable tags, and word

        Raises
        ------

        """

        options = []
        for syl_count in range(min_syllables, max_syllables + 1):
            for key in self.vocabulary[syl_count].keys():
                if set(tags).issubset(set(key)):
                    for word in self.vocabulary[syl_count][key]:
                        options.append((syl_count, key, word))
        if options:
            return choice(options)
        raise ExhaustedVocabulary(
            f"No words found between {min_syllables} and {max_syllables} syllables with tags {tags}."
        )

    def clear_tags(self):
        self.current_tags = []

    def create_verb_phrase(self, syllables, gerund=False):
        remaining_syllables = syllables
        tags = self.current_tags
        if gerund:
            tags.append(GERUND)
        else:
            tags.append(VERB)
        syl, tags, word = self.pick_word(1, remaining_syllables, tags)
        for tag in tags:
            if tag in self.global_tags:
                self.current_tags.append(tag)
        remaining_syllables -= syl
        options = [ADVERB, PREP_PHRASE]
        used = [((GERUND, VERB), word)]
        while remaining_syllables > 1:
            if remaining_syllables < 2 and PREP_PHRASE in options:
                options.remove(PREP_PHRASE)
            addition = choice(options)
            if addition is PREP_PHRASE:
                word, syl = create_prep_phrase(remaining_syllables)
                options.remove(PREP_PHRASE)
            elif addition is ADVERB:
                word, syl = pick_word(remaining_syllables, (ADVERB,))
                options.remove(ADVERB)
            if word:
                used.append((addition, word))
                remaining_syllables -= syl
            if not options and remaining_syllables > 0:
                print("Verb Phrase full iteration")
                return None, None
        while remaining_syllables == 1:
            syl, word_to_replace = choice(used)
            goal_syl = syl + 1
            counter = 0
            while syl != goal_syl and counter < 50:
                word, syl = pick_word(goal_syl, word_to_replace[0])
                counter += 1
            if counter != 50:
                remaining_syllables -= 1
                used.remove(word_to_replace)
                used.append((word, word_to_replace[0]))
        phrase = []
        for pos in choice(([ADVERB, VERB, PREP_PHRASE], [VERB, ADVERB, PREP_PHRASE], [VERB, PREP_PHRASE, ADVERB])):
            for x in used:
                if x[0] is pos:
                    phrase.append(x[1])
        return " ".join(phrase), syllables



vocabulary = None
pov = None


def create_haiku():
    return '\n'.join([create_five(), create_seven(), create_five()])


def create_five():
    line, syl = choice([lambda: create_noun_phrase(5), lambda: create_verb_phrase(5, True), lambda: create_prep_phrase(5)])()
    counter = 0
    while not line:
        if counter == 50:
            raise TimeoutError
        line, syl = choice([lambda: create_noun_phrase(5), lambda: create_verb_phrase(5, True), lambda: create_prep_phrase(5)])()
        counter += 1
    return line


def create_seven():
    line, syl = choice([create_verb_phrase, create_sentence])(7)
    counter = 0
    while not line:
        if counter == 50:
            raise TimeoutError
        line, syl = choice([create_verb_phrase, create_sentence])(7)
        counter += 1
    return line


def create_noun_phrase(syllables, adjust_pov=True):
    global pov

    remaining_syllables = syllables
    # Assign a global pov if there is none
    if pov is None and adjust_pov:
        pov = choice([THIRD_PERSON, FIRST_SECOND_PERSON])
    # Retrieve a noun to use
    word, syl = pick_word(remaining_syllables, (NOUN, pov))
    remaining_syllables -= syl
    # All the extra parts that can go into the noun phrase
    options = [DETERMINER, ADJECTIVE, PREP_PHRASE]
    # The parts and choices we have used so far
    used = [(NOUN, word)]
    # While there is space, round out the noun phrase
    while remaining_syllables != 0:
        if remaining_syllables < 2 and PREP_PHRASE in options:
            options.remove(PREP_PHRASE)
        addition = choice(options)
        if addition is not ADJECTIVE:
            options.remove(addition)
        # Retrieve our chosen word part
        if addition is PREP_PHRASE:
            word, syl = create_prep_phrase(randint(2, remaining_syllables))
        else:
            word, syl = pick_word(remaining_syllables, (addition))
        # If there was a match, append it to used
        if word:
            used.append((addition, word))
            remaining_syllables -= syl
        # If the phrase could not be completed
        if not options and remaining_syllables > 0:
            print("Noun Phrase full iteration.")
            return None, None
    # Organize our phrase appropriately for our chosen word parts
    phrase = []
    for pos in [DETERMINER, ADJECTIVE, NOUN, PREP_PHRASE]:
        for x in used:
            if x[0] is pos:
                phrase.append(x[1])
    return " ".join(phrase), syllables


def create_prep_phrase(syllables):
    remaining_syllables = syllables
    # Choose the preposition
    word, syl = pick_word(remaining_syllables - 1, (PREPOSITION))
    remaining_syllables -= syl
    # Then create a noun phrase for it, with a limit of 50 tries
    noun_phrase, syl = create_noun_phrase(remaining_syllables)
    counter = 0
    while not noun_phrase:
        if counter == 50:
            print("Prep Phrase full iteration.")
            return None, None
        noun_phrase, syl = create_noun_phrase(remaining_syllables, False)
        counter += 1
    return word + " " + noun_phrase, syllables


def create_verb_phrase(syllables, gerund=False):
    global pov

    remaining_syllables = syllables
    # Assign the global POV if there is none
    if pov is None:
        pov = choice([THIRD_PERSON, FIRST_SECOND_PERSON])
    # If a gerund, choose a gerund instead of a verb, and assign pov to FIRST_SECOND_PERSON
    if gerund:
        word, syl = pick_word(remaining_syllables, (GERUND))
        pov = FIRST_SECOND_PERSON
    else:
        word, syl = pick_word(remaining_syllables, (VERB, pov))
    remaining_syllables -= syl
    options = [ADVERB, ADVERB, PREP_PHRASE]
    used = [(VERB, word)]
    while remaining_syllables > 1:
        if remaining_syllables < 2 and PREP_PHRASE in options:
            options.remove(PREP_PHRASE)
        addition = choice(options)
        if addition is PREP_PHRASE:
            word, syl = create_prep_phrase(remaining_syllables)
            options.remove(PREP_PHRASE)
        elif addition is ADVERB:
            word, syl = pick_word(remaining_syllables, (ADVERB))
            options.remove(ADVERB)
        if word:
            used.append((addition, word))
            remaining_syllables -= syl
        if not options and remaining_syllables > 0:
            print("Verb Phrase full iteration")
            return None, None
    while remaining_syllables == 1:
        syl, word_to_replace = choice(used)
        goal_syl = syl + 1
        counter = 0
        while syl != goal_syl and counter < 50:
            word, syl = pick_word(goal_syl, word_to_replace[0])
            counter += 1
        if counter != 50:
            remaining_syllables -= 1
            used.remove(word_to_replace)
            used.append((word, word_to_replace[0]))
    phrase = []
    for pos in choice(([ADVERB, VERB, PREP_PHRASE], [VERB, ADVERB, PREP_PHRASE], [VERB, PREP_PHRASE, ADVERB])):
        for x in used:
            if x[0] is pos:
                phrase.append(x[1])
    return " ".join(phrase), syllables


def create_sentence(syllables):
    breakdown = randint(0, syllables)
    if breakdown != 0:
        noun_phrase, syl = create_noun_phrase(breakdown)
        counter = 0
        while not noun_phrase:
            if counter == 50:
                return None, None
            noun_phrase, syl = create_noun_phrase(breakdown)
            counter += 1
        if breakdown == 7:
            return noun_phrase, syllables
    if breakdown != 7:
        verb_phrase, syl = create_verb_phrase(syllables - breakdown)
        counter = 0
        while not verb_phrase:
            if counter == 50:
                return None, None
            verb_phrase, syl = create_verb_phrase(syllables - breakdown)
            counter += 1
        if breakdown == 0:
            return verb_phrase, syllables
    return noun_phrase + " " + verb_phrase, syllables


def pick_word(max_syllables, tags):
    options = []
    for i in range(1, max_syllables + 1):
        try:
            for word in vocabulary[tags][i]:
                options.append((word, i))
        except KeyError:
            pass
    if not options:
        print("No options for tags: {}".format(tags))
        return None, None
    else:
        return choice(options)


if __name__ == '__main__':
    vocabulary = {
        (NOUN, THIRD_PERSON): {
            1: ['life', 'love', 'world', 'day', 'heart', 'plant'],
            2: ['salmon', 'island', 'student', 'mother', 'water', 'music', 'squirrel'],
            3: ['chocolate', 'banana', 'piano', 'animal'],
            4: ['caterpillar', 'ant colony', 'vegetable'],
            5: [],
            6: [],
            7: []
        },
        (NOUN, FIRST_SECOND_PERSON): {
            1: ['days', 'hearts', 'plants', 'I', 'fish', 'deer', 'ants'],
            2: ['pumpkins', 'pictures', 'flowers'],
            3: ['elephants', 'adventures'],
            4: ['caterpillars', 'alligators', 'watermelons'],
            5: [],
            6: [],
            7: []
        },
        (DETERMINER): {
            1: ['the', 'a', 'an', 'this', 'that', 'these', 'those', 'its', 'thier', 'some', 'one', 'ten'],
            2: ['a few', 'many', 'twenty'],
            3: ['a little', 'a lot of'],
            4: [],
            5: [],
            6: [],
            7: []
        },
        (ADJECTIVE): {
            1: ['rare', 'sweet', 'new', 'soft', 'whole'],
            2: ['pristine', 'quiet', 'scenic', 'perfect', 'divine', 'simple'],
            3: ['oppressive', 'astounding', 'unsurpassed', 'romantic', 'singular', 'picturesque', 'glorious'],
            4: ['incredible', 'overwhelming', 'extravagant'],
            5: ['unbelievable'],
            6: [],
            7: []
        },
        (VERB, THIRD_PERSON): {
            1: ['bolts', 'craves', 'soars', 'lurks', 'flies', 'wails'],
            2: ['absorbs', 'cowers', 'glistens', 'rises', 'trudges'],
            3: ['advises', 'untangles'],
            4: [],
            5: [],
            6: [],
            7: []
        },
        (VERB, FIRST_SECOND_PERSON): {
            1: ['bust', 'climb', 'gleam', 'fight', 'stretch'],
            2: ['advance', 'attack', 'retreat', 'struggle', 'survey'],
            3: [],
            4: [],
            5: [],
            6: [],
            7: []
        },
        (ADVERB): {
            1: ['fast', 'high'],
            2: ['brightly', 'calmly', 'queerly', 'quickly', 'coolly', 'gently', 'roughly'],
            3: ['fervently', 'joyfully', 'intently', 'hungrily', 'solemnly', 'hastily'],
            4: ['furiously', 'ferociously', 'powerfully', 'quizzically'],
            5: ['mechanically', 'majestically'],
            6: [],
            7: []
        },
        (GERUND): {
            1: [],
            2: ['boosting', 'bursting', 'groping', 'fighting'],
            3: ['shriveling', 'scampering', 'absorbing', 'unveiling'],
            4: ['enveloping'],
            5: ['illuminating'],
            6: [],
            7: []
        },
        (PREPOSITION): {
            1: ['at', 'as'],
            2: ['aboard', 'about' 'above', 'across' 'after', 'against', 'along', 'amid', 'amidst', 'among', 'around',
                'atop', 'before', 'behind', 'below', 'beneath', 'beside', 'between', 'beyond', 'far from', 'ontop',
                'outside'],
            3: ['opposite', 'underneath'],
            4: [],
            5: [],
            6: [],
            7: []
        }
    }
    for i in range(10):
        print(create_haiku())
        print('=' * 20)
