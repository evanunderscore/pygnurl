"""Low-level interface to Readline API."""
from ctypes import *  # pylint: disable=wildcard-import,unused-wildcard-import

from . import callback_mananger
from . import strings
from . import typedefs


class Bindings(object):  # pylint: disable=too-many-instance-attributes
    """Low-level bindings to Readline shared library."""
    def __init__(self, dll):
        self.dll = dll
        self.cbmanager = callback_mananger.CallbackManager(self.dll)
        self.py_cbmanager = callback_mananger.CallbackManager(pythonapi)

        self._strings = {}

        self._init_functions()

    def get(self, c_type, name):
        """Get a value of the given type from the shared library."""
        value = c_type.in_dll(self.dll, name).value
        if c_type in [c_char, c_char_p] and value is not None:
            value = strings.decode(value)
        return value

    def set(self, c_type, name, value):
        """Set a value of the given type in the shared library."""
        if c_type in [c_char, c_char_p] and value is not None:
            value = strings.encode(value)
            self._strings[name] = value
        c_type.in_dll(self.dll, name).value = value

    def malloc(self, size):
        """Allocate memory and return its address."""
        try:
            malloc = self.dll.xmalloc
        except AttributeError:
            malloc = self.dll.malloc
        malloc.argtypes = [c_size_t]
        malloc.restype = c_void_p
        return malloc(size)

    def free(self, p_memory):
        """Free memory allocated with malloc."""
        try:
            free = self.dll.xfree
        except AttributeError:
            free = self.dll.free
        free.argtypes = [c_void_p]
        free(p_memory)

    def strdup(self, string):
        """Return the *address of* a copy of the string."""
        size = len(string) + 1
        dup = self.malloc(size)
        memmove(dup, string, size)
        return dup

    def _init_functions(self):
        """Add functions from the shared library to this object.

        All functions will have their argument and return types set
        appropriately.
        """
        self.rl_prep_terminal = self._get_c_func(
            'rl_prep_terminal', [c_int], None)
        self.rl_callback_handler_install = self._get_c_func(
            'rl_callback_handler_install', [c_char_p, typedefs.rl_vcpfunc_t],
            None)
        self.rl_callback_read_char = self._get_c_func(
            'rl_callback_read_char', [], None)
        self.rl_free_line_state = self._get_c_func(
            'rl_free_line_state', [], None)
        self.rl_cleanup_after_signal = self._get_c_func(
            'rl_cleanup_after_signal', [], None)
        self.rl_callback_handler_remove = self._get_c_func(
            'rl_callback_handler_remove', [], None)

        self.using_history = self._get_c_func(
            'using_history', [], None)
        self.rl_bind_key = self._get_c_func(
            'rl_bind_key', [c_char, c_void_p], c_int)
        self.rl_bind_key_in_map = self._get_c_func(
            'rl_bind_key_in_map', [c_char, c_void_p, c_void_p], c_int)
        self.rl_initialize = self._get_c_func(
            'rl_initialize', [], c_int)
        self.rl_parse_and_bind = self._get_c_func(
            'rl_parse_and_bind', [c_char_p], c_int)
        self.rl_insert_text = self._get_c_func(
            'rl_insert_text', [c_char_p], c_int)
        self.rl_read_init_file = self._get_c_func(
            'rl_read_init_file', [c_char_p], c_int)
        self.rl_redisplay = self._get_c_func(
            'rl_redisplay', [], c_int)
        self.rl_forced_update_display = self._get_c_func(
            'rl_forced_update_display', [], c_int)
        self.rl_add_defun = self._get_c_func(
            'rl_add_defun', [c_char_p, c_void_p, c_int], c_int)

        self.history_list = self._get_c_func(
            'history_list', [], POINTER(POINTER(typedefs.HIST_ENTRY)))
        self.replace_history_entry = self._get_c_func(
            'replace_history_entry', [c_int, c_char_p, c_void_p],
            POINTER(typedefs.HIST_ENTRY))
        self.free_history_entry = self._get_c_func(
            'free_history_entry', [POINTER(typedefs.HIST_ENTRY)], c_void_p)
        self.remove_history = self._get_c_func(
            'remove_history', [c_int], POINTER(typedefs.HIST_ENTRY))
        self.add_history = self._get_c_func(
            'add_history', [c_char_p], None)
        self.clear_history = self._get_c_func(
            'clear_history', [], None)
        self.where_history = self._get_c_func(
            'where_history', [], c_int)
        self.history_set_pos = self._get_c_func(
            'history_set_pos', [c_int], c_int)
        self.read_history = self._get_c_func(
            'read_history', [c_char_p], c_int)
        self.write_history = self._get_c_func(
            'write_history', [c_char_p], c_int)
        self.history_truncate_file = self._get_c_func(
            'history_truncate_file', [c_char_p, c_int], c_int)

        self.rl_filename_completion_function = self._get_c_func(
            'rl_filename_completion_function', [c_char_p, c_int], c_void_p)
        self.rl_completion_matches = self._get_c_func(
            'rl_completion_matches', [c_char_p, typedefs.rl_compentry_func_t],
            c_void_p)

        self.rl_begin_undo_group = self._get_c_func(
            'rl_begin_undo_group', [], c_int)
        self.rl_end_undo_group = self._get_c_func(
            'rl_end_undo_group', [], c_int)
        self.rl_delete_text = self._get_c_func(
            'rl_delete_text', [c_int, c_int], c_int)

        # Won't work on Windows, but shouldn't be accessed anyway.
        try:
            self.fileno = self._get_c_func(
                'fileno', [c_void_p], c_int)
        except AttributeError:
            pass

    def _get_c_func(self, name, argtypes, restype):
        """Get a configured function from the shared library."""
        func = getattr(self.dll, name)
        func.argtypes = argtypes
        func.restype = restype
        return func
