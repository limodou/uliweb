#coding=utf-8
import sys
import logging
import re
try:
    import colorama
    colorama.init()
except:
    colorama = None
   
_r_color_delimeter = re.compile(r'\{\{.*?\}\}')

#Available formatting constants are:
#Fore: BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE, RESET.
#Back: BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE, RESET.
#Style: DIM, NORMAL, BRIGHT, RESET_ALL

def colored(text, fore=None, back=None, style=None):
    if colorama:
        part = []
        if fore:
            part.append(getattr(colorama.Fore, fore.upper(), None))
        if back:
            part.append(getattr(colorama.Back, back.upper(), None))
        if style:
            part.append(getattr(colorama.Style, style.upper(), None))
        part.append(text)
        part = filter(None, part)
        part.append(colorama.Fore.RESET + colorama.Back.RESET + colorama.Style.RESET_ALL)
        return ''.join(part)
    else:
        return text

class ColoredStream(object):
    def __init__(self, stream, color_delimeter=('{{', '}}')):
        self.stream = stream
        self.color_delimeter = color_delimeter
        
    def write(self, buf):
        def m(match):
            c, text = match.group()[2:-2].split(':', 1)
            v = list(c.split('|'))
            v.extend(['', ''])
            fore, back, style = v[:3]
            msg = colored(text, fore, back, style)
            return msg
        
        b = _r_color_delimeter.sub(m, buf)
        self.stream.write(b)
        
default_log_colors = {
    'DEBUG':    'white',
    'INFO':     'green',
    'WARNING':  'yellow',
    'ERROR':    'red',
    'CRITICAL': 'red',
}

class ColoredFormatter(logging.Formatter):
    """A formatter that allows colors to be placed in the format string.

    Intended to help in creating more readable logging output."""

    def __init__(self, format=None, datefmt=None,
                 log_colors=None, reset=True, style='%'):
        """
        :Parameters:
        - format (str): The format string to use
        - datefmt (str): A format string for the date
        - log_colors (dict):
            A mapping of log level names to color names
        - reset (bool):
            Implictly append a color reset to all records unless False
        - style ('%' or '{' or '$'):
            The format style to use. No meaning prior to Python 3.2.

        The ``format``, ``datefmt`` and ``style`` args are passed on to the
        Formatter constructor.
        """
        if sys.version_info > (3, 2):
            super(ColoredFormatter, self).__init__(
                format, datefmt, style=style)
        elif sys.version_info > (2, 7):
            super(ColoredFormatter, self).__init__(format, datefmt)
        else:
            logging.Formatter.__init__(self, format, datefmt)
        self.log_colors = default_log_colors
        self.log_colors.update(log_colors or {})
        self.reset = reset

    def format(self, record):
        # If we recognise the level name,
        # add the levels color as `log_color`
        # Format the message
        if sys.version_info > (2, 7):
            message = super(ColoredFormatter, self).format(record)
        else:
            message = logging.Formatter.format(self, record)

        if record.levelname in self.log_colors:
            message = colored(message, self.log_colors[record.levelname])
        
        return message

class ColoredStreamHandler(logging.StreamHandler):
    def __init__(self, stream=None, color_delimeter=('{{', '}}')):
        logging.StreamHandler.__init__(self, stream)
        self.color_delimeter = color_delimeter
        self.stream = ColoredStream(self.stream, color_delimeter)
        
if __name__ == '__main__':
    
    log = logging.getLogger('test')
    log.addHandler(ColoredStreamHandler())
    log.setLevel(logging.DEBUG)
    log.info("Test {{white|red:Red text}} {{green:Green Text}} {{yellow|white|BRIGHT:bright}}")