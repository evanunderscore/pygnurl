"""C function and structure typedefs"""
from ctypes import *  # pylint: disable=wildcard-import,unused-wildcard-import

# pylint: disable=invalid-name

# Python
# ------

# char * call_readline(FILE *sys_stdin, FILE *sys_stdout, char *prompt)
PyOS_ReadlineFunctionPointer_t = CFUNCTYPE(c_char_p, c_void_p, c_void_p,
                                           c_char_p)

# ???
PyOS_InputHook_t = CFUNCTYPE(None)

# Readline
# --------

# typedef char *rl_compentry_func_t PARAMS((const char *, int));
rl_compentry_func_t = CFUNCTYPE(c_char_p, c_char_p, c_int)

# typedef char **rl_completion_func_t PARAMS((const char *, int, int));
# Python won't let us return POINTER(c_char_p) from a callback function
rl_completion_func_t = CFUNCTYPE(c_void_p, c_char_p, c_int, c_int)

# typedef int rl_hook_func_t PARAMS((void));
rl_hook_func_t = CFUNCTYPE(c_int)

# typedef void rl_compdisp_func_t PARAMS((char **, int, int));
rl_compdisp_func_t = CFUNCTYPE(None, POINTER(c_char_p), c_int, c_int)

# typedef void rl_vcpfunc_t PARAMS((char *));
rl_vcpfunc_t = CFUNCTYPE(None, c_char_p)


class HIST_ENTRY(Structure):  # pylint: disable=too-few-public-methods
    """The structure used to store a history entry.

    typedef struct _hist_entry {
      char *line;
      char *timestamp;
      histdata_t data;
    } HIST_ENTRY;
    """
    _fields_ = [('line', c_char_p),
                ('timestamp', c_char_p),
                ('data', c_void_p)]
