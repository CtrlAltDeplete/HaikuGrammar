from PyQt5.QtWidgets import (
    QApplication, QWidget
)
from PyQt5.uic import loadUi


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
        self.syllable_count_spin_box.setMaximum(1)

        self.model = {}

        self.sentences = []
        self.generate_sentences_from_source(source)

        self.sentence_index = -1
        self.next_sentence()
        self.previous_button.setEnabled(False)

    def generate_sentences_from_source(self, source):
        with open(source) as f:
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
                tags.append(checkbox.text().upper())
        if 'VERB' in tags and 'GERUND' in tags:
            tags.remove('VERB')
        for key in self.model.keys():
            if set(key) == set(tags):
                self.model[key].append(self.get_selected_words())
                return
        self.model[tags] = [self.get_selected_words()]

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
        pass

    def get_selected_words(self):
        pass

    def update_sentence(self):
        self.reset_options()
        self.sentence_label.setText(self.sentences[self.sentence_index])

    def reset_options(self):
        for checkbox in [self.first_person_radio, self.gerund_radio, self.plural_radio, self.second_person_radio,
                         self.singular_radio, self.third_person_radio]:
            checkbox.setChecked(False)
        self.pos_combo_box.setCurrentIndex(0)
        self.syllable_count_spin_box.setValue(1)


if __name__ == '__main__':
    app = QApplication([])
    window = TaggerWindow('c:/Users/gavyn/Documents/Python/HaikuGrammar/data/the_fox_and_the_grapes.txt')
    window.show()
    app.exec_()
