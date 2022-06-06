import csv
import unittest


class TriviaQuestionsTests(unittest.TestCase):
    questions_file = '../assets/questions.csv'

    valid_sources = [
        "The Silmarillion (book)",
        "Extended Lore",
        "The Lord of the Rings (book)",
        "The Lord of the Rings (P. J. movie adaptations)",
        "The Hobbit (book)",
        "The Hobbit (P. J. movie adaptations)",
        "Life of Tolkien",
        "History of Middle-Earth (book)",
        "Tolkien's Languages",
        "Arda Geography",
        "General Knowledge"
    ]

    def test_parse(self):
        with open(self.questions_file, 'r') as csvfile:
            csv.reader(csvfile, delimiter=',', quotechar='"')

    def test_number_of_arguments(self):
        with open(self.questions_file, 'r') as csvfile:
            for i, entries in enumerate(csv.reader(csvfile, delimiter=',', quotechar='"')):
                self.assertEqual(6, len(entries),
                                 'Invalid number of arguments for this question:\n' + entries[1])

    def test_sources(self):
        with open(self.questions_file, 'r') as csvfile:
            for i, entries in enumerate(csv.reader(csvfile, delimiter=',', quotechar='"')):
                source, question, *answers = entries
                self.assertFalse('source' in source.lower(),
                                 'Source not set for this question:\n' + question)

                self.assertIn(source, self.valid_sources,
                              'Source not in list of valid sources for this question:\n' + question)

    def test_format(self):
        with open(self.questions_file, 'r') as csvfile:
            for i, entries in enumerate(csv.reader(csvfile, delimiter=',', quotechar='"')):
                source, question, *answers = entries
                self.assertIn('?', question,
                              'No question mark in this question:\n' + question)

    def test_marked_answers(self):
        with open(self.questions_file, 'r') as csvfile:
            for i, entries in enumerate(csv.reader(csvfile, delimiter=',', quotechar='"')):
                source, question, *answers = entries
                count = 0
                for item in answers:
                    if item.startswith('*'):
                        count += 1
                self.assertNotEqual(0, count,
                                    'No correct answers marked for this question:\n' + question)
                self.assertEqual(1, count,
                                 f'Too many ({count}) correct answers marked:\n' + question)
