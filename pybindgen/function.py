"""
C function wrapper
"""

from copy import copy

from typehandlers.base import ForwardWrapperBase, ReturnValue
from typehandlers import codesink
import overloading
import settings
import utils
import warnings
import traceback

class Function(ForwardWrapperBase):
    """
    Class that generates a wrapper to a C function.
    """

    def __init__(self, function_name, return_value, parameters, docstring=None, unblock_threads=None,
                 template_parameters=(), custom_name=None, deprecated=False, foreign_cpp_namespace=None):
        """
        @param function_name: name of the C function
        @param return_value: the function return value
        @type return_value: L{ReturnValue}
        @param parameters: the function parameters
        @type parameters: list of L{Parameter}
        @param deprecated: deprecation state for this API:
          - False: Not deprecated
          - True: Deprecated
          - "message": Deprecated, and deprecation warning contains the given message
        @param foreign_cpp_namespace: if set, the function is assumed to
        belong to the given C++ namespace, regardless of the C++
        namespace of the python module it will be added to.
        """
        self.stack_where_defined = traceback.extract_stack()

        if unblock_threads is None:
            unblock_threads = settings.unblock_threads
        
        ## backward compatibility check
        if isinstance(return_value, str) and isinstance(function_name, ReturnValue):
            warnings.warn("Function has changed API; see the API documentation (but trying to correct...)",
                          DeprecationWarning, stacklevel=2)
            function_name, return_value = return_value, function_name
            
        if return_value is None:
            return_value = ReturnValue.new('void')

        return_value = utils.eval_retval(return_value, self)
        parameters = [utils.eval_param(param, self) for param in parameters]

        super(Function, self).__init__(
            return_value, parameters,
            parse_error_return="return NULL;",
            error_return="return NULL;",
            unblock_threads=unblock_threads)
        self.deprecated = deprecated
        self.foreign_cpp_namespace = foreign_cpp_namespace
        self._module = None
        function_name = utils.ascii(function_name)
        self.function_name = function_name
        self.wrapper_base_name = None
        self.wrapper_actual_name = None
        self.docstring = docstring
        self.self_parameter_pystruct = None
        self.template_parameters = template_parameters
        self.custom_name = custom_name
        self.mangled_name = utils.get_mangled_name(function_name, self.template_parameters)

    def clone(self):
        """Creates a semi-deep copy of this function wrapper.  The returned
        function wrapper clone contains copies of all parameters, so
        they can be modified at will.
        """
        func = Function(self.function_name,
                        self.return_value,
                        [copy(param) for param in self.parameters],
                        docstring=self.docstring)
        func._module = self._module
        func.wrapper_base_name = self.wrapper_base_name
        func.wrapper_actual_name = self.wrapper_actual_name
        return func

    def get_module(self):
        """Get the Module object this function belongs to"""
        return self._module
    def set_module(self, module):
        """Set the Module object this function belongs to"""
        self._module = module
        self.wrapper_base_name = "_wrap_%s%s" % (
            module.prefix, self.mangled_name)
    module = property(get_module, set_module)
    
    def generate_call(self):
        "virtual method implementation; do not call"
        if self.foreign_cpp_namespace:
            namespace = self.foreign_cpp_namespace + '::'
        elif self._module.cpp_namespace_prefix:
            namespace = self._module.cpp_namespace_prefix + '::'
        else:
            namespace = ''

        if self.template_parameters:
            template_params = '< %s >' % ', '.join(self.template_parameters)
        else:
            template_params = ''
 
        if self.return_value.ctype == 'void':
            self.before_call.write_code(
                '%s%s%s(%s);' % (namespace, self.function_name, template_params,
                                 ", ".join(self.call_params)))
        else:
            if self.return_value.REQUIRES_ASSIGNMENT_CONSTRUCTOR:
                self.before_call.write_code(
                    '%s retval = %s%s%s(%s);' % (self.return_value.ctype,
                                                 namespace, self.function_name, template_params,
                                                 ", ".join(self.call_params)))
            else:
                self.before_call.write_code(
                    'retval = %s%s%s(%s);' % (namespace, self.function_name, template_params,
                                              ", ".join(self.call_params)))

    def _before_return_hook(self):
        "hook that post-processes parameters and check for custodian=<n> CppClass parameters"
        cppclass_typehandlers.implement_parameter_custodians(self)

    def generate(self, code_sink, wrapper_name=None, extra_wrapper_params=()):
        """
        Generates the wrapper code
        code_sink -- a CodeSink instance that will receive the generated code
        wrapper_name -- name of wrapper function
        """
        if wrapper_name is None:
            self.wrapper_actual_name = self.wrapper_base_name
        else:
            self.wrapper_actual_name = wrapper_name
        tmp_sink = codesink.MemoryCodeSink()
        self.generate_body(tmp_sink)

        flags = self.get_py_method_def_flags()
        self.wrapper_args = []
        if 'METH_VARARGS' in flags:
            if self.self_parameter_pystruct is None:
                self_param = 'PyObject * PYBINDGEN_UNUSED(dummy)'
            else:
                self_param = '%s *self' % self.self_parameter_pystruct
            self.wrapper_args.append(self_param)
            self.wrapper_args.append("PyObject *args")
            if 'METH_KEYWORDS' in flags:
                self.wrapper_args.append("PyObject *kwargs")
        self.wrapper_args.extend(extra_wrapper_params)
        self.wrapper_return = "PyObject *"
        self.write_open_wrapper(code_sink)
        tmp_sink.flush_to(code_sink)
        self.write_close_wrapper(code_sink)
        

    def generate_declaration(self, code_sink, extra_wrapper_parameters=()):
        ## We need to fake generate the code (and throw away the
        ## result) only in order to obtain correct method signature.
        self.reset_code_generation_state()
        self.generate(codesink.NullCodeSink(), extra_wrapper_params=extra_wrapper_parameters)
        assert isinstance(self.wrapper_return, str)
        assert isinstance(self.wrapper_actual_name, str)
        assert isinstance(self.wrapper_args, list)
        code_sink.writeln('%s %s(%s);' % (self.wrapper_return, self.wrapper_actual_name, ', '.join(self.wrapper_args)))
        self.reset_code_generation_state()

    def get_py_method_def(self, name):
        """
        Returns an array element to use in a PyMethodDef table.
        Should only be called after code generation.

        @param name: python function/method name
        """
        flags = self.get_py_method_def_flags()
        assert isinstance(self.wrapper_return, basestring)
        assert isinstance(self.wrapper_actual_name, basestring)
        assert isinstance(self.wrapper_args, list)
        return "{(char *) \"%s\", (PyCFunction) %s, %s, %s }," % \
               (name, self.wrapper_actual_name, '|'.join(flags),
                (self.docstring is None and "NULL" or ('"'+self.docstring+'"')))


class CustomFunctionWrapper(Function):
    """
    Adds a custom function wrapper.  The custom wrapper must be
    prepared to support overloading, i.e. it must have an additional
    "PyObject **return_exception" parameter, and raised exceptions
    must be returned by this parameter.
    """

    NEEDS_OVERLOADING_INTERFACE = True

    def __init__(self, function_name, wrapper_name, wrapper_body=None,
                 flags=('METH_VARARGS', 'METH_KEYWORDS')):
        super(CustomFunctionWrapper, self).__init__(function_name, ReturnValue.new('void'), [])
        self.wrapper_base_name = wrapper_name
        self.wrapper_actual_name = wrapper_name
        self.meth_flags = list(flags)
        self.wrapper_body = wrapper_body
        self.wrapper_args = ["PyObject *args", "PyObject *kwargs", "PyObject **return_exception"]
        self.wrapper_return = "PyObject *"


    def generate(self, code_sink, dummy_wrapper_name=None, extra_wrapper_params=()):
        assert extra_wrapper_params == ["PyObject **return_exception"]
        if self.wrapper_body is not None:
            code_sink.writeln(self.wrapper_body)
        else:
            self.generate_declaration(code_sink, extra_wrapper_parameters=extra_wrapper_params)

        #return "PyObject * %s (PyObject *args, PyObject *kwargs, PyObject **return_exception)" % self.wrapper_actual_name

    def generate_call(self, *args, **kwargs):
        pass


class OverloadedFunction(overloading.OverloadedWrapper):
    """Adds support for overloaded functions"""
    RETURN_TYPE = 'PyObject *'
    ERROR_RETURN = 'return NULL;'

import cppclass_typehandlers
