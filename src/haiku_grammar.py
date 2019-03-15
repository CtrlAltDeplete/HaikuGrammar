from src.constants import *
from src.Syllables import syllablesInWord
from random import randint, choice
from pickle import load


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
    current_global_tags : list
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
        self.global_tags = (PAST, PRESENT, PERFECT, PROGRESSIVE, CONDITIONAL, SUBJUNCTIVE, PASSIVE, ACTIVE,
                            FIRST_PERSON, SECOND_PERSON, THIRD_PERSON, SINGULAR, PLURAL)
        self.current_global_tags = []

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
            A tuple with the syllable count and word

        Raises
        ------
        ExhaustedVocabulary
            If there are no words in the vocabulary matching the criteria, this error is raised
        """

        tags.extend(self.current_global_tags)

        options = []
        for syl_count in range(min_syllables, max_syllables + 1):
            for key in self.vocabulary[syl_count].keys():
                if set(tags).issubset(set(key)) or set(key).issubset(set(tags)):
                    for word in self.vocabulary[syl_count][key]:
                        options.append((syl_count, key, word))
        if options:
            c = choice(options)
            for tag in c[1]:
                if tag in self.global_tags and tag not in self.current_global_tags:
                    self.current_global_tags.append(tag)
            return c[0], c[2]
        raise ExhaustedVocabulary(
            f"No words found between {min_syllables} and {max_syllables} syllables with tags {tags}."
        )

    def clear_tags(self):
        self.current_global_tags = []

    def create_verb_phrase(self, min_syllables, max_syllables, gram_function=None):
        remaining_syllables = max_syllables
        if gram_function is None:
            gram_function = choice((BE, LINKING, INTRANSITIVE, TRANSITIVE))

        if gram_function is BE:
            options = [PREP_PHRASE]
        elif gram_function is LINKING:
            options = [SUBJECT_COMPLIMENT]
        elif gram_function is INTRANSITIVE:
            options = [ADVERB, PREP_PHRASE]
        elif gram_function is TRANSITIVE:
            options = [DIRECT_OBJECT, ADVERB, PREP_PHRASE]
        elif gram_function is GERUND:
            options = [DIRECT_OBJECT]
        elif gram_function is PARTICIPLE:
            options = []

        syllables_used, word = self.pick_word(1, max_syllables, [gram_function])

    def create_be_verb_phrase(self, min_syllables, max_syllables):
        remaining_syllables = max_syllables
        options = [PREP_PHRASE]


    def create_noun_phrase(self, syllables, require_determiner=False):
        remaining_syllables = syllables
        # Retrieve a noun to use
        syllables_used, word = self.pick_word(1, remaining_syllables, [NOUN])
        remaining_syllables -= syllables_used
        # All the extra parts that can go into the noun phrase
        options = [DETERMINER, ADJECTIVE, PREP_PHRASE]
        # The parts and choices we have used so far
        used = [(NOUN, word)]
        # While there is space, round out the noun phrase
        while remaining_syllables != 0:
            if remaining_syllables <= 3 and PREP_PHRASE in options:
                options.remove(PREP_PHRASE)
            if require_determiner and DETERMINER in options:
                addition = DETERMINER
            else:
                addition = choice(options)
            if addition is not ADJECTIVE:
                options.remove(addition)
            # Retrieve our chosen word part
            if addition is PREP_PHRASE:
                syllables_used, word = self.create_prep_phrase(randint(3, remaining_syllables))
            else:
                syllables_used, word = self.pick_word(1, remaining_syllables, [addition])
            # If there was a match, append it to used
            if word:
                used.append((addition, word))
                remaining_syllables -= syllables_used
            # If the phrase could not be completed
            if not options and remaining_syllables > 0:
                raise ExhaustedVocabulary(
                    "In the creation of a NOUN PHRASE, the GRAMMAR ran out of options."
                )
        # Organize our phrase appropriately for our chosen word parts
        phrase = []
        for pos in [DETERMINER, ADJECTIVE, NOUN, PREP_PHRASE]:
            for x in used:
                if x[0] is pos:
                    phrase.append(x[1])
        return syllables, " ".join(phrase)

    def create_prep_phrase(self, syllables):
        remaining_syllables = syllables
        # Choose the preposition
        syllables_used, word = self.pick_word(1, remaining_syllables - 1, [PREPOSITION])
        remaining_syllables -= syllables_used
        # Then create a noun phrase for it, with a limit of 50 tries
        syllables_used, noun_phrase = self.create_noun_phrase(remaining_syllables, True)
        counter = 0
        while not noun_phrase:
            if counter == 50:
                raise ExhaustedVocabulary(
                    "In the creation of a PREPOSITIONAL PHRASE, the GRAMMAR ran out of options."
                )
            syllables_used, noun_phrase = self.create_noun_phrase(remaining_syllables, True)
            counter += 1
        return syllables, word + " " + noun_phrase


if __name__ == '__main__':
    with open(f'{path}/data/the_fox_and_the_grapes.model', 'rb') as f:
        vocabulary = load(f)
    new_vocabulary = {1: {}, 2: {}, 3: {}, 4: {}, 5: {}, 6: {}, 7: {}}
    for key in vocabulary:
        for i in range(1, 8):
            new_vocabulary[i][key] = []
        for word in vocabulary[key]:
            new_vocabulary[syllablesInWord(word)][key].append(word)

    grammar = GrammarModel(new_vocabulary)
    print(grammar.create_noun_phrase(5))
    print(grammar.create_prep_phrase(7))
    print(grammar.create_verb_phrase(5))
