"""Interfaces to Readline DLLs."""
from ctypes import *  # pylint: disable=wildcard-import,unused-wildcard-import
import logging
import msvcrt
import time

from . import callback_mananger
from . import typedefs

SIGINT = 2


class Readline(object):
    """Python interface to Readline DLL."""
    # ctypes gives many false positives for in_dll
    # pylint: disable=no-member
    # modelling this after the C implementation
    # pylint: disable=invalid-name
    # pylint: disable=too-many-public-methods,too-many-instance-attributes
    def __init__(self, dll_name):
        self.dll = cdll.LoadLibrary(dll_name)
        self.rl_cbmanager = callback_mananger.CallbackManager(self.dll)
        self.py_cbmanager = callback_mananger.CallbackManager(pythonapi)
        self._history_length = -1
        self._begidx = 0
        self._endidx = 0
        self._startup_hook = None
        self._pre_input_hook = None
        self._completer = None
        self._completion_display_matches_hook = None
        self._completed_input_string = None
        self._input_complete = False

        # String constant we need to keep a reference to
        self._PYTHON = 'python'

        self._old_inthandler = None

        self.logger = logging.getLogger(__name__)

        self._initreadline()

    def _initreadline(self):
        """See readline.c: PyInit_readline."""
        call_readline = typedefs.PyOS_ReadlineFunctionPointer_t(
            self._call_readline)
        self.py_cbmanager.install('PyOS_ReadlineFunctionPointer',
                                  call_readline)
        self._setup_readline()

    def _call_readline(self, stdin, stdout, prompt):
        """See readline.c: call_readline."""
        # stdin/stdout will be used eventually
        # pylint: disable=unused-argument
        # FUTURE: save/restore locale?
        # FUTURE: this bit is specific to my readline DLL; move into subclass
        # ???: Not sure what the deal is here...
        # I think rl_initialize is supposed to set this but rl_prep_terminal
        # hasn't been called so haveConsole is 0 and the screen defaults to
        # 80x24. It looks like I can only call this while the terminal is
        # prepped. Possibly a bug in this implementation?
        # It looks like the Unix version works by letting readline catch
        # SIGWINCH and update these values automatically. I can't find
        # anywhere in the code that is attempting to do the same for
        # Windows. Calling this function every time we call rl_prep_terminal
        # means that we'll adjust the size every line (which means we can
        # still be out of sync until the user presses enter).
        # FUTURE: investigate rl_resize_display
        self.dll.rl_prep_terminal.argtypes = [c_int]
        self.dll.rl_prep_terminal(1)
        self.dll._rl_get_screen_size(0, 1)  # pylint: disable=protected-access
        try:
            line = self._readline_until_enter_or_signal(prompt)
        except KeyboardInterrupt:
            return None
        if line is None:
            # We got an EOF; return an empty string
            line = ''
        else:
            if line:
                history_length = self.get_current_history_length()
                last = self.get_history_item(history_length)
                if line != last:
                    self.add_history(line)
            line += '\n'
        # line must be allocated with PyMem_Malloc
        size = len(line) + 1
        linecopy = pythonapi.PyMem_Malloc(size)
        cdll.msvcrt.memcpy(linecopy, line, size)
        cdll.msvcrt.free(line)
        return linecopy

    def _readline_until_enter_or_signal(self, prompt):
        """See readline.c: readline_until_enter_or_signal."""
        # can't have any solution that allows readline to catch signals
        # because we have no way to catch the SIGINT it raises (or at
        # least I couldn't figure out how)
        # FUTURE: this should be moved somewhere Windows-specific
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
                    if self._fake_select(timeout):
                        break
                    if input_hook:
                        cast(input_hook, typedefs.PyOS_InputHook_t)()
                self.dll.rl_callback_read_char()
        except KeyboardInterrupt:
            self.dll.rl_free_line_state()
            self.dll.rl_cleanup_after_signal()
            self.dll.rl_callback_handler_remove()
            raise
        return self._completed_input_string

    def _rlhandler(self, text):
        """See readline.c: rlhandler."""
        self.dll.rl_callback_handler_remove()
        self._completed_input_string = text
        self._input_complete = True

    @staticmethod
    def _fake_select(timeout=None):
        """Function to imitate select()

        Poll for keyboard input while also allowing KeyboardInterrupt
        to propagate within the interpreter.

        :param timeout: timeout in seconds, or None for no timeout
        :return: True if input available, False if timeout reached
        """
        start = time.time()
        while not msvcrt.kbhit():
            time.sleep(0.01)
            if timeout is not None:
                elapsed = time.time() - start
                if elapsed > timeout:
                    return False
        return True

    def _setup_readline(self):
        """See readline.c: setup_readline."""
        self.dll.using_history()
        c_char_p.in_dll(self.dll, 'rl_readline_name').value = self._PYTHON
        cdll.msvcrt.getenv.argtypes = [c_char_p]
        # don't automatically convert return type
        cdll.msvcrt.getenv.restype = c_void_p
        term = cdll.msvcrt.getenv('TERM')
        c_char_p.in_dll(self.dll, 'rl_terminal_name').value = term
        self.parse_and_bind('tab: tab-insert')
        self.dll.rl_bind_key_in_map.argtypes = [c_char, c_void_p, c_void_p]
        self.dll.rl_bind_key_in_map('\t', self.dll.rl_complete,
                                    self.dll.emacs_meta_keymap)
        self.dll.rl_bind_key_in_map('\033', self.dll.rl_complete,
                                    self.dll.emacs_meta_keymap)
        on_startup_hook = typedefs.rl_hook_func_t(self._on_startup_hook)
        self.rl_cbmanager.install('rl_startup_hook', on_startup_hook)
        on_pre_input_hook = typedefs.rl_hook_func_t(self._on_pre_input_hook)
        self.rl_cbmanager.install('rl_pre_input_hook', on_pre_input_hook)
        flex_complete = typedefs.rl_completion_func_t(self._flex_complete)
        self.rl_cbmanager.install('rl_attempted_completion_function',
                                  flex_complete)
        self.set_completer_delims(" \t\n`~!@#$%^&*()-=+[{]}\\|;:'\",<>/?")
        self.dll.rl_initialize()

    def _on_startup_hook(self):
        """See readline.c: on_startup_hook."""
        return self._on_hook(self._startup_hook)

    def _on_pre_input_hook(self):
        """See readline.c: on_pre_input_hook."""
        return self._on_hook(self._pre_input_hook)

    @staticmethod
    def _on_hook(hook):
        """See readline.c: on_hook."""
        if hook:
            try:
                return hook()
            except Exception:  # pylint: disable=broad-except
                return -1
        return 0

    def _flex_complete(self, text, start, end):
        """See readline.c: flex_complete."""
        c_char.in_dll(self.dll, 'rl_completion_append_character').value = '\0'
        c_int.in_dll(self.dll, 'rl_completion_suppress_append').value = 0
        self._begidx = start
        self._endidx = end
        on_completion = typedefs.rl_compentry_func_t(self._on_completion)
        return self.dll.rl_completion_matches(text, on_completion)

    def _on_completion(self, text, state):
        """See readline.c: on_completion."""
        if self._completer:
            c_int.in_dll(self.dll, 'rl_attempted_completion_over').value = 1
            try:
                result = self._completer(text, state)
                return self._strdup(result)
            except Exception:  # pylint: disable=broad-except
                pass
        return None

    def parse_and_bind(self, string):
        """Parse and execute single line of a readline init file."""
        # rl_parse_and_bind modifies its input
        cstring = create_string_buffer(string)
        self.dll.argtypes = [c_char_p]
        self.dll.rl_parse_and_bind(cstring)

    def get_line_buffer(self):
        """Return the current contents of the line buffer."""
        return c_char_p.in_dll(self.dll, 'rl_line_buffer').value

    def insert_text(self, text):
        """Insert text into the command line."""
        self.dll.rl_insert_text.argtypes = [c_char_p]
        self.dll.rl_insert_text(text)

    def read_init_file(self, filename=None):
        """Parse a readline initialization file. The default filename
        is the last filename used.
        """
        self.dll.rl_read_init_file.argtypes = [c_char_p]
        self.dll.rl_read_init_file.restype = c_int
        errno = self.dll.rl_read_init_file(filename)
        if errno:
            raise IOError(errno)

    def read_history_file(self, filename=None):
        """Load a readline history file. The default filename is
        ~/.history.
        """
        self.dll.read_history.argtypes = [c_char_p]
        self.dll.read_history.restype = c_int
        errno = self.dll.read_history(filename)
        if errno:
            raise IOError(errno)

    def write_history_file(self, filename=None):
        """Save a readline history file. The default filename is
        ~/.history.
        """
        self.dll.write_history.argtypes = [c_char_p]
        self.dll.write_history.restype = c_int
        errno = self.dll.write_history(filename)
        if errno:
            raise IOError(errno)
        if self._history_length >= 0:
            self.dll.history_truncate_file.argtypes = [c_char_p, c_int]
            self.dll.history_truncate_file(filename, self._history_length)

    def clear_history(self):
        """Clear the current history."""
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
        line = None
        if p_hist_entry:
            line = p_hist_entry[0].line
        return line

    def remove_history_item(self, pos):
        """Remove history item specified by its position from the
        history.
        """
        if pos < 0:
            raise ValueError('History index cannot be negative')
        self.dll.remove_history.argtypes = [c_int]
        self.dll.remove_history.restype = POINTER(typedefs.HIST_ENTRY)
        p_hist_entry = self.dll.remove_history(pos)
        if p_hist_entry is None:
            raise ValueError('No history item at position {}'.format(pos))
        self._free_hist_entry(p_hist_entry)

    def replace_history_item(self, pos, line):
        """Replace history item specified by its position with the
        given line.
        """
        if pos < 0:
            raise ValueError('History index cannot be negative')
        self.dll.replace_history.argtypes = [c_int, c_int, c_void_p]
        self.dll.replace_history.restype = POINTER(typedefs.HIST_ENTRY)
        p_hist_entry = self.dll.replace_history_entry(pos, line, None)
        if p_hist_entry is None:
            raise ValueError('No history item at position {}'.format(pos))
        self._free_hist_entry(p_hist_entry)

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

    def set_completer(self, func):
        """Set or remove the completer function. If function is
        specified, it will be used as the new completer function; if
        omitted or None, any completer function already installed is
        removed. The completer function is called as
        function(text, state), for state in 0, 1, 2, ..., until it
        returns a non-string value. It should return the next possible
        completion starting with text.
        """
        self._completer = func

    def get_completer(self):
        """Get the completer function, or None if no completer function
        has been set.
        """
        return self._completer

    def get_completion_type(self):
        """Get the type of completion being attempted."""
        return c_char.in_dll(self.dll, 'rl_completion_type').value

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
        p_characters = c_char_p.in_dll(self.dll,
                                       'rl_completer_word_break_characters')
        self._free(p_characters)
        # need to strdup so it can be freed
        p_characters.value = self._strdup(string)

    def get_completer_delims(self):
        """Get the readline word delimiters for tab-completion."""
        return c_char_p.in_dll(self.dll,
                               'rl_completer_word_break_characters').value

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
            pass

    def add_history(self, line):
        """Append a line to the history buffer, as if it was the last
        line typed.
        """
        self.dll.add_history.argtypes = [c_char_p]
        self.dll.add_history(line)

    @staticmethod
    def _malloc(size):
        """Allocate memory and return its address."""
        cdll.msvcrt.malloc.argtypes = [c_size_t]
        cdll.msvcrt.malloc.restype = c_void_p
        return cdll.msvcrt.malloc(size)

    def _free(self, p_memory):  # pylint: disable=no-self-use
        """Free memory allocated with malloc."""
        cdll.msvcrt.free.argtypes = [c_void_p]
        cdll.msvcrt.free(p_memory)

    def _strdup(self, string):
        """Return the *address of* a copy of the string."""
        size = len(string) + 1
        dup = self._malloc(size)
        cdll.msvcrt.memcpy.argtypes = [c_void_p, c_void_p, c_size_t]
        cdll.msvcrt.memcpy(dup, string, size)
        return dup

    def _free_hist_entry(self, p_hist_entry):
        """Free the memory allocated for the HIST_ENTRY structure"""
        if not p_hist_entry:
            return
        hist_entry = p_hist_entry[0]
        if hist_entry.line:
            self._free(hist_entry.line)
        if hist_entry.data:
            self._free(hist_entry.data)
        self._free(p_hist_entry)
