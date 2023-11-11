import unittest

import yaml


class QuotesTests(unittest.TestCase):
    quotes_file = '../../assets/quotes.yaml'
    greek_to_num = {
        1: 'single',
        2: 'double',
        3: 'triple',
        4: 'quad',
        5: 'penta',
        6: 'hexa'
    }
    sub_categories = ["shipping", "nonshipping"]
    sub_sub_categories = ["nsfw", "sfw"]

    suspicious_chars = ['<', '[', ']', '>']

    def test_parse(self):
        with open(self.quotes_file, 'r', encoding='utf-8') as qfile:
            yaml.safe_load(qfile)

    def test_categories(self):
        with open(self.quotes_file, 'r', encoding='utf-8') as qfile:
            quotes = yaml.safe_load(qfile)

            for num, category in self.greek_to_num.items():
                category = f'{category}Quotes'
                self.assertIn(category, quotes,
                              f'Category "{category}" was not found!')
                for sub_category in self.sub_categories:
                    self.assertIn(sub_category, quotes[category],
                                  f'Sub-category "{sub_category}" was not found!')
                    for sub_sub_category in self.sub_sub_categories:
                        self.assertIn(sub_sub_category, quotes[category][sub_category],
                                      f'Sub-sub-category "{sub_sub_category}" was not found!')
                return

    def test_character_numbers(self):
        with open(self.quotes_file, 'r', encoding='utf-8') as qfile:
            quotes = yaml.safe_load(qfile)
            for num, category in self.greek_to_num.items():
                category = f'{category}Quotes'
                category_quotes = []
                for sub_cat in self.sub_categories:
                    for sub_sub_cat in self.sub_sub_categories:
                        category_quotes += quotes[category][sub_cat][sub_sub_cat]

                for i, quote in enumerate(category_quotes):
                    for test_num in range(max(self.greek_to_num.keys())):
                        test_str = f"{{{test_num}}}"
                        if test_num < num:
                            self.assertIn(test_str, quote,
                                          f'player {test_num} not found in quote:\n\t\t"{quote[:40]}"')
                        else:
                            self.assertNotIn(test_str, quote,
                                             f'player {test_num} found in quote, which is more than allowed:\n\t\t"{quote[:40]}')


if __name__ == '__main__':
    unittest.main()
