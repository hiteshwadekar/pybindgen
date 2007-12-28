# docstrings not neede here (the type handler interfaces are fully
# documented in base.py) pylint: disable-msg=C0111

from base import ReturnValue, Parameter,\
     ReverseWrapperBase, ForwardWrapperBase


class IntParam(Parameter):

    DIRECTIONS = [Parameter.DIRECTION_IN]
    CTYPES = ['int']

    def convert_c_to_python(self, wrapper):
        assert isinstance(wrapper, ReverseWrapperBase)
        wrapper.build_params.add_parameter('i', [self.value])

    def convert_python_to_c(self, wrapper):
        assert isinstance(wrapper, ForwardWrapperBase)
        name = wrapper.declarations.declare_variable(self.ctype, self.name)
        wrapper.parse_params.add_parameter('i', ['&'+name], self.name)
        wrapper.call_params.append(name)


class UnsignedIntParam(Parameter):

    DIRECTIONS = [Parameter.DIRECTION_IN]
    CTYPES = ['unsigned int', 'uint32_t']

    def convert_c_to_python(self, wrapper):
        assert isinstance(wrapper, ReverseWrapperBase)
        wrapper.build_params.add_parameter('I', [self.value])

    def convert_python_to_c(self, wrapper):
        assert isinstance(wrapper, ForwardWrapperBase)
        name = wrapper.declarations.declare_variable(self.ctype, self.name)
        wrapper.parse_params.add_parameter('I', ['&'+name], self.name)
        wrapper.call_params.append(name)


class IntReturn(ReturnValue):

    CTYPES = ['int']

    def get_c_error_return(self):
        return "return INT_MIN;"
    
    def convert_python_to_c(self, wrapper):
        wrapper.parse_params.add_parameter("i", ["&"+self.value], prepend=True)

    def convert_c_to_python(self, wrapper):
        wrapper.build_params.add_parameter("i", [self.value], prepend=True)


class UnsignedIntReturn(ReturnValue):

    CTYPES = ['unsigned int', 'uint32_t']

    def get_c_error_return(self):
        return "return 0;"
    
    def convert_python_to_c(self, wrapper):
        wrapper.parse_params.add_parameter("I", ["&"+self.value], prepend=True)

    def convert_c_to_python(self, wrapper):
        wrapper.build_params.add_parameter("I", [self.value], prepend=True)


class IntPtrParam(Parameter):

    DIRECTIONS = [Parameter.DIRECTION_IN, Parameter.DIRECTION_OUT,
                  Parameter.DIRECTION_IN|Parameter.DIRECTION_OUT]
    CTYPES = ['int*']
    
    def convert_c_to_python(self, wrapper):
        if self.direction & self.DIRECTION_IN:
            wrapper.build_params.add_parameter('i', ['*'+self.value])
        if self.direction & self.DIRECTION_OUT:
            wrapper.parse_params.add_parameter("i", [self.value], self.name)

    def convert_python_to_c(self, wrapper):
        assert self.ctype == 'int*'
        name = wrapper.declarations.declare_variable(self.ctype[:-1], self.name)
        wrapper.call_params.append('&'+name)
        if self.direction & self.DIRECTION_IN:
            wrapper.parse_params.add_parameter('i', ['&'+name], self.name)
        if self.direction & self.DIRECTION_OUT:
            wrapper.build_params.add_parameter("i", [name])
        


class IntRefParam(Parameter):

    DIRECTIONS = [Parameter.DIRECTION_IN, Parameter.DIRECTION_OUT,
                  Parameter.DIRECTION_IN|Parameter.DIRECTION_OUT]
    CTYPES = ['int&']
    
    def convert_c_to_python(self, wrapper):
        if self.direction & self.DIRECTION_IN:
            wrapper.build_params.add_parameter('i', [self.value])
        if self.direction & self.DIRECTION_OUT:
            wrapper.parse_params.add_parameter("i", [self.value], self.name)

    def convert_python_to_c(self, wrapper):
        assert self.ctype == 'int&'
        name = wrapper.declarations.declare_variable(self.ctype[:-1], self.name)
        wrapper.call_params.append(name)
        if self.direction & self.DIRECTION_IN:
            wrapper.parse_params.add_parameter('i', ['&'+name], self.name)
        if self.direction & self.DIRECTION_OUT:
            wrapper.build_params.add_parameter("i", [name])



class UInt16Return(ReturnValue):

    CTYPES = ['uint16_t']

    def get_c_error_return(self):
        return "return 0;"
    
    def convert_python_to_c(self, wrapper):
        tmp_var = wrapper.declarations.declare_variable("int", "tmp")
        wrapper.parse_params.add_parameter("i", ["&"+tmp_var], prepend=True)
        wrapper.after_call.write_error_check('%s > 0xffff' % tmp_var,
                                             'PyErr_SetString(PyExc_ValueError, "Out of range");')
        wrapper.after_call.write_code(
            "%s = %s;" % (self.value, tmp_var))

    def convert_c_to_python(self, wrapper):
        wrapper.build_params.add_parameter("i", [self.value], prepend=True)


class UInt16Param(Parameter):

    DIRECTIONS = [Parameter.DIRECTION_IN]
    CTYPES = ['uint16_t']

    def convert_c_to_python(self, wrapper):
        assert isinstance(wrapper, ReverseWrapperBase)
        wrapper.build_params.add_parameter('i', [self.value])

    def convert_python_to_c(self, wrapper):
        assert isinstance(wrapper, ForwardWrapperBase)
        name = wrapper.declarations.declare_variable("int", self.name)
        wrapper.parse_params.add_parameter('i', ['&'+name], self.name)
        wrapper.before_call.write_error_check('%s > 0xffff' % name,
                                              'PyErr_SetString(PyExc_ValueError, "Out of range");')
        wrapper.call_params.append(name)


class UInt8Return(ReturnValue):

    CTYPES = ['uint8_t']

    def get_c_error_return(self):
        return "return 0;"
    
    def convert_python_to_c(self, wrapper):
        tmp_var = wrapper.declarations.declare_variable("int", "tmp")
        wrapper.parse_params.add_parameter("i", ["&"+tmp_var], prepend=True)
        wrapper.after_call.write_error_check('%s > 0xff' % tmp_var,
                                             'PyErr_SetString(PyExc_ValueError, "Out of range");')
        wrapper.after_call.write_code(
            "%s = %s;" % (self.value, tmp_var))

    def convert_c_to_python(self, wrapper):
        wrapper.build_params.add_parameter("i", ['(int)' + self.value], prepend=True)


class UnsignedLongLongParam(Parameter):

    DIRECTIONS = [Parameter.DIRECTION_IN]
    CTYPES = ['unsigned long long', 'uint64_t']

    def convert_c_to_python(self, wrapper):
        assert isinstance(wrapper, ReverseWrapperBase)
        wrapper.build_params.add_parameter('K', [self.value])

    def convert_python_to_c(self, wrapper):
        assert isinstance(wrapper, ForwardWrapperBase)
        name = wrapper.declarations.declare_variable(self.ctype, self.name)
        wrapper.parse_params.add_parameter('K', ['&'+name], self.name)
        wrapper.call_params.append(name)

class UnsignedLongLongReturn(ReturnValue):

    CTYPES = ['unsigned long long', 'uint64_t']

    def get_c_error_return(self):
        return "return 0;"
    
    def convert_python_to_c(self, wrapper):
        wrapper.parse_params.add_parameter("K", ["&"+self.value], prepend=True)

    def convert_c_to_python(self, wrapper):
        wrapper.build_params.add_parameter("K", [self.value], prepend=True)



class LongLongParam(Parameter):

    DIRECTIONS = [Parameter.DIRECTION_IN]
    CTYPES = ['long long', 'int64_t']

    def convert_c_to_python(self, wrapper):
        assert isinstance(wrapper, ReverseWrapperBase)
        wrapper.build_params.add_parameter('L', [self.value])

    def convert_python_to_c(self, wrapper):
        assert isinstance(wrapper, ForwardWrapperBase)
        name = wrapper.declarations.declare_variable(self.ctype, self.name)
        wrapper.parse_params.add_parameter('L', ['&'+name], self.name)
        wrapper.call_params.append(name)

class LongLongReturn(ReturnValue):

    CTYPES = ['long long', 'int64_t']

    def get_c_error_return(self):
        return "return 0;"
    
    def convert_python_to_c(self, wrapper):
        wrapper.parse_params.add_parameter("L", ["&"+self.value], prepend=True)

    def convert_c_to_python(self, wrapper):
        wrapper.build_params.add_parameter("L", [self.value], prepend=True)


class Int8PtrParam(Parameter):

    DIRECTIONS = [Parameter.DIRECTION_IN, Parameter.DIRECTION_OUT,
                  Parameter.DIRECTION_IN|Parameter.DIRECTION_OUT]
    CTYPES = ['int8_t*']
    
    def convert_c_to_python(self, wrapper):
        if self.direction & self.DIRECTION_IN:
            wrapper.build_params.add_parameter('b', ['*'+self.value])
        if self.direction & self.DIRECTION_OUT:
            wrapper.parse_params.add_parameter("b", [self.value], self.name)

    def convert_python_to_c(self, wrapper):
        assert self.ctype.endswith('*')
        name = wrapper.declarations.declare_variable(self.ctype[:-1], self.name)
        wrapper.call_params.append('&'+name)
        if self.direction & self.DIRECTION_IN:
            wrapper.parse_params.add_parameter('b', ['&'+name], self.name)
        if self.direction & self.DIRECTION_OUT:
            wrapper.build_params.add_parameter("b", [name])

class UInt8PtrParam(Parameter):

    DIRECTIONS = [Parameter.DIRECTION_IN, Parameter.DIRECTION_OUT,
                  Parameter.DIRECTION_IN|Parameter.DIRECTION_OUT]
    CTYPES = ['uint8_t*']
    
    def convert_c_to_python(self, wrapper):
        if self.direction & self.DIRECTION_IN:
            wrapper.build_params.add_parameter('B', ['*'+self.value])
        if self.direction & self.DIRECTION_OUT:
            wrapper.parse_params.add_parameter("B", [self.value], self.name)

    def convert_python_to_c(self, wrapper):
        assert self.ctype.endswith('*')
        name = wrapper.declarations.declare_variable(self.ctype[:-1], self.name)
        wrapper.call_params.append('&'+name)
        if self.direction & self.DIRECTION_IN:
            wrapper.parse_params.add_parameter('B', ['&'+name], self.name)
        if self.direction & self.DIRECTION_OUT:
            wrapper.build_params.add_parameter("B", [name])
