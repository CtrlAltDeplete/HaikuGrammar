import re

from src.constants import path
from pickle import dump
from PyQt5.QtWidgets import (
    QApplication, QWidget
)
from PyQt5.uic import loadUi


class TaggerWindow(QWidget):
    def __init__(self, source):
        super(TaggerWindow, self).__init__()
        loadUi('tagger.ui', self)
        self.form_combo_box.addItems(['', 'Noun', 'Determiner', 'Adjective', 'Verb', 'Adverb', 'Preposition', 'Coordinating Conjunction', 'Pronoun'])
        self.function_combo_box.addItems(['', 'Direct Object', 'Indirect Object', 'Subject', 'Subject Compliment', 'Object Compliment', 'Object of Preposition', 'Gerund', 'Participle', 'Transitive', 'Intransitive', 'Linking', 'Be'])
        self.add_button.clicked.connect(self.add_currently_selected_words_with_tags)
        self.next_button.clicked.connect(self.next_sentence)
        self.previous_button.clicked.connect(self.previous_sentence)
        self.save_button.clicked.connect(self.save_model)

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
        if self.form_combo_box.currentText():
            tags.append('_'.join(self.form_combo_box.currentText().upper().split()))
        if self.function_combo_box.currentText():
            tags.append('_'.join(self.function_combo_box.currentText().upper().split()))

        radios = (self.first_singular_radio, self.first_plural_radio,
                  self.second_singular_radio, self.second_plural_radio,
                  self.third_singular_radio, self.third_plural_radio)
        radio_tags = (('FIRST_PERSON', 'SINGULAR'), ('FIRST_PERSON', 'PLURAL'),
                      ('SECOND_PERSON', 'SINGULAR'), ('SECOND_PERSON', 'PLURAL'),
                      ('THIRD_PERSON', 'SINGULAR'), ('THIRD_PERSON', 'PLURAL'))

        for i, radio in enumerate(radios):
            if radio.isChecked():
                tags.extend(radio_tags[i])

        for key in self.model.keys():
            if set(key) == set(tags):
                self.model[key].append(self.get_selected_words())
                self.dictionary.update([self.get_selected_words()])
                self.update_sentence()
                return
        self.model[tuple(tags)] = [self.get_selected_words()]
        self.dictionary.update([self.get_selected_words()])
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
        return self.regex.sub('', self.word_to_tag.toPlainText()).lower()

    def update_sentence(self):
        self.reset_options()
        self.progress_label.setText(f"{self.sentence_index + 1} / {len(self.sentences)}")
        plain_text_sentence = self.sentences[self.sentence_index].split()
        rich_text_sentence = []
        for word in plain_text_sentence:
            if self.regex.sub('', word).lower() in self.dictionary:
                rich_text_sentence.append(f"<span style=\"color: #ff2222;\">{word}</span>")
            else:
                rich_text_sentence.append(word)
        self.sentence_label.setText(" ".join(rich_text_sentence))

    def reset_options(self):
        self.form_combo_box.setCurrentIndex(0)
        self.function_combo_box.setCurrentIndex(0)
        self.word_to_tag.clear()

        radios = (self.first_singular_radio, self.first_plural_radio,
                  self.second_singular_radio, self.second_plural_radio,
                  self.third_singular_radio, self.third_plural_radio)

        for radio in radios:
            radio.setChecked(False)


if __name__ == '__main__':
    app = QApplication([])
    window = TaggerWindow(f'{path}/data/the_fox_and_the_grapes.txt')
    window.show()
    app.exec_()
