from PyQt5.QtWidgets import (
    QApplication, QWidget
)
from PyQt5.uic import loadUi
import re
from pickle import dump


class TaggerWindow(QWidget):
    def __init__(self, source):
        super(TaggerWindow, self).__init__()
        loadUi('tagger.ui', self)
        self.pos_combo_box.addItems(['Noun', 'Determiner', 'Adjective', 'Verb', 'Adverb', 'Preposition'])
        self.add_button.clicked.connect(self.add_currently_selected_words_with_tags)
        self.next_button.clicked.connect(self.next_sentence)
        self.previous_button.clicked.connect(self.previous_sentence)
        self.save_button.clicked.connect(self.save_model)
        self.syllable_count_spin_box.setMinimum(1)
        self.syllable_count_spin_box.setMaximum(7)
        self.syllable_count_spin_box.setEnabled(False)

        self.model = {}

        self.regex = re.compile('[^a-zA-Z]')

        self.sentences = []
        self.dictionary = set()
        self.source = source
        self.generate_sentences_from_source()

        self.sentence_index = -1
        self.next_sentence()
        self.previous_button.setEnabled(False)

    def generate_sentences_from_source(self):
        with open(self.source) as f:
            data = f.read()
        data = " ".join(data.split())
        for sentence_ender in ".?!":
            data = data.replace(f'{sentence_ender} ', f'{sentence_ender}__END__ ')
            data = data.replace(f'{sentence_ender}" ', f'{sentence_ender}"__END__ ')
        self.sentences = data.split("__END__")

    def add_currently_selected_words_with_tags(self):
        tags = []
        tags.append(self.pos_combo_box.currentText().upper())
        for checkbox in [self.first_person_radio, self.gerund_radio, self.plural_radio, self.second_person_radio,
                         self.singular_radio, self.third_person_radio]:
            if checkbox.isChecked():
                tags.append('_'.join(checkbox.text().upper().split()))
        if {'VERB', 'GERUND'}.issubset(set(tags)):
            tags.remove('VERB')
        if {'FIRST_PERSON', 'SECOND_PERSON', 'THIRD_PERSON'}.issubset(set(tags)):
            tags = list(set(tags) - {'FIRST_PERSON', 'SECOND_PERSON', 'THIRD_PERSON'})
        if {'SINGULAR', 'PLURAL'}.issubset(set(tags)):
            tags = list(set(tags) - {'SINGULAR', 'PLURAL'})

        for key in self.model.keys():
            if set(key) == set(tags):
                self.model[key].extend(self.get_selected_words())
                self.dictionary.update(self.get_selected_words())
                self.update_sentence()
                return
        self.model[tuple(tags)] = self.get_selected_words()
        self.dictionary.update(self.get_selected_words())
        self.update_sentence()

    def next_sentence(self):
        self.sentence_index += 1
        if len(self.sentences) == self.sentence_index + 1:
            self.next_button.setEnabled(False)
        if self.sentence_index == 1:
            self.previous_button.setEnabled(True)
        self.update_sentence()

    def previous_sentence(self):
        self.sentence_index -= 1
        if len(self.sentences) == self.sentence_index + 2:
            self.next_button.setEnabled(True)
        if self.sentence_index == 0:
            self.previous_button.setEnabled(False)
        self.update_sentence()

    def save_model(self):
        with open('.'.join(self.source.split('.')[:-1]) + '.model', 'wb') as f:
            dump(self.model, f)

    def get_selected_words(self):
        return [self.regex.sub('', word).lower() for word in self.word_to_tag.text().split()]

    def update_sentence(self):
        self.reset_options()
        plain_text_sentence = self.sentences[self.sentence_index].split()
        rich_text_sentence = []
        for word in plain_text_sentence:
            if self.regex.sub('', word).lower() in self.dictionary:
                rich_text_sentence.append(f"<span style=\"color: #ff2222;\">{word}</span>")
            else:
                rich_text_sentence.append(word)
        self.sentence_label.setText(" ".join(rich_text_sentence))

    def reset_options(self):
        for checkbox in [self.first_person_radio, self.gerund_radio, self.plural_radio, self.second_person_radio,
                         self.singular_radio, self.third_person_radio]:
            checkbox.setChecked(False)
        self.pos_combo_box.setCurrentIndex(0)
        self.syllable_count_spin_box.setValue(1)
        self.word_to_tag.clear()


if __name__ == '__main__':
    app = QApplication([])
    window = TaggerWindow('c:/Users/gavyn/PycharmProjects/HaikuGrammar/data/the_fox_and_the_grapes.txt')
    window.show()
    app.exec_()
