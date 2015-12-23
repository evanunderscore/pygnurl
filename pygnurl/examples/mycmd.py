"""Example showing completion in a command line environment."""
from __future__ import print_function

import cmd
# Import this before Cmd does so we can override things it changes.
import readline  # pylint: disable=unused-import

import pygnurl

completion = pygnurl.readline.completion  # pylint: disable=invalid-name

# These are the characters that signify a break between words.
completion.word_break_characters = completion.basic_word_break_characters
# If any of the word_break_characters appear in a filename, require it
# to be quoted.
completion.filename_quote_characters = completion.word_break_characters
# Filenames can be quoted with any of these characters.
completion.quote_characters = completion.basic_quote_characters


class MyCmd(cmd.Cmd, object):
    """Example shell with simple commands."""
    # pylint: disable=unused-argument,no-self-use
    def do_cat(self, line, *args):
        """Display the contents of a file.

        usage: cat <file>

        The file argument will tab complete.
        """
        with open(line) as cat_file:
            print(cat_file.read())

    def complete_cat(self, line, *args):
        """Complete the filename argument to cat."""
        return completion.filename_completions(line)

    def do_exit(self, *args):
        """Exit the shell."""
        return 1

    def complete(self, text, state):
        # Cmd uses the readline module which sets append_character to
        # '\0' before calling the completer. This is useful in the
        # interpreter but not on a command line. We'll set it back to
        # ' ' before calling the completer.
        completion.append_character = ' '
        return super(MyCmd, self).complete(text, state)


if __name__ == '__main__':
    MyCmd().cmdloop()
