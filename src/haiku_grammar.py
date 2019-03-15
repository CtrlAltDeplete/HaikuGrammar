from src.constants import *
from src.Syllables import syllables_in_word
from random import randint, choice
from pickle import load


class ExhaustedVocabulary(Exception):
    pass


class UnsuccessfulPhraseGeneration(Exception):
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

    def create_verb_phrase(self, min_syllables, max_syllables, gram_function=None, max_tries=20):
        if gram_function is None:
            gram_function = choice((BE, LINKING, INTRANSITIVE, TRANSITIVE))

        if gram_function is BE:
            structure_options = ((4, VERB, PREP_PHRASE),
                                 (2, VERB, SUBJECT_COMPLIMENT))
        elif gram_function is LINKING:
            structure_options = ((2, VERB, SUBJECT_COMPLIMENT),)
        elif gram_function is INTRANSITIVE:
            structure_options = ((5, ADVERB, VERB, PREP_PHRASE),
                                 (5, VERB, ADVERB, PREP_PHRASE),
                                 (5, VERB, PREP_PHRASE, ADVERB),
                                 (4, VERB, PREP_PHRASE),
                                 (2, VERB, ADVERB),
                                 (1, VERB))
        elif gram_function is TRANSITIVE:
            structure_options = ((3, ADVERB, VERB, DIRECT_OBJECT),
                                 (3, VERB, DIRECT_OBJECT, ADVERB),
                                 (5, VERB, DIRECT_OBJECT, PREP_PHRASE),
                                 (6, ADVERB, VERB, DIRECT_OBJECT, PREP_PHRASE),
                                 (6, VERB, DIRECT_OBJECT, PREP_PHRASE, ADVERB))
        elif gram_function is GERUND:
            structure_options = ((2, VERB, DIRECT_OBJECT),
                                 (3, VERB, DIRECT_OBJECT, ADVERB))
        elif gram_function is PARTICIPLE:
            structure_options = ((1, VERB),)
        else:
            raise UnsuccessfulPhraseGeneration(f"Unknown grammatical function for verbs: {gram_function}")

        chosen_structure = choice([opt[1:] for opt in structure_options if opt[0] <= max_syllables])

        if gram_function in [BE, LINKING, INTRANSITIVE, TRANSITIVE]:
            self.global_tags = []

        tries = 0

        while tries < max_tries:
            options_used = []
            words_used = []
            syllables_used = 0
            remaining_choices = list(chosen_structure)

            while True:
                if max_syllables <= syllables_used:
                    break
                if not remaining_choices:
                    break
                current_min_syllables = 1 if len(remaining_choices) > 1 else min_syllables - syllables_used
                current_max_syllables = max_syllables - syllables_used
                word_form_to_pick = choice(list(remaining_choices))
                if word_form_to_pick is VERB:
                    syllables, word = self.pick_word(current_min_syllables, current_max_syllables, [gram_function, VERB])
                elif word_form_to_pick is PREP_PHRASE:
                    syllables, word = self.create_prep_phrase(3, current_max_syllables)
                elif word_form_to_pick is SUBJECT_COMPLIMENT:
                    syllables, word = self.create_subject_compliment(current_min_syllables, current_max_syllables)
                elif word_form_to_pick is ADVERB:
                    syllables, word = self.pick_word(current_min_syllables, current_max_syllables, [ADVERB, gram_function])
                elif word_form_to_pick is DIRECT_OBJECT:
                    syllables, word = self.create_direct_object(current_min_syllables, current_max_syllables)
                else:
                    raise UnsuccessfulPhraseGeneration(f"Unknown word form for verbs: {word_form_to_pick}")
                options_used.append(word_form_to_pick)
                words_used.append(word)
                syllables_used += syllables
                remaining_choices.remove(word_form_to_pick)

            tries += 1

            if min_syllables > syllables_used or max_syllables < syllables_used:
                break

            verb_phrase = []
            for word_form in chosen_structure:
                for i, tag in enumerate(options_used):
                    if tag == word_form:
                        verb_phrase.append(words_used[i])
                        break
            return syllables_used, ' '.join(verb_phrase)

        raise UnsuccessfulPhraseGeneration(f"Unsuccessfully met word count for verb phrase.")

    def create_subject_compliment(self, min_syllables, max_syllables, gram_form=None):
        if gram_form is None:
            gram_form = choice([NOUN, ADJECTIVE])

        if gram_form is NOUN:
            return self.create_noun_phrase(min_syllables, max_syllables, SUBJECT_COMPLIMENT)
        elif gram_form is ADJECTIVE:
            return self.pick_word(min_syllables, max_syllables, [ADJECTIVE, SUBJECT_COMPLIMENT])
        else:
            raise UnsuccessfulPhraseGeneration(f"Unknown grammatical form for subject compliment: {gram_form}")

    def create_direct_object(self, min_syllables, max_syllables):
        return self.create_noun_phrase(min_syllables, max_syllables, DIRECT_OBJECT)

    def create_noun_phrase(self, min_syllables, max_syllables, gram_function=None, max_tries=20):
        if gram_function is None:
            gram_function = choice([SUBJECT, SUBJECT_COMPLIMENT, OBJECT_COMPLIMENT, DIRECT_OBJECT, OBJECT_OF_PREPOSITION])

        structure_options = ((1, NOUN),
                             (2, ADJECTIVE, NOUN),
                             (2, DETERMINER, NOUN),
                             (3, DETERMINER, ADJECTIVE, NOUN),
                             (4, DETERMINER, ADJECTIVE, ADJECTIVE, NOUN),
                             (3, ADJECTIVE, ADJECTIVE, NOUN),
                             (4, NOUN, PREP_PHRASE),
                             (5, DETERMINER, NOUN, PREP_PHRASE),
                             (5, ADJECTIVE, NOUN, PREP_PHRASE),
                             (6, DETERMINER, ADJECTIVE, NOUN, PREP_PHRASE),
                             (3, gram_function, COORDINATING_CONJUNCTION, gram_function),
                             (1, PRONOUN),
                             (3, GERUND, DIRECT_OBJECT))

        if gram_function is OBJECT_OF_PREPOSITION:
            structure_options = (opt for opt in structure_options if DETERMINER in opt)

        chosen_structure = choice([opt[1:] for opt in structure_options if opt[0] <= max_syllables])

        if gram_function is SUBJECT:
            self.global_tags = []

        tries = 0

        while tries < max_tries:
            options_used = []
            words_used = []
            syllables_used = 0
            remaining_choices = list(chosen_structure)

            while True:
                if not remaining_choices or syllables_used >= max_syllables:
                    break
                current_min_syllables = 1 if len(remaining_choices) > 1 else max(1, min_syllables - syllables_used)
                current_max_syllables = max_syllables - syllables_used
                word_form_to_pick = choice(list(remaining_choices)) if PREP_PHRASE not in remaining_choices else PREP_PHRASE
                if word_form_to_pick in [NOUN, PRONOUN, GERUND]:
                    syllables, word = self.pick_word(current_min_syllables, current_max_syllables, [gram_function, word_form_to_pick])
                elif word_form_to_pick is ADJECTIVE:
                    syllables, word = self.pick_word(current_min_syllables, current_max_syllables, [ADJECTIVE, gram_function])
                elif word_form_to_pick is DETERMINER:
                    syllables, word = self.pick_word(current_min_syllables, current_max_syllables, [DETERMINER, gram_function])
                elif word_form_to_pick is PREP_PHRASE:
                    syllables, word = self.create_prep_phrase(current_min_syllables, current_max_syllables)
                elif word_form_to_pick is gram_function:
                    syllables, word = self.create_noun_phrase(current_min_syllables, current_max_syllables, gram_function)
                elif word_form_to_pick is COORDINATING_CONJUNCTION:
                    syllables, word = self.pick_word(current_min_syllables, current_max_syllables, [COORDINATING_CONJUNCTION, gram_function])
                elif word_form_to_pick is DIRECT_OBJECT:
                    syllables, word = self.create_direct_object(current_min_syllables, current_max_syllables)
                else:
                    raise UnsuccessfulPhraseGeneration(f"Unknown word form for verbs: {word_form_to_pick}")
                options_used.append(word_form_to_pick)
                words_used.append(word)
                syllables_used += syllables
                remaining_choices.remove(word_form_to_pick)

            tries += 1

            if max_syllables < syllables_used or min_syllables > syllables_used or len(options_used) != len(chosen_structure):
                break

            noun_phrase = []
            for word_form in chosen_structure:
                for i, tag in enumerate(options_used):
                    if tag == word_form:
                        noun_phrase.append(words_used[i])
                        break
            return syllables_used, ' '.join(noun_phrase)

        raise UnsuccessfulPhraseGeneration(f"Unsuccessfully met word count for verb phrase.")

    def create_prep_phrase(self, min_syllables, max_syllables, max_tries=20):
        tries = 0
        while tries < max_tries:
            syllables_used = 0
            syllables, preposition = self.pick_word(1, max_syllables - 2, [PREPOSITION])
            syllables_used += syllables
            syllables, object_of_preposition = self.create_noun_phrase(1, max_syllables - syllables_used, OBJECT_OF_PREPOSITION)
            syllables_used += syllables

            if min_syllables > syllables_used or max_syllables < syllables_used:
                tries += 1
                continue

            return syllables_used, ' '.join([preposition, object_of_preposition])

        raise UnsuccessfulPhraseGeneration(f"Unsuccessfully met word count for prep phrase.")


if __name__ == '__main__':
    with open(f'{path}/data/cs.model', 'rb') as f:
        vocabulary = load(f)
    new_vocabulary = {1: {}, 2: {}, 3: {}, 4: {}, 5: {}, 6: {}, 7: {}}
    for key in vocabulary:
        for i in range(1, 8):
            new_vocabulary[i][key] = []
        for word in vocabulary[key]:
            new_vocabulary[syllables_in_word(word)][key].append(word)

    grammar = GrammarModel(new_vocabulary)

    tries = 0
    while tries < 20:
        try:
            noun_phrase = grammar.create_noun_phrase(5, 5, SUBJECT)[1]
            print(noun_phrase)
            break
        except UnsuccessfulPhraseGeneration:
            tries += 1
            continue

    tries = 0
    while tries < 20:
        try:
            verb_phrase = grammar.create_verb_phrase(7, 7)[1]
            print(verb_phrase)
            break
        except UnsuccessfulPhraseGeneration:
            tries += 1
            continue

    tries = 0
    while tries < 20:
        try:
            prep_phrase = grammar.create_prep_phrase(5, 5)[1]
            print(prep_phrase)
            break
        except UnsuccessfulPhraseGeneration:
            tries += 1
            continue
