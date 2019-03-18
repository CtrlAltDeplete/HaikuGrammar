from src.constants import *
from src.Syllables import syllables_in_word
from random import randint, choice
from pickle import load, dump


class ExhaustedVocabulary(Exception):
    pass


class UnsuccessfulPhraseGeneration(Exception):
    pass


class GrammarModel:
    def __init__(self, vocabulary: dict=None):
        self.vocabulary = vocabulary
        if vocabulary is None:
            self.vocabulary = {}
        self.global_tags = (PAST, PRESENT, PERFECT, PROGRESSIVE, CONDITIONAL, SUBJUNCTIVE, PASSIVE, ACTIVE,
                            FIRST_PERSON, SECOND_PERSON, THIRD_PERSON, SINGULAR, PLURAL)
        self.current_global_tags = []

    def add_word(self, word: str, syllables: int, tags: list):
        for key in self.vocabulary[syllables].keys():
            if set(key) == set(tags):
                if word not in self.vocabulary[syllables][key]:
                    self.vocabulary[syllables][key].append(word)
                return
        self.vocabulary[syllables][tags] = [word]

    def pick_word(self, min_syllables: int, max_syllables: int, tags: list, update_global_tags=False) -> tuple:
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
                if tag in self.global_tags and tag not in self.current_global_tags and update_global_tags:
                    self.current_global_tags.append(tag)
            return c[0], c[2]
        raise ExhaustedVocabulary(
            f"No words found between {min_syllables} and {max_syllables} syllables with tags {tags}."
        )

    def create_verb_phrase(self, min_syllables, max_syllables, gram_function=None, max_tries=20):
        starting_global_tags = self.current_global_tags.copy()
        all_structure_options = {
            BE: ((4, VERB, PREP_PHRASE), (2, VERB, SUBJECT_COMPLIMENT)),
            LINKING: ((2, VERB, SUBJECT_COMPLIMENT),),
            INTRANSITIVE: ((5, ADVERB, VERB, PREP_PHRASE), (5, VERB, ADVERB, PREP_PHRASE),
                           (5, VERB, PREP_PHRASE, ADVERB), (4, VERB, PREP_PHRASE), (2, VERB, ADVERB), (1, VERB)),
            TRANSITIVE: ((4, ADVERB, VERB, DIRECT_OBJECT), (4, VERB, DIRECT_OBJECT, ADVERB),
                         (6, VERB, DIRECT_OBJECT, PREP_PHRASE), (7, ADVERB, VERB, DIRECT_OBJECT, PREP_PHRASE),
                         (7, VERB, DIRECT_OBJECT, PREP_PHRASE, ADVERB)),
            GERUND: ((2, VERB, DIRECT_OBJECT), (3, VERB, DIRECT_OBJECT, ADVERB)),
            PARTICIPLE: ((1, VERB),)
        }

        if gram_function:
            structure_options = all_structure_options[gram_function]
        else:
            structure_options = []
            for key in all_structure_options:
                if key not in [GERUND, PARTICIPLE]:
                    structure_options.extend(all_structure_options[key])

        chosen_structure = choice([opt[1:] for opt in structure_options if opt[0] <= max_syllables])

        tries = 0

        while tries < max_tries:
            self.current_global_tags = starting_global_tags.copy()
            options_used = []
            words_used = []
            syllables_used = 0
            remaining_choices = list(chosen_structure)

            while True:
                if max_syllables <= syllables_used or not remaining_choices:
                    break
                current_min_syllables = 1 if len(remaining_choices) > 1 else min_syllables - syllables_used
                current_max_syllables = max_syllables - syllables_used - len(chosen_structure) + len(options_used) + 1
                if PREP_PHRASE in chosen_structure and PREP_PHRASE not in options_used:
                    current_max_syllables -= 2
                if DIRECT_OBJECT in chosen_structure and DIRECT_OBJECT not in options_used:
                    current_max_syllables -= 1
                word_form_to_pick = choice(remaining_choices)
                try:
                    if word_form_to_pick is VERB:
                        syllables, word = self.pick_word(current_min_syllables, current_max_syllables, [gram_function, VERB] if gram_function else [VERB])
                    elif word_form_to_pick is PREP_PHRASE:
                        current_max_syllables = max(current_max_syllables, 3)
                        syllables, word = self.create_prep_phrase(3, current_max_syllables)
                    elif word_form_to_pick is SUBJECT_COMPLIMENT:
                        syllables, word = self.create_subject_compliment(current_min_syllables, current_max_syllables)
                    elif word_form_to_pick is ADVERB:
                        syllables, word = self.pick_word(current_min_syllables, current_max_syllables, [ADVERB, gram_function])
                    elif word_form_to_pick is DIRECT_OBJECT:
                        current_max_syllables = max(current_max_syllables, 2)
                        syllables, word = self.create_direct_object(current_min_syllables, current_max_syllables)
                    else:
                        raise UnsuccessfulPhraseGeneration(f"Unknown word form for verbs: {word_form_to_pick}")
                except ExhaustedVocabulary:
                    break
                if word not in words_used:
                    options_used.append(word_form_to_pick)
                    words_used.append(word)
                    syllables_used += syllables
                    remaining_choices.remove(word_form_to_pick)

            tries += 1

            if not (min_syllables <= syllables_used <= max_syllables) or len(options_used) != len(chosen_structure):
                break

            verb_phrase = []
            for word_form in chosen_structure:
                for i, tag in enumerate(options_used):
                    if tag == word_form:
                        verb_phrase.append(words_used.pop(i))
                        options_used.pop(i)
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

    def create_noun_phrase(self, min_syllables, max_syllables, gram_function=None, max_tries=20, chosen_structure=None):
        # Store what the global tags were before generation.
        starting_global_tags = self.current_global_tags.copy()
        # All possible structure options for noun phrases and their minimum syllable count.
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

        if gram_function is None:
            gram_function = NOUN

        # If the function of this noun phrase is the object of a preposition, we need a determiner in our structure.
        if gram_function in [DIRECT_OBJECT, OBJECT_OF_PREPOSITION]:
            structure_options = (opt for opt in structure_options if DETERMINER in opt)

        # Choose a structure out of all the options, as long as the minimum required syllable count for that structure
        # is less than or equal to the noun phrase's maximum syllable count.
        if chosen_structure is None:
            chosen_structure = choice([opt[1:] for opt in structure_options if opt[0] <= max_syllables])

        tries = 0

        while tries < max_tries:
            # Reset all values at the beginning of an attempt.
            self.current_global_tags = starting_global_tags.copy()
            options_used = []
            words_used = []
            syllables_used = 0
            remaining_choices = list(chosen_structure)

            while True:
                # If we ran out of choices or have reached our max syllable count, break out.
                if not remaining_choices or syllables_used >= max_syllables:
                    break
                # Otherwise, set the minimum syllable count for the current strucrural component to 1 if their are more
                # structural components. If there aren't any more components, set it to the number of syllables required
                # to meet the minimum syllable amount of the phrase.
                current_min_syllables = 1 if len(remaining_choices) > 1 else max(1, min_syllables - syllables_used)
                # Set the max syllable count to the max syllables - used syllables - 1 for each remaining component.
                current_max_syllables = max_syllables - syllables_used - len(chosen_structure) + len(options_used) + 1
                # If we still need to make a prepositional phrase, lower the max syllables by two more, because prep
                # phrases require at least 3 syllables.
                if PREP_PHRASE in chosen_structure and PREP_PHRASE not in options_used:
                    current_max_syllables -= 2
                # Randomly choose what component we are generating.
                word_form_to_pick = choice(list(remaining_choices))
                try:
                    # Based on the structure, call the appropriate method.
                    if word_form_to_pick in [NOUN, PRONOUN, GERUND]:
                        syllables, word = self.pick_word(current_min_syllables, current_max_syllables, [gram_function, word_form_to_pick], update_global_tags=gram_function is SUBJECT)
                    elif word_form_to_pick is ADJECTIVE:
                        syllables, word = self.pick_word(current_min_syllables, current_max_syllables, [ADJECTIVE, gram_function])
                    elif word_form_to_pick is DETERMINER:
                        syllables, word = self.pick_word(current_min_syllables, current_max_syllables, [DETERMINER, gram_function])
                    elif word_form_to_pick is PREP_PHRASE:
                        current_max_syllables = max(current_max_syllables, 3)
                        syllables, word = self.create_prep_phrase(current_min_syllables, current_max_syllables)
                    elif word_form_to_pick is gram_function:
                        syllables, word = self.create_noun_phrase(current_min_syllables, current_max_syllables, gram_function)
                    elif word_form_to_pick is COORDINATING_CONJUNCTION:
                        syllables, word = self.pick_word(current_min_syllables, current_max_syllables, [COORDINATING_CONJUNCTION, gram_function])
                    elif word_form_to_pick is DIRECT_OBJECT:
                        syllables, word = self.create_direct_object(current_min_syllables, current_max_syllables)
                    else:
                        raise UnsuccessfulPhraseGeneration(f"Unknown word form for verbs: {word_form_to_pick}")
                except ExhaustedVocabulary:
                    break
                # If that word isn't already used in this phrase,
                if word not in words_used:
                    # Update all the values appropriately.
                    options_used.append(word_form_to_pick)
                    words_used.append(word)
                    syllables_used += syllables
                    remaining_choices.remove(word_form_to_pick)

            tries += 1

            # Check if all the phrase's requirements are met.
            if not (min_syllables <= syllables_used <= max_syllables) or len(options_used) != len(chosen_structure):
                break

            # If they are, compose our noun phrase.
            noun_phrase = []
            # Iterate through all components of the chosen structure and
            for word_form in chosen_structure:
                # All of our used options/words.
                for i, tag in enumerate(options_used):
                    if tag == word_form:
                        # Append the word that matches the current component from the chosen structure.
                        noun_phrase.append(words_used.pop(i))
                        options_used.pop(i)
                        break
            # Then return the noun phrase, joined by spaces.
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

    def create_independent_clause(self, min_syllables, max_syllables, max_tries=20):
        tries = 0
        while tries < max_tries:
            noun_phrase_syllables, noun_phrase = self.create_noun_phrase(1, max_syllables - 1)
            verb_phrase_syllables, verb_phrase = self.create_verb_phrase(max(1, min_syllables - noun_phrase_syllables), max_syllables - noun_phrase_syllables)
            syllables_used = noun_phrase_syllables + verb_phrase_syllables

            if not (min_syllables <= syllables_used <= max_syllables):
                tries += 1
                continue

            return syllables_used, ' '.join([noun_phrase, verb_phrase])

        raise UnsuccessfulPhraseGeneration(f"Unsuccessfully met word count for independent clause.")

    def create_haiku(self, chosen_structure=None, max_tries=20):
        total_tries = 0
        structure = chosen_structure

        while total_tries < max_tries:
            if chosen_structure is None:
                options = (self.create_verb_phrase, self.create_noun_phrase, self.create_prep_phrase, self.create_independent_clause)
                structure = (lambda: choice(options)(5, 5), lambda: choice(options)(7, 7), lambda: choice(options)(5, 5))

            line_tries = 0
            while line_tries < max_tries:
                try:
                    line1 = structure[0]()[1]
                    break
                except UnsuccessfulPhraseGeneration:
                    line1 = None
                    line_tries += 1
                    continue
            if line1 is None:
                total_tries += 1
                continue

            line_tries = 0
            while line_tries < max_tries:
                try:
                    line2 = structure[1]()[1]
                    break
                except UnsuccessfulPhraseGeneration:
                    line2 = None
                    line_tries += 1
                    continue
            if line2 is None:
                total_tries += 1
                continue

            line_tries = 0
            while line_tries < max_tries:
                try:
                    line3 = structure[2]()[1]
                    break
                except UnsuccessfulPhraseGeneration:
                    line3 = None
                    line_tries += 1
                    continue
            if line3 is None:
                total_tries += 1
                continue

            return '\n'.join([line1, line2, line3])

        raise UnsuccessfulPhraseGeneration(f"Maximum tries reached for haiku creation.")


def demo_1(grammar):
    with open(f'{path}/data/cs.model', 'rb') as f:
        vocabulary = load(f)
    grammar = GrammarModel(vocabulary)

    print(grammar.create_haiku((
        lambda: grammar.create_prep_phrase(5, 5),
        lambda: grammar.create_noun_phrase(7, 7, SUBJECT),
        lambda: grammar.create_verb_phrase(5, 5))))


def demo_2():
    with open(f'{path}/data/the_fox_and_the_grapes.model', 'rb') as f:
        vocabulary = load(f)
    grammar = GrammarModel(vocabulary)

    print(grammar.create_noun_phrase(3, 3, chosen_structure=(DETERMINER, ADJECTIVE, NOUN)))


if __name__ == '__main__':
    demo_1()
    # demo_2()
