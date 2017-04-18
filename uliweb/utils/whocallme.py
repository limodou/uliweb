def who_called_me(show_filename=True, out=None, indent=' '):
    def _wrapper(fn):
        def _inner_wrapper(*args, **kwargs):
            import sys
            import inspect
            output = out or sys.stdout
            assert hasattr(output, 'write'), \
                'argument \'out\' of function \'who_called_me\' must have a write method'
            index = 0
            stack = inspect.stack()
            stack.reverse()
            # remove ourself from the stack list
            stack.pop()
            for record in stack:
                frame = record[0]
                line = frame.f_lineno
                func_name = frame.f_code.co_name
                if show_filename:
                    descr = frame.f_code.co_filename
                else:
                    descr = frame.f_globals["__name__"]
                print >>output, '%sFile "%s", line %d, in %s' % (indent*index, descr, line, func_name)
#                print >>output, '%s%s@%s:%d' % (indent*index, descr, func_name, line)
                # to be safe explicitly delete the stack frame reference
                # @see http://docs.python.org/lib/inspect-stack.html
                del frame
                index += 1
            del stack
            if hasattr(output, 'flush'):
                output.flush()
            return fn(*args, **kwargs)
        return _inner_wrapper
    return _wrapper

def print_frame(out=None, depth=1):
    import sys
    import inspect

    # remove ourself from the stack list
    output = out or sys.stdout
    assert hasattr(output, 'write'), \
        'argument \'out\' of function \'who_called_me\' must have a write method'
    index = 0
    indent = ' '
    stack = inspect.stack()
    stack.reverse()
    stack.pop()
    for record in stack[-1*depth-1:-1]:
        if index >= depth:
            break
        frame = record[0]
        line = frame.f_lineno
        func_name = frame.f_code.co_name
        descr = frame.f_code.co_filename
        output.write('%sFile "%s", line %d, in %s' % (indent * index, descr, line, func_name))
        #                print >>output, '%s%s@%s:%d' % (indent*index, descr, func_name, line)
        # to be safe explicitly delete the stack frame reference
        # @see http://docs.python.org/lib/inspect-stack.html
        del frame
        index += 1
    if hasattr(output, 'flush'):
        output.flush()
