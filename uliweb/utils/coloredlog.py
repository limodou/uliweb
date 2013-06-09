#coding=utf-8
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
            msg = self.colored(text, fore, back, style)
            return msg
        
        b = _r_color_delimeter.sub(m, buf)
        self.stream.write(b)
        
    def colored(self, text, fore=None, back=None, style=None):
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