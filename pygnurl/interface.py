"""High-level interface to Readline API."""
from __future__ import unicode_literals

import contextlib
from ctypes import *  # pylint: disable=wildcard-import,unused-wildcard-import
import errno
import functools
import locale
import logging
import os
import select
import signal
import time

from . import bindings
from . import strings
from . import typedefs


@contextlib.contextmanager
def store_locale():
    """Save and restore the current locale."""
    saved_locale = locale.setlocale(locale.LC_CTYPE, '')
    locale.setlocale(locale.LC_CTYPE, '')
    try:
        yield
    finally:
        locale.setlocale(locale.LC_CTYPE, saved_locale)


@contextlib.contextmanager
def ignore_sigint():
    """Ignore SIGINT for the duration."""
    old_handler = signal.signal(signal.SIGINT, signal.SIG_IGN)
    try:
        yield
    finally:
        signal.signal(signal.SIGINT, old_handler)


class Readline(object):
    """Python interface to Readline library."""
    # modelling this after the C implementation
    # pylint: disable=invalid-name
    # pylint: disable=too-many-public-methods,too-many-instance-attributes
    def __init__(self, dll):
        self.lib = bindings.Bindings(dll)
        self.history = History(self.lib)
        self.completion = Completion(self.lib)

        self.startup_hook = None
        """If not None, this function is called with no arguments just
        before readline prints the first prompt.
        """

        self.pre_input_hook = None
        """If not None, The function is called with no arguments after
        the first prompt has been printed and just before readline
        starts reading input characters.
        """

        self.logger = logging.getLogger(__name__)

        self._completed_input_string = None
        self._input_complete = False
        self._functions = {}
        self._function_wrappers = {}

        self._initreadline()

    @property
    def version(self):
        """Return the version number of the library.

        The encoding is of the form 0xMMmm, where MM is the two-digit
        major version number, and mm is the two-digit minor version
        number.
        """
        version = self.lib.get(c_int, 'rl_readline_version')
        self.logger.debug('readline version: 0x%x', version)
        return version

    @property
    def name(self):
        """Unique name for the current application."""
        return self.lib.get(c_char_p, 'rl_readline_name')

    @name.setter
    def name(self, name):
        self.lib.set(c_char_p, 'rl_readline_name', name)

    @property
    def instream(self):
        """The stdio stream from which Readline reads input."""
        return self.lib.get(c_void_p, 'rl_instream')

    @instream.setter
    def instream(self, instream):
        self.lib.set(c_void_p, 'rl_instream', instream)

    @property
    def outstream(self):
        """The stdio stream to which Readline performs output."""
        return self.lib.get(c_void_p, 'rl_outstream')

    @outstream.setter
    def outstream(self, outstream):
        self.lib.set(c_void_p, 'rl_outstream', outstream)

    @property
    def done(self):
        """If True, Readline immediately returns the line."""
        return self.lib.get(c_bool, 'rl_done')

    @done.setter
    def done(self, done):
        self.lib.set(c_bool, 'rl_done', done)

    @property
    def point(self):
        """The offset of the cursor in line_buffer."""
        return self.lib.get(c_int, 'rl_point')

    @point.setter
    def point(self, point):
        if point > len(self.line_buffer):
            raise ValueError('point is not contained in line_buffer')
        self.lib.set(c_int, 'rl_point', point)

    @property
    def prompt(self):
        """The prompt readline uses."""
        return self.lib.get(c_char_p, 'rl_prompt')

    def _initreadline(self):
        """See readline.c: PyInit_readline."""
        self.logger.debug('installing readline function pointer')
        call_readline = typedefs.PyOS_ReadlineFunctionPointer_t(
            self._call_readline)
        self.lib.py_cbmanager.install('PyOS_ReadlineFunctionPointer',
                                      call_readline)
        self._setup_readline()

    def _call_readline(self, stdin, stdout, prompt):
        """See readline.c: call_readline."""
        # stdin/stdout will be used eventually
        # pylint: disable=unused-argument
        self.logger.debug('calling readline with prompt: %s', prompt)
        with store_locale():
            self._prep_terminal(stdin, stdout)
            try:
                line = self._readline_until_enter_or_signal(prompt)
            except KeyboardInterrupt:
                return None
            if line is None:
                # We got an EOF; return an empty string
                line = b''
            else:
                if line:
                    if not self.history or line != self.history[-1]:
                        self.logger.debug('adding item to history: %s', line)
                        self.history.append(strings.decode(line))
                line += b'\n'
            self.logger.debug('allocating copy of line: %s', line)
            # line must be allocated with PyMem_Malloc
            size = len(line) + 1
            pythonapi.PyMem_Malloc.restype = c_void_p
            linecopy = pythonapi.PyMem_Malloc(size)
            memmove(linecopy, line, size)
            self.logger.debug('returning copy of line: %s', linecopy)
            return linecopy

    def _prep_terminal(self, stdin, stdout):
        """Prepare the terminal for input.

        This is only a separate function because I need to override
        this behaviour for Windows at the moment.
        """
        if (stdin, stdout) != (self.instream, self.outstream):
            self.instream = stdin
            self.outstream = stdout
            self.lib.rl_prep_terminal(1)

    def _readline_until_enter_or_signal(self, prompt):
        """See readline.c: readline_until_enter_or_signal."""
        # Can't have any solution that allows readline to catch signals
        # because we have no way to catch the SIGINT it raises (or at
        # least I couldn't figure out how).
        self.lib.set(c_bool, 'rl_catch_signals', False)
        rlhandler = typedefs.rl_vcpfunc_t(self._rlhandler)
        self.lib.rl_callback_handler_install(prompt, rlhandler)
        try:
            self._input_complete = False
            while not self._input_complete:
                while True:
                    timeout = None
                    # pylint: disable=no-member
                    input_hook = c_void_p.in_dll(pythonapi, 'PyOS_InputHook')
                    if input_hook:
                        timeout = 0.1
                    if self._select(timeout):
                        break
                    if input_hook:
                        cast(input_hook, typedefs.PyOS_InputHook_t)()
                # An unhandled KeyboardInterrupt in a ctypes callback
                # function (this can call _rlhandler or _attempted_completion)
                # is a bit of a disaster. To be safe, I'm disabling the
                # handling of SIGINT for the duration of this function
                # call. This should return relatively quickly (unless
                # there are an absurd amount of completion options),
                # and I'd rather miss a Ctrl-C than crash.
                with ignore_sigint():
                    self.logger.debug('reading single character')
                    self.lib.rl_callback_read_char()
        except KeyboardInterrupt:
            self.logger.debug('cleaning up after KeyboardInterrupt')
            self.lib.rl_free_line_state()
            self.lib.rl_cleanup_after_signal()
            self.lib.rl_callback_handler_remove()
            raise
        return self._completed_input_string

    def _rlhandler(self, text):
        """See readline.c: rlhandler."""
        self.lib.rl_callback_handler_remove()
        # Get the string value for Python internal use
        self._completed_input_string = cast(text, c_char_p).value
        self.logger.debug('received input line: %s',
                          self._completed_input_string)
        # Free memory allocated by Readline
        self.lib.free(text)
        self._input_complete = True

    def _select(self, timeout=None):
        """Wait for input on stdin, allowing KeyboardInterrupt to
        propagate.

        :param timeout: time in seconds to wait
        :return: True on input, False on timeout
        """
        fileno = self.lib.fileno(self.instream)
        self.logger.debug('calling select with fileno: %d', fileno)
        # Call select, retrying on EINTR.
        while True:
            try:
                return any(select.select([fileno], [], [], timeout))
            except select.error as error:
                if error.args[0] != errno.EINTR:
                    raise

    def _setup_readline(self):
        """See readline.c: setup_readline."""
        with store_locale():
            self.lib.using_history()
            self.name = 'python'
            self.lib.rl_bind_key(b'\t', self.lib.dll.rl_insert)
            self.lib.rl_bind_key_in_map(b'\t', self.lib.dll.rl_complete,
                                        self.lib.dll.emacs_meta_keymap)
            self.lib.rl_bind_key_in_map(b'\033', self.lib.dll.rl_complete,
                                        self.lib.dll.emacs_meta_keymap)
            on_startup_hook = typedefs.rl_hook_func_t(self._on_startup_hook)
            self.lib.cbmanager.install('rl_startup_hook', on_startup_hook)
            on_preinput_hook = typedefs.rl_hook_func_t(self._on_pre_input_hook)
            self.lib.cbmanager.install('rl_pre_input_hook', on_preinput_hook)
            # FUTURE: move to completion's init
            # pylint: disable=protected-access
            attempted_completion = typedefs.rl_completion_func_t(
                self.completion._attempted_completion)
            self.lib.cbmanager.install('rl_attempted_completion_function',
                                       attempted_completion)
            self.lib.rl_initialize()

    def _on_startup_hook(self):
        """See readline.c: on_startup_hook."""
        self.logger.debug('calling startup hook')
        return self._on_hook(self.startup_hook)

    def _on_pre_input_hook(self):
        """See readline.c: on_pre_input_hook."""
        self.logger.debug('calling pre-input hook')
        return self._on_hook(self.pre_input_hook)

    def _on_hook(self, hook):
        """See readline.c: on_hook."""
        if hook:
            try:
                return int(hook() or 0)
            except Exception:  # pylint: disable=broad-except
                self.logger.exception('exception calling hook')
                return -1
        return 0

    def parse_and_bind(self, string):
        """Parse and execute single line of a readline init file."""
        # rl_parse_and_bind modifies its input
        string = strings.encode(string)
        self.logger.debug('string to parse: %s', string)
        cstring = create_string_buffer(string)
        self.lib.rl_parse_and_bind(cstring)

    @property
    def line_buffer(self):
        """Return the current contents of the line buffer."""
        return self.lib.get(c_char_p, 'rl_line_buffer')

    @line_buffer.setter
    def line_buffer(self, string):
        with self.undo_group():
            self.delete_text(0, len(self.line_buffer))
            self.insert_text(string)

    @contextlib.contextmanager
    def undo_group(self):
        """Return a context manager for an undo group.

        Any modifications to the line buffer in the context will be
        recorded as a single undo unit.
        """
        self.lib.rl_begin_undo_group()
        try:
            yield
        finally:
            self.lib.rl_end_undo_group()

    def insert_text(self, text):
        """Insert text into the command line."""
        text = strings.encode(text)
        self.logger.debug('inserting text: %s', text)
        # rl_insert_text fails silently if this is not the case.
        assert self.point <= len(self.line_buffer)
        self.lib.rl_insert_text(text)

    def delete_text(self, start, end):
        """Delete the text between [start, end) in the line.

        If the point is within the region, is is moved to the beginning
        of the region.
        If the point is beyond the region, it is shifted down by the
        size of the region.
        """
        self.logger.debug('deleting text: %s', self.line_buffer[start:end])
        self.lib.rl_delete_text(start, end)
        if start <= self.point <= end:
            # The text surrounds the point; pull the point to start.
            self.point = start
        elif self.point > end:
            # The point is after the text; adjust by amount deleted.
            self.point -= (end - start)

    def read_init_file(self, filename=None):
        """Parse a readline initialization file.

        The default filename is the last filename used.
        """
        if filename is not None:
            # FUTURE: emulate PyUnicode_FSConverter?
            filename = strings.encode(filename)
        self.logger.debug('reading init file: %s', filename)
        error = self.lib.rl_read_init_file(filename)
        if error:
            raise IOError(error)

    def redisplay(self):
        """Change what's displayed on the screen to reflect the current
        contents of the line buffer.
        """
        self.lib.rl_redisplay()

    def forced_update_display(self):
        """Force the line to be updated and redisplayed, whether or
        not Readline thinks the screen display is correct.
        """
        self.lib.rl_forced_update_display()

    def add_function(self, name, function):
        """Add or overwrite a bindable named function. The function
        can be referenced by name in an initialization file or in
        a call to readline.parse_and_bind. The function is called as
        function(count, key) where count is the numeric argument (or 1
        if defaulted) and key is the key that invoked the function.
        The function should return 0 on success or a non-zero value if
        some error occurs.
        """
        name = strings.encode(name)
        # Wrapper functions will retrieve Python functions from this
        # dict by name. Note that this also stores a reference to name
        # so it does not get GC'd.
        self._functions[name] = function
        if name in self._function_wrappers:
            self.logger.debug('function wrapper exists for %s', name)
            return
        self.logger.debug('registering function wrapper for %s', name)
        _wrapper = functools.partial(self._on_function, name)
        wrapper = typedefs.rl_command_func_t(_wrapper)
        # Save off the wrapper so that it doesn't get GC'd and we know
        # not to create it again.
        self._function_wrappers[name] = wrapper
        self.lib.rl_add_defun(name, wrapper, -1)

    def _on_function(self, name, count, key):
        """Call the function registered for name, passing count and key
        as parameters.
        """
        self.logger.debug('calling function for name %s', name)
        try:
            return int(self._functions[name](count, key) or 0)
        except Exception:  # pylint: disable=broad-except
            self.logger.exception('exception in function %s', name)
            return -1


class WindowsReadline(Readline):
    """Python interface to Windows Readline DLL."""
    def _prep_terminal(self, stdin, stdout):
        # FUTURE: These problems may be specific to my Readline DLL,
        # in which case this function can probably be deleted.
        self.lib.rl_prep_terminal(1)
        # Using rl_resize_display here seems to cause the prompt to be
        # printed twice (at least in my DLL). I think it needs to be
        # called after rl_callback_handler_install. Might want to watch
        # https://bugs.python.org/issue23735 and go with a similar
        # solution to what they end up with instead of this (since that
        # will affect Linux too).
        # pylint: disable=protected-access
        self.lib.dll._rl_get_screen_size(0, 1)

    def _select(self, timeout=None):
        # The Windows version of select only deals with sockets, so we
        # have to do this the hard way.
        import msvcrt  # pylint: disable=import-error
        start = time.time()
        while not msvcrt.kbhit():
            time.sleep(0.01)
            if timeout is not None:
                elapsed = time.time() - start
                if elapsed > timeout:
                    return False
        return True

    def _call_readline(self, stdin, stdout, prompt):
        # IPython expects pyreadline to handle ANSI color codes. We can
        # offload most of this work to colorama, but the printing of
        # the prompt happens inside the DLL where we can't get to it.
        # I tried experimenting with printing the prompt myself and
        # using rl_already_prompted, but this has a number of issues:
        #   * IPython has a newline in the prompt which doesn't seem to
        #       be handled well
        #   * This only helps us the first time the prompt is printed;
        #       if Readline updates the display itself (like after
        #       printing completion matches), this doesn't work.
        # Could look into providing our own rl_redisplay_function, but
        # the default rl_redisplay does quite a lot of work, so I'm not
        # game to touch that right now.
        # For now, I'm just stripping the color codes and printing a
        # boring prompt.
        self.logger.debug('stripping prompt: %s', prompt)
        prompt = strings.strip_ansi_from_bytes(prompt)
        self.logger.debug('stripped prompt: %s', prompt)
        return super(WindowsReadline, self)._call_readline(stdin, stdout,
                                                           prompt)

    def read_init_file(self, filename=None):
        try:
            super(WindowsReadline, self).read_init_file(filename)
        except IOError:
            if filename is not None:
                raise
            # This fallback doesn't seem to work properly in my DLL.
            # Should investigate further.
            filename = os.path.expanduser('~/.inputrc')
            return super(WindowsReadline, self).read_init_file(filename)


class History(object):
    """Python interface to Readline history functions."""
    def __init__(self, lib):
        self.lib = lib

        self.logger = logging.getLogger(__name__)

    def __len__(self):
        return self.lib.get(c_int, 'history_length')

    def __getitem__(self, item):
        if item < 0:
            item += len(self)
        if not 0 <= item < len(self):
            raise IndexError('history index out of range')
        entries = self.lib.history_list()
        entry = entries[item]
        return strings.decode(entry[0].line)

    def __setitem__(self, key, value):
        if key < 0:
            key += len(self)
        if not 0 <= key < len(self):
            raise IndexError('history index out of range')
        line = strings.encode(value)
        self.logger.debug('replacing history item: %s', line)
        p_hist_entry = self.lib.replace_history_entry(key, line, None)
        self.lib.free_history_entry(p_hist_entry)

    def __delitem__(self, key):
        if key < 0:
            key += len(self)
        if not 0 <= key < len(self):
            raise IndexError('history index out of range')
        p_hist_entry = self.lib.remove_history(key)
        self.lib.free_history_entry(p_hist_entry)

    def append(self, line):
        """Add a line to the history buffer."""
        line = strings.encode(line)
        self.logger.debug('adding history: %s', line)
        self.lib.add_history(line)

    def clear(self):
        """Clear the current history."""
        self.logger.debug('clearing history')
        self.lib.clear_history()

    @property
    def base(self):
        """Return the value of history_base."""
        return self.lib.get(c_int, 'history_base')

    @property
    def pos(self):
        """Return the offset of the current history element."""
        return self.lib.where_history()

    @pos.setter
    def pos(self, index):
        """Set the history offset."""
        if not self.lib.history_set_pos(index):
            raise IndexError

    def read_file(self, filename=None):
        """Load a readline history file.

        The default filename is ~/.history.
        """
        if filename is not None:
            # FUTURE: emulate PyUnicode_FSConverter?
            filename = strings.encode(filename)
        self.logger.debug('reading history file: %s', filename)
        error = self.lib.read_history(filename)
        if error:
            raise IOError(error)

    def write_file(self, filename=None):
        """Save a readline history file.

        The default filename is ~/.history.
        """
        if filename is not None:
            # FUTURE: emulate PyUnicode_FSConverter?
            filename = strings.encode(filename)
        self.logger.debug('writing history file: %s', filename)
        error = self.lib.write_history(filename)
        if error:
            raise IOError(error)

    def truncate_file(self, lines, filename=None):
        """Truncate the history file.

        The default filename is ~/.history.
        """
        if filename is not None:
            # FUTURE: emulate PyUnicode_FSConverter?
            filename = strings.encode(filename)
        self.logger.debug('truncating history file: %s', filename)
        error = self.lib.history_truncate_file(filename, lines)
        if error:
            raise IOError(error)


class Completion(object):
    """Python interface to Readline completion functions."""
    def __init__(self, lib):
        self.lib = lib

        self.completer = None
        """If not None, this function is called once as
        function(text, start, end), where start and end are indices in
        self.line_buffer defining the boundaries of text, and should
        return an iterable of all possible completions starting with
        text.
        """

        self.logger = logging.getLogger(__name__)

        self._display_matches_hook = None

    @property
    def append_character(self):
        """Character to append to a single completion match."""
        return self.lib.get(c_char, 'rl_completion_append_character')

    @append_character.setter
    def append_character(self, char):
        self.lib.set(c_char, 'rl_completion_append_character', char)

    @property
    def suppress_append(self):
        """If True, do not append append_character."""
        return self.lib.get(c_bool, 'rl_completion_suppress_append')

    @suppress_append.setter
    def suppress_append(self, suppress):
        self.lib.set(c_bool, 'rl_completion_suppress_append', suppress)

    @property
    def word_break_characters(self):
        """Characters that signify a break between words."""
        return self.lib.get(c_char_p, 'rl_completer_word_break_characters')

    @word_break_characters.setter
    def word_break_characters(self, chars):
        self.lib.set(c_char_p, 'rl_completer_word_break_characters', chars)

    @property
    def basic_word_break_characters(self):
        """Basic characters that signify a break between words."""
        return self.lib.get(c_char_p, 'rl_basic_word_break_characters')

    @property
    def type(self):
        """Type of completion being attempted."""
        return self.lib.get(c_char, 'rl_completion_type')

    @property
    def quote_characters(self):
        """Characters used to quote a substring of the line."""
        return self.lib.get(c_char_p, 'rl_completer_quote_characters')

    @quote_characters.setter
    def quote_characters(self, chars):
        self.lib.set(c_char_p, 'rl_completer_quote_characters', chars)

    @property
    def basic_quote_characters(self):
        """Basic characters used to quote a substring of the line."""
        return self.lib.get(c_char_p, 'rl_basic_quote_characters')

    @property
    def filename_quote_characters(self):
        """Characters requiring a filename to be quoted."""
        return self.lib.get(c_char_p, 'rl_filename_quote_characters')

    @filename_quote_characters.setter
    def filename_quote_characters(self, chars):
        self.lib.set(c_char_p, 'rl_filename_quote_characters', chars)

    @property
    def filename_completion_desired(self):
        """If True, the completions are treated as filenames."""
        return self.lib.get(c_bool, 'rl_filename_completion_desired')

    @filename_completion_desired.setter
    def filename_completion_desired(self, desired):
        self.lib.set(c_bool, 'rl_filename_completion_desired', desired)

    def filename_completions(self, text):
        """Return the possible filename completions."""
        text = strings.encode(text)
        completions = []
        while True:
            p_completion = self.lib.rl_filename_completion_function(
                text, len(completions))
            if not p_completion:
                break
            completion = cast(p_completion, c_char_p).value
            completions.append(strings.decode(completion))
            self.lib.free(p_completion)
        return completions

    def _attempted_completion(self, text, start, end):
        """Used as rl_attempted_completion_function."""
        if not self.completer:
            return None

        # Still need to pass text to rl_completion_matches.
        text_decoded = strings.decode(text)
        self.lib.set(c_bool, 'rl_attempted_completion_over', True)

        try:
            # pylint: disable=not-callable
            completions = self.completer(text_decoded, start, end)
        except Exception:  # pylint: disable=broad-except
            self.logger.exception('exception calling completer')
            return None
        else:
            self.logger.debug('completer returned completions %s', completions)

        def _on_completion(dummy, state):
            """Allocate and return a single completion."""
            try:
                completion = completions[state]
            except IndexError:
                return None
            else:
                completion = strings.encode(completion)
                return self.lib.strdup(completion)

        on_completion = typedefs.rl_compentry_func_t(_on_completion)
        return self.lib.rl_completion_matches(text, on_completion)

    @property
    def display_matches_hook(self):
        """Return the completion display function."""
        return self._display_matches_hook

    @display_matches_hook.setter
    def display_matches_hook(self, function):
        """Set or remove the completion display function. If function
        is specified, it will be used as the new completion display
        function; if omitted or None, any completion display function
        already installed is removed. The completion display function
        is called as
        function(substitution, [matches], longest_match_length) once
        each time matches need to be displayed.
        """
        self._display_matches_hook = function
        # This hook replaces the default completion display; only install it
        # when it is required and uninstall it otherwise
        if function:
            display_matches_hook = typedefs.rl_compdisp_func_t(
                self._on_display_matches_hook)
            self.lib.cbmanager.install('rl_completion_display_matches_hook',
                                       display_matches_hook)
        else:
            self.lib.cbmanager.uninstall('rl_completion_display_matches_hook')

    def _on_display_matches_hook(self, matches, num_matches, max_length):
        """See readline.c: on_completion_display_matches_hook."""
        try:
            prefix = matches[0]
            real_matches = [matches[x] for x in range(1, num_matches + 1)]
            self._display_matches_hook(prefix, real_matches,
                                       max_length)
        except Exception:  # pylint: disable=broad-except
            self.logger.exception('exception displaying matches')
