import os
import codecs
import re
import sys


# can raise FileNotFoundError if the file does not exist
def get_version(rel_path):
    for line in read_path(rel_path).splitlines():
        if line.startswith("__version__"):
            delim = '"' if '"' in line else "'"
            return line.split(delim)[1]


def read_path(rel_path):
    here = os.path.abspath(os.path.dirname(__file__))
    with codecs.open(os.path.join(here, rel_path), "r") as fp:
        return fp.read()


def remove_leading_trailing_newline(text):
    if text.startswith("\n"):
        text = text[1:]
    if text.endswith("\n"):
        text = text[:-1]
    return text


def verify_paths(paths):
    for path in paths:
        if not os.path.exists(path):
            print(f"Error: The path '{path}' does not exist.")
            sys.exit(1)


def remove_inner_quotes(s):
    # Define patterns for both single and double quotes
    double_quote_pattern = r"\"([^\"]*?)\""
    single_quote_pattern = r"\'([^\']*?)\'"

    # Remove inner quotes for double quotes
    s = re.sub(double_quote_pattern, lambda m: m.group(0).replace('"', ""), s)
    # Remove inner quotes for single quotes
    s = re.sub(single_quote_pattern, lambda m: m.group(0).replace("'", ""), s)

    return s


# known issue: returns "", "" on less than two word-part strings
def get_first_two_word_parts(string):
    word_parts = string.split()
    if len(word_parts) < 2:
        return "", ""
    first_word = remove_inner_quotes(word_parts[0])
    second_word = remove_inner_quotes(word_parts[1])
    return first_word, second_word
