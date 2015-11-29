"""Interfaces to Readline DLLs."""
from __future__ import unicode_literals

import contextlib
from ctypes import *  # pylint: disable=wildcard-import,unused-wildcard-import
import errno
import locale
import logging
import select
import signal
import time

from . import callback_mananger
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


# ctypes gives many false positives for in_dll
# pylint: disable=no-member


class Readline(object):
    """Python interface to Readline library."""
    # modelling this after the C implementation
    # pylint: disable=invalid-name
    # pylint: disable=too-many-public-methods,too-many-instance-attributes
    def __init__(self, dll_name):
        self.dll = cdll.LoadLibrary(dll_name)
        self.rl_cbmanager = callback_mananger.CallbackManager(self.dll)
        self.py_cbmanager = callback_mananger.CallbackManager(pythonapi)
        self._READLINE_VERSION = None
        self._READLINE_RUNTIME_VERSION = None
        self._history_length = -1
        self._begidx = 0
        self._endidx = 0
        self._startup_hook = None
        self._pre_input_hook = None
        self._completer = None
        self._completion_display_matches_hook = None
        self._completed_input_string = None
        self._input_complete = False
        self._completer_delims = None

        # String constant we need to keep a reference to
        self._PYTHON = b'python'

        self.logger = logging.getLogger(__name__)

        self._initreadline()

    def _initreadline(self):
        """See readline.c: PyInit_readline."""
        self.logger.debug('installing readline function pointer')
        call_readline = typedefs.PyOS_ReadlineFunctionPointer_t(
            self._call_readline)
        self.py_cbmanager.install('PyOS_ReadlineFunctionPointer',
                                  call_readline)
        self._setup_readline()
        version = c_int.in_dll(self.dll, 'rl_readline_version').value
        self._READLINE_VERSION = version
        self._READLINE_RUNTIME_VERSION = version
        self.logger.debug('readline version: 0x%x', version)

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
                    history_length = self.get_current_history_length()
                    last = self.get_history_item(history_length)
                    self.logger.debug('previous history item: %s', last)
                    if line != last:
                        self.logger.debug('adding item to history: %s', line)
                        self.dll.add_history(line)
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
        instream = c_void_p.in_dll(self.dll, 'rl_instream')
        outstream = c_void_p.in_dll(self.dll, 'rl_outstream')
        if (stdin, stdout) != (instream.value, outstream.value):
            instream.value = stdin
            outstream.value = stdout
            self.dll.rl_prep_terminal.argtypes = [c_int]
            self.dll.rl_prep_terminal(1)

    def _readline_until_enter_or_signal(self, prompt):
        """See readline.c: readline_until_enter_or_signal."""
        # Can't have any solution that allows readline to catch signals
        # because we have no way to catch the SIGINT it raises (or at
        # least I couldn't figure out how).
        c_int.in_dll(self.dll, 'rl_catch_signals').value = 0
        rlhandler = typedefs.rl_vcpfunc_t(self._rlhandler)
        self.dll.rl_callback_handler_install.argtypes = [c_char_p,
                                                         typedefs.rl_vcpfunc_t]
        self.dll.rl_callback_handler_install(prompt, rlhandler)
        try:
            self._input_complete = False
            while not self._input_complete:
                while True:
                    timeout = None
                    input_hook = c_void_p.in_dll(pythonapi, 'PyOS_InputHook')
                    if input_hook:
                        timeout = 0.1
                    if self._select(timeout):
                        break
                    if input_hook:
                        cast(input_hook, typedefs.PyOS_InputHook_t)()
                # An unhandled KeyboardInterrupt in a ctypes callback
                # function (this can call _rlhandler or _flex_complete)
                # is a bit of a disaster. To be safe, I'm disabling the
                # handling of SIGINT for the duration of this function
                # call. This should return relatively quickly (unless
                # there are an absurd amount of completion options),
                # and I'd rather miss a Ctrl-C than crash.
                with ignore_sigint():
                    self.logger.debug('reading single character')
                    self.dll.rl_callback_read_char()
        except KeyboardInterrupt:
            self.logger.debug('cleaning up after KeyboardInterrupt')
            self.dll.rl_free_line_state()
            self.dll.rl_cleanup_after_signal()
            self.dll.rl_callback_handler_remove()
            raise
        return self._completed_input_string

    def _rlhandler(self, text):
        """See readline.c: rlhandler."""
        self.dll.rl_callback_handler_remove()
        # Get the string value for Python internal use
        self._completed_input_string = cast(text, c_char_p).value
        self.logger.debug('received input line: %s',
                          self._completed_input_string)
        # Free memory allocated by Readline
        self._free(text)
        self._input_complete = True

    def _select(self, timeout=None):
        """Wait for input on stdin, allowing KeyboardInterrupt to
        propagate.

        :param timeout: time in seconds to wait
        :return: True on input, False on timeout
        """
        instream = c_void_p.in_dll(self.dll, 'rl_instream').value
        self.dll.fileno.argtypes = [c_void_p]
        self.dll.fileno.restype = c_int
        fileno = self.dll.fileno(instream)
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
            self.dll.using_history()
            c_char_p.in_dll(self.dll, 'rl_readline_name').value = self._PYTHON
            self.dll.rl_bind_key.argtypes = [c_char, c_void_p]
            self.dll.rl_bind_key(b'\t', self.dll.rl_insert)
            self.dll.rl_bind_key_in_map.argtypes = [c_char, c_void_p, c_void_p]
            self.dll.rl_bind_key_in_map(b'\t', self.dll.rl_complete,
                                        self.dll.emacs_meta_keymap)
            self.dll.rl_bind_key_in_map(b'\033', self.dll.rl_complete,
                                        self.dll.emacs_meta_keymap)
            on_startup_hook = typedefs.rl_hook_func_t(self._on_startup_hook)
            self.rl_cbmanager.install('rl_startup_hook', on_startup_hook)
            on_preinput_hook = typedefs.rl_hook_func_t(self._on_pre_input_hook)
            self.rl_cbmanager.install('rl_pre_input_hook', on_preinput_hook)
            flex_complete = typedefs.rl_completion_func_t(self._flex_complete)
            self.rl_cbmanager.install('rl_attempted_completion_function',
                                      flex_complete)
            self.set_completer_delims(" \t\n`~!@#$%^&*()-=+[{]}\\|;:'\",<>/?")
            self.dll.rl_initialize()

    def _on_startup_hook(self):
        """See readline.c: on_startup_hook."""
        self.logger.debug('calling startup hook')
        return self._on_hook(self._startup_hook)

    def _on_pre_input_hook(self):
        """See readline.c: on_pre_input_hook."""
        self.logger.debug('calling pre-input hook')
        return self._on_hook(self._pre_input_hook)

    def _on_hook(self, hook):
        """See readline.c: on_hook."""
        if hook:
            try:
                return int(hook())
            except Exception:  # pylint: disable=broad-except
                self.logger.debug('exception in hook')
                return -1
        return 0

    def _flex_complete(self, text, start, end):
        """See readline.c: flex_complete."""
        c_char.in_dll(self.dll, 'rl_completion_append_character').value = b'\0'
        c_int.in_dll(self.dll, 'rl_completion_suppress_append').value = 0
        self._begidx = start
        self._endidx = end
        on_completion = typedefs.rl_compentry_func_t(self._on_completion)
        self.logger.debug('calling completion matches: %s', text)
        self.dll.rl_completion_matches.argtypes = \
            [c_char_p, typedefs.rl_compentry_func_t]
        self.dll.rl_completion_matches.restype = c_void_p
        return self.dll.rl_completion_matches(text, on_completion)

    def _on_completion(self, text, state):
        """See readline.c: on_completion."""
        if self._completer:
            c_int.in_dll(self.dll, 'rl_attempted_completion_over').value = 1
            try:
                text = strings.decode(text)
                self.logger.debug('calling completer: %s, %d', text, state)
                result = self._completer(text, state)
                if result is None:
                    self.logger.debug('completer returned None')
                    return None
                result = strings.encode(result)
                self.logger.debug('returning completion: %s', result)
                return self._strdup(result)
            except Exception:  # pylint: disable=broad-except
                self.logger.debug('exception calling completer')
        return None

    def parse_and_bind(self, string):
        """Parse and execute single line of a readline init file."""
        # rl_parse_and_bind modifies its input
        string = strings.encode(string)
        self.logger.debug('string to parse: %s', string)
        cstring = create_string_buffer(string)
        self.dll.argtypes = [c_char_p]
        self.dll.rl_parse_and_bind(cstring)

    def get_line_buffer(self):
        """Return the current contents of the line buffer."""
        line_buffer = c_char_p.in_dll(self.dll, 'rl_line_buffer').value
        return strings.decode(line_buffer)

    def insert_text(self, text):
        """Insert text into the command line."""
        text = strings.encode(text)
        self.logger.debug('inserting text: %s', text)
        self.dll.rl_insert_text.argtypes = [c_char_p]
        self.dll.rl_insert_text(text)

    def read_init_file(self, filename=None):
        """Parse a readline initialization file. The default filename
        is the last filename used.
        """
        if filename is not None:
            # FUTURE: emulate PyUnicode_FSConverter?
            filename = strings.encode(filename)
        self.logger.debug('reading init file: %s', filename)
        self.dll.rl_read_init_file.argtypes = [c_char_p]
        self.dll.rl_read_init_file.restype = c_int
        error = self.dll.rl_read_init_file(filename)
        if error:
            raise IOError(error)

    def read_history_file(self, filename=None):
        """Load a readline history file. The default filename is
        ~/.history.
        """
        if filename is not None:
            # FUTURE: emulate PyUnicode_FSConverter?
            filename = strings.encode(filename)
        self.logger.debug('reading history file: %s', filename)
        self.dll.read_history.argtypes = [c_char_p]
        self.dll.read_history.restype = c_int
        error = self.dll.read_history(filename)
        if error:
            raise IOError(error)

    def write_history_file(self, filename=None):
        """Save a readline history file. The default filename is
        ~/.history.
        """
        if filename is not None:
            # FUTURE: emulate PyUnicode_FSConverter?
            filename = strings.encode(filename)
        self.logger.debug('writing history file: %s', filename)
        self.dll.write_history.argtypes = [c_char_p]
        self.dll.write_history.restype = c_int
        error = self.dll.write_history(filename)
        if error:
            raise IOError(error)
        if self._history_length >= 0:
            self.logger.debug('truncating history file')
            self.dll.history_truncate_file.argtypes = [c_char_p, c_int]
            self.dll.history_truncate_file(filename, self._history_length)

    def clear_history(self):
        """Clear the current history."""
        self.logger.debug('clearing history')
        self.dll.clear_history()

    def get_history_length(self):
        """Return the desired length of the history file. Negative
        values imply unlimited history file size.
        """
        return self._history_length

    def set_history_length(self, length):
        """Set the number of lines to save in the history file.
        write_history_file() uses this value to truncate the history
        file when saving. Negative values imply unlimited history file
        size.
        """
        self._history_length = length

    def get_current_history_length(self):
        """Return the number of lines currently in the history. (This
        is different from get_history_length(), which returns the
        maximum number of lines that will be written to a history
        file.)
        """
        return c_int.in_dll(self.dll, 'history_length').value

    def get_history_item(self, index):
        """Return the current contents of history item at index."""
        self.dll.history_get.argtypes = [c_int]
        self.dll.history_get.restype = POINTER(typedefs.HIST_ENTRY)
        p_hist_entry = self.dll.history_get(index)
        if p_hist_entry:
            return strings.decode(p_hist_entry[0].line)
        else:
            return None

    def remove_history_item(self, pos):
        """Remove history item specified by its position from the
        history.
        """
        if pos < 0:
            raise ValueError('History index cannot be negative')
        self.dll.remove_history.argtypes = [c_int]
        self.dll.remove_history.restype = POINTER(typedefs.HIST_ENTRY)
        p_hist_entry = self.dll.remove_history(pos)
        if not p_hist_entry:
            raise ValueError('No history item at position {}'.format(pos))
        self.dll.free_history_entry.argtypes = [POINTER(typedefs.HIST_ENTRY)]
        self.dll.free_history_entry(p_hist_entry)

    def replace_history_item(self, pos, line):
        """Replace history item specified by its position with the
        given line.
        """
        line = strings.encode(line)
        self.logger.debug('replacing history item: %s', line)
        if pos < 0:
            raise ValueError('History index cannot be negative')
        self.dll.replace_history_entry.argtypes = [c_int, c_char_p, c_void_p]
        self.dll.replace_history_entry.restype = POINTER(typedefs.HIST_ENTRY)
        p_hist_entry = self.dll.replace_history_entry(pos, line, None)
        if not p_hist_entry:
            raise ValueError('No history item at position {}'.format(pos))
        self.dll.free_history_entry.argtypes = [POINTER(typedefs.HIST_ENTRY)]
        self.dll.free_history_entry(p_hist_entry)

    def redisplay(self, force=False):
        """Change what's displayed on the screen to reflect the current
        contents of the line buffer.
        """
        # added force flag to call rl_forced_update_display instead because
        # rl_redisplay doesn't seem to do anything for me
        if force:
            self.dll.rl_forced_update_display()
        else:
            self.dll.rl_redisplay()

    def set_startup_hook(self, function=None):
        """Set or remove the startup_hook function. If function is
        specified, it will be used as the new startup_hook function; if
        omitted or None, any hook function already installed is
        removed. The startup_hook function is called with no arguments
        just before readline prints the first prompt.
        """
        self._startup_hook = function

    def set_pre_input_hook(self, function=None):
        """Set or remove the pre_input_hook function. If function is
        specified, it will be used as the new pre_input_hook function;
        if omitted or None, any hook function already installed is
        removed. The pre_input_hook function is called with no
        arguments after the first prompt has been printed and just
        before readline starts reading input characters."""
        self._pre_input_hook = function

    def set_completer(self, function=None):
        """Set or remove the completer function. If function is
        specified, it will be used as the new completer function; if
        omitted or None, any completer function already installed is
        removed. The completer function is called as
        function(text, state), for state in 0, 1, 2, ..., until it
        returns a non-string value. It should return the next possible
        completion starting with text.
        """
        self._completer = function

    def get_completer(self):
        """Get the completer function, or None if no completer function
        has been set.
        """
        return self._completer

    def get_completion_type(self):
        """Get the type of completion being attempted."""
        completion_type = c_char.in_dll(self.dll, 'rl_completion_type').value
        return strings.decode(completion_type)

    def get_begidx(self):
        """Get the beginning index of the readline tab-completion
        scope.
        """
        return self._begidx

    def get_endidx(self):
        """Get the ending index of the readline tab-completion scope."""
        return self._endidx

    def set_completer_delims(self, string):
        """Set the readline word delimiters for tab-completion."""
        string = strings.encode(string)
        self.logger.debug('setting completer delims: %s', string)
        # Store a reference so this doesn't get GC'd.
        self._completer_delims = string
        c_char_p.in_dll(self.dll,
                        'rl_completer_word_break_characters').value = string

    def get_completer_delims(self):
        """Get the readline word delimiters for tab-completion."""
        delims = c_char_p.in_dll(self.dll,
                                 'rl_completer_word_break_characters').value
        return strings.decode(delims)

    def set_completion_display_matches_hook(self, function=None):
        """Set or remove the completion display function. If function
        is specified, it will be used as the new completion display
        function; if omitted or None, any completion display function
        already installed is removed. The completion display function
        is called as
        function(substitution, [matches], longest_match_length) once
        each time matches need to be displayed.
        """
        self._completion_display_matches_hook = function
        # This hook replaces the default completion display; only install it
        # when it is required and uninstall it otherwise
        if function:
            completion_display_matches_hook = typedefs.rl_compdisp_func_t(
                self._on_completion_display_matches_hook)
            self.rl_cbmanager.install('rl_completion_display_matches_hook',
                                      completion_display_matches_hook)
        else:
            self.rl_cbmanager.uninstall('rl_completion_display_matches_hook')

    def _on_completion_display_matches_hook(self, matches, num_matches,
                                            max_length):
        """See readline.c: on_completion_display_matches_hook."""
        try:
            prefix = matches[0]
            real_matches = [matches[x] for x in range(1, num_matches + 1)]
            self._completion_display_matches_hook(prefix, real_matches,
                                                  max_length)
        except Exception:  # pylint: disable=broad-except
            self.logger.debug('exception displaying matches')

    def add_history(self, line):
        """Append a line to the history buffer, as if it was the last
        line typed.
        """
        line = strings.encode(line)
        self.logger.debug('adding history: %s', line)
        self.dll.add_history.argtypes = [c_char_p]
        self.dll.add_history(line)

    def _malloc(self, size):
        """Allocate memory and return its address."""
        try:
            malloc = self.dll.xmalloc
        except AttributeError:
            malloc = self.dll.malloc
        malloc.argtypes = [c_size_t]
        malloc.restype = c_void_p
        return malloc(size)

    def _free(self, p_memory):  # pylint: disable=no-self-use
        """Free memory allocated with malloc."""
        try:
            free = self.dll.xfree
        except AttributeError:
            free = self.dll.free
        free.argtypes = [c_void_p]
        free(p_memory)

    def _strdup(self, string):
        """Return the *address of* a copy of the string."""
        size = len(string) + 1
        dup = self._malloc(size)
        memmove(dup, string, size)
        return dup


class WindowsReadline(Readline):
    """Python interface to Windows Readline DLL."""
    def _prep_terminal(self, stdin, stdout):
        # FUTURE: These problems may be specific to my Readline DLL,
        # in which case this function can probably be deleted.
        self.dll.rl_prep_terminal.argtypes = [c_int]
        self.dll.rl_prep_terminal(1)
        # Using rl_resize_display here seems to cause the prompt to be
        # printed twice (at least in my DLL). I think it needs to be
        # called after rl_callback_handler_install. Might want to watch
        # https://bugs.python.org/issue23735 and go with a similar
        # solution to what they end up with instead of this (since that
        # will affect Linux too).
        self.dll._rl_get_screen_size(0, 1)  # pylint: disable=protected-access

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
