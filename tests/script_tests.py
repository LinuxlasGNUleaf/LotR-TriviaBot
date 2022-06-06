import re
import unittest


class ScriptTests(unittest.TestCase):
    # this regex finds lines that are directly followed by a CAPITALIZED line (i.e. missing linebreak)
    missing_linebreak_regex = re.compile(r".*\S.*\n\b[A-Z][A-Z]+\b")
    # this regex finds paragraphs that have no header, i.e. no CAPITALIZED line in front of it.
    missing_speaker_regex = re.compile(r"\n\n\b[A-Z][a-z]+.*\b")

    file_location = '../assets/script.txt'

    def test_newlines(self):
        with open(self.file_location, 'r') as f:
            matches = re.finditer(self.missing_linebreak_regex, f.read())
            match_str = '\n'.join([match[0] for match in matches])
            self.assertIsNot(matches,
                             f'The following matches for missing newlines have been found:\n'+match_str)

    def test_speaker_lines(self):
        with open(self.file_location, 'r') as f:
            matches = re.finditer(self.missing_speaker_regex, f.read())
            match_str = '\n'.join([match[0] for match in matches])
            self.assertIsNot(matches,
                             f'The following matches for missing or misformatted speaker lines have been found:\n' + match_str)
