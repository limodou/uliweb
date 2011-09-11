#!/usr/bin/env python

import os, sys

def parse_translation(f, lineno):
    """Read a single translation entry from the file F and return a
    tuple with the comments, msgid and msgstr.  The comments is returned
    as a list of lines which do not end in new-lines.  The msgid and
    msgstr are strings, possibly with embedded newlines"""
    line = f.readline()
    
    def get_line(f, line, need_keys, lineno):
        line = line.rstrip()
        key, value = line.split(' ', 1)
        # Parse msgid
        if key not in need_keys:
            print 'Error Line, need %r: %d, line=' % (need_keys, lineno, line)
            raise RuntimeError("parse error")
        v = value
        while 1:
            line = f.readline()
            line = line.rstrip()
            lineno += 1
            if not line or line[0] != '"':
                break
            v += '\n' + line[:]
        return lineno, key, v, line
    
    # Parse comments
    comments = []
    while 1:
        if not line:
            return lineno, None, None, None
        if line.strip() == '':
            return lineno, comments, None, None
        elif line[0] == '#':
            comments.append(line[:-1])
        else:
            break
        line = f.readline()
        lineno += 1

    lineno, key, msgid, line = get_line(f, line, ['msgid'], lineno)
    lineno, key, value, line = get_line(f, line, ['msgid_plural', 'msgstr'], lineno)
    if key == 'msgid_plural':
        msgid = (msgid, value)
        lineno, key, v1, line = get_line(f, line, ['msgstr[0]'], lineno)
        lineno, key, v2, line = get_line(f, line, ['msgstr[1]'], lineno)
        msgstr = (v1, v2)
    else:
        msgstr = value
        
    if line != '':
        print 'Error Line: ', line
        raise RuntimeError("parse error")

    return lineno, comments, msgid, msgstr

def split_comments(comments):
    """Split COMMENTS into flag comments and other comments.  Flag
    comments are those that begin with '#,', e.g. '#,fuzzy'."""
    flags = []
    other = []
    for c in comments:
        if len(c) > 1 and c[1] == ',':
            flags.append(c)
        else:
            other.append(c)
    return flags, other

def write_msg(comments, msgid, msgstr):
    s = []
    s.append('\n'.join(comments) + '\n')
    if isinstance(msgid, (tuple, list)):
        s.append('msgid ' + msgid[0] + '\n')
        s.append('msgid_plural ' + msgid[1] + '\n')
    else:
        s.append('msgid ' + msgid + '\n')
    if isinstance(msgstr, (tuple, list)):
        s.append('msgstr[0] ' + msgstr[0] + '\n')
        s.append('msgstr[1] ' + msgstr[1] + '\n\n')
    else:
        s.append('msgstr ' + msgstr + '\n\n')
    return ''.join(s)

def merge(file1, file2):
    import shutil
    if not os.path.exists(file1):
        shutil.copyfile(file2, file1)
        return
    # Read the source po file into a hash
    source = {}
    f2 = file(file2)
    lineno = 1
    while 1:
        lineno, comments, msgid, msgstr = parse_translation(f2, lineno)
        if comments is None and msgid is None and msgstr is None:
            break
        if msgid is not None and msgid != '""' and msgid != ('""', '""') :
            source[msgid] = msgstr, split_comments(comments)[1]
    
    f2.close()
    
    # Make a backup of the output file, open the copy for reading
    # and the original for writing.
    infile = file1 + '.bak'
    shutil.copyfile(file1, infile)
    outfile = open(file1, 'w')
    
    # Loop thought the original and replace stuff as we go
    string_count = 0
    update_count = 0
    untranslated = 0
    f1 = file(infile)
    lineno = 1
    while 1:
        lineno, comments, msgid, msgstr = parse_translation(f1, lineno)
        if comments is None and msgid is None and msgstr is None:
            break
        if msgid is None:
            continue
        else:
            if msgid != '""' and msgid != ('""', '""'):
                string_count += 1
            # Do not update the header, and only update if the source
            # has a non-empty translation.
            if msgid != '""':
                if msgid in source:
                    other = split_comments(comments)[1]
                    new_msgstr, new_flags = source[msgid]
                    new_comments = other + new_flags
                    del source[msgid]
                    if (new_msgstr != msgstr and new_msgstr != '""' and new_msgstr != ('""', '""')) or new_comments != comments:
                        if new_msgstr != msgstr and new_msgstr != '""' and new_msgstr != ('""', '""'):
                            update_count += 1
                            msgstr = new_msgstr
                        else:
                            comments = new_comments
                    
#                    else:
#                        if msgid != '""' and msgstr == '""':
#                            untranslated += 1
            outfile.write(write_msg(comments, msgid, msgstr))
        if msgid != '""' and (msgstr == '""' or msgstr == ('""', '""')):
            untranslated += 1
    
    _len = len(source)
    if _len:
        update_count += _len
        string_count += _len
        for msgid, _v in source.iteritems():
            msgstr, comments = _v
            outfile.write(write_msg(comments, msgid, msgstr))
            
            if msgid != '""' and msgstr == '""':
                untranslated += 1

    f1.close()
    outfile.close()
    # We're done.  Tell the user what we did.
    if string_count == 0:
        print '0 strings updated.'
    else:
        print('%d strings updated. '
            '%d of %d strings are still untranslated (%.0f%%).' %
            (update_count, untranslated, string_count,
            100.0 * untranslated / string_count))
    
def main(argv):
    if len(argv) != 2:
        argv0 = os.path.basename(argv[0])
        sys.exit('Usage: %s <lang.po>\n'
                 '\n'
                 'This script will replace the translations and flags in lang.po with\n'
                 'the translations and flags in the source po file read from standard\n'
                 'input.  Strings that are not found in the source file are left untouched.\n'
                 'A backup copy of lang.po is saved as lang.po.bak.\n'
                 '\n'
                 'Example:\n'
                 '    svn cat http://svn.collab.net/repos/svn/trunk/subversion/po/sv.po | \\\n'
                 '        %s sv.po' % (argv0, argv0))

    # Read the source po file into a hash
    source = {}
    while 1:
        comments, msgid, msgstr = parse_translation(sys.stdin)
        if not comments and msgid is None:
            break
        if msgid is not None:
            source[msgid] = msgstr, split_comments(comments)[0]

    # Make a backup of the output file, open the copy for reading
    # and the original for writing.
    os.rename(argv[1], argv[1] + '.bak')
    infile = open(argv[1] + '.bak')
    outfile = open(argv[1], 'w')

    # Loop thought the original and replace stuff as we go
    first = 1
    string_count = 0
    update_count = 0
    untranslated = 0
    while 1:
        comments, msgid, msgstr = parse_translation(infile)
        if not comments and msgid is None:
            break
        if not first:
            outfile.write('\n')
        first = 0
        if msgid is None:
            outfile.write('\n'.join(comments) + '\n')
        else:
            string_count += 1
            # Do not update the header, and only update if the source
            # has a non-empty translation.
            if msgid != '""' and source.get(msgid, ['""', []])[0] != '""':
                other = split_comments(comments)[1]
                new_msgstr, new_flags = source[msgid]
                new_comments = other + new_flags
                if new_msgstr != msgstr or new_comments != comments:
                    update_count += 1
                    msgstr = new_msgstr
                    comments = new_comments
            outfile.write('\n'.join(comments) + '\n')
            outfile.write('msgid ' + msgid + '\n')
            outfile.write('msgstr ' + msgstr + '\n')
        if msgstr == '""':
            untranslated += 1

    # We're done.  Tell the user what we did.
    print('%d strings updated. '
          '%d of %d strings are still untranslated (%.0f%%).' %
          (update_count, untranslated, string_count,
           100.0 * untranslated / string_count))

if __name__ == '__main__':
    main(sys.argv)
