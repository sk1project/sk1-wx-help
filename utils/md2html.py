# -*- coding: utf-8 -*-
#
#   Markdown to HTML converter
#
# 	Copyright (C) 2018 by Igor E. Novikov
#
# 	This program is free software: you can redistribute it and/or modify
# 	it under the terms of the GNU General Public License as published by
# 	the Free Software Foundation, either version 3 of the License, or
# 	(at your option) any later version.
#
# 	This program is distributed in the hope that it will be useful,
# 	but WITHOUT ANY WARRANTY; without even the implied warranty of
# 	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# 	GNU General Public License for more details.
#
# 	You should have received a copy of the GNU General Public License
# 	along with this program.  If not, see <http://www.gnu.org/licenses/>.

import re

mdMODEL = 'Markdown Model'
mdOBJ = 'Markdown Object'
mdGROUP = 'Markdown Group'
mdSPACE = 'Empty Line'

mdH1 = '# '
mdH2 = '## '
mdH3 = '### '
mdH4 = '#### '
mdH5 = '##### '
mdH6 = '###### '
mdHEADERS = (mdH1, mdH2, mdH3, mdH4, mdH5, mdH6)
mdHRULE = '---'
mdIMAGE = '!['

mdUL = 'UL'
mdOL = 'OL'
mdLI = '* '

mdQB = 'QUOTE'
mdQL = '> '

mdPARA = 'PARA'
mdLINE = 'LINE'

mdHB = 'HTML'
mdCODE = '```'
mdTABLE = 'TABLE'


class MdObject(object):
    name = mdOBJ
    text = ''
    childs = []

    def __init__(self, name=mdOBJ, text=''):
        self.text = text
        self.name = name

    def write(self, fileptr):
        for item in self.childs:
            item.write(fileptr)


class MdGroup(MdObject):
    name = mdGROUP

    def __init__(self, name=''):
        name = name or self.name
        MdObject.__init__(self, name=name)
        self.childs = []

    def append(self, obj):
        self.childs.append(obj)


class MdModel(MdGroup):
    name = mdMODEL


class MdLine(MdObject):
    def __init__(self, name, text):
        MdObject.__init__(self, name=name, text=text)

    def write(self, fileptr):
        fileptr.write(self.text + '\n')


class MdLoader(object):
    model = None
    last = None

    @staticmethod
    def check_header(line):
        if line.startswith('#') and ' ' in line:
            return line.split(' ')[0] + ' ' in mdHEADERS
        return False

    def rotate_last(self, group=None):
        if self.last and self.last.name == mdTABLE:
            if len(self.last.childs) < 3 or \
                    '---' not in self.last.childs[1].text:
                self.last.name = mdPARA
        self.last = group

    def add_line(self, group_name, name, line):
        if group_name is None:
            self.rotate_last()
            self.model.append(MdLine(name, line))
        else:
            if not self.last or self.last.name != group_name:
                self.rotate_last(MdGroup(group_name))
                self.model.append(self.last)
            self.last.append(MdLine(name, line))

    def __call__(self, fileptr):
        fileptr.seek(0)
        self.model = MdModel()
        self.last = None
        for line in fileptr.readlines():
            line = line.strip('\r\n')
            # Code block
            if line.startswith(mdCODE):
                if self.last and self.last.name == mdCODE:
                    self.add_line(mdCODE, mdLINE, line)
                    self.last = None
                else:
                    self.add_line(mdCODE, mdLINE, line)
            elif self.last and self.last.name == mdCODE:
                self.add_line(mdCODE, mdLINE, line)
            # Empty line
            elif not line.strip():
                self.add_line(None, mdSPACE, line)
            # Horizontal rule
            elif line.startswith(mdHRULE) \
                    or line.startswith('***') \
                    or line.startswith('___'):
                self.add_line(None, mdHRULE, line)
            # Headers
            elif self.check_header(line):
                name = line.split(' ')[0] + ' '
                self.add_line(None, name, line)
            # Image
            elif line.startswith(mdIMAGE) and line.strip().endswith(')'):
                self.add_line(None, mdIMAGE, line)
            # Ordered list
            elif line.startswith('1. '):
                self.last = None
                self.add_line(mdOL, mdLI, line)
            elif self.last and self.last.name == mdOL and \
                    line.startswith('%d. ' % (len(self.last.childs) + 1)):
                self.add_line(mdOL, mdLI, line)
            # Unordered list items
            elif line.startswith(mdLI) or \
                    line.startswith('+ ') or line.startswith('- '):
                self.add_line(mdUL, mdLI, line)
            # Quote
            elif line.startswith(mdQL):
                self.add_line(mdQB, mdQL, line)
            # HTML block
            elif line.strip().startswith('<') and line.strip().endswith('>'):
                self.add_line(mdHB, mdLINE, line)
            # Table
            elif '|' in line:
                self.add_line(mdTABLE, mdLINE, line)
            # Paragraph
            else:
                self.add_line(mdPARA, mdLINE, line)
        model, self.model, self.last = self.model, None, None
        return model


parse_md = MdLoader()


class MdSaver(object):
    def __call__(self, fileptr, model):
        model.write(fileptr)


save_md = MdSaver()

HTML_HEADER = "<!DOCTYPE html PUBLIC '-//W3C//DTD XHTML 1.0 Transitional//EN'"
HTML_HEADER += """ 'http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd'>
<html xmlns='http://www.w3.org/1999/xhtml'>
<head>
<meta http-equiv='Content-Type' content='text/html; charset=utf-8' />%s
</head>
<body>
"""
HTML_FOOTER = "</body></html>"


class MdToHtmlConverter(object):
    html_header = True
    html_footer = True
    html_css = ''
    php_header = False
    php_footer = False
    indent = '    '

    def setup(self, **kwargs):
        for key, value in kwargs.iteritems():
            setattr(self, key, value)

    @staticmethod
    def parse_line(line):
        # Bold emphasis
        if '**' in line:
            line = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', line)
        if '__' in line:
            line = re.sub(r'__(.+?)__', r'<b>\1</b>', line)
        # Italic emphasis
        if '*' in line:
            line = re.sub(r'\*(.+?)\*', r'<i>\1</i>', line)
        if '_' in line:
            line = re.sub(r'_(.+?)_', r'<i>\1</i>', line)
        # Strikethrough
        if '~~' in line:
            line = re.sub(r'~~(.+?)~~', r'<s>\1</s>', line)
        # Inlined image
        if '![' in line:
            line = re.sub(r'!\[(.+?)\]\((.+?) \"(.+?)\"\)',
                          r"<img src='\2' alt='\1' title='\3'>", line)
        if '![' in line:
            line = re.sub(r'!\[(.+?)\]\((.+?)\)',
                          r"<img src='\2' alt='\1'>", line)
        # Links
        if '](' in line:
            line = re.sub(r'\[(.+?)\]\((.+?) \"(.+?)\"\)',
                          r"<a href='\2' title='\3'>\1</a>", line)
        if '](' in line:
            line = re.sub(r'\[(.+?)\]\((.+?)\)',
                          r"<a href='\2'>\1</a>", line)
        if 'http://' in line:
            line = re.sub(r' http://(.+?) ',
                          r" <a href='http://\1'>http://\1</a> ", line)
            line = re.sub(r' http://(.+?)$',
                          r" <a href='http://\1'>http://\1</a> ", line)
            line = re.sub(r'^http://(.+?) ',
                          r"<a href='http://\1'>http://\1</a> ", line)
            line = re.sub(r'^http://(.+?)$',
                          r"<a href='http://\1'>http://\1</a> ", line)
        if 'https://' in line:
            line = re.sub(r' https://(.+?) ',
                          r" <a href='https://\1'>https://\1</a> ", line)
            line = re.sub(r' https://(.+?)$',
                          r" <a href='https://\1'>https://\1</a> ", line)
            line = re.sub(r'^https://(.+?) ',
                          r"<a href='https://\1'>https://\1</a> ", line)
            line = re.sub(r'^https://(.+?)$',
                          r"<a href='https://\1'>https://\1</a> ", line)
        if '``' in line:
            line = re.sub(r'``(.+?)``', r'<code>\1</code>', line)
        if '`' in line:
            line = re.sub(r'`(.+?)`', r'<code>\1</code>', line)

        return line

    @staticmethod
    def parse_tr(line):
        line = line.strip().strip('|')
        return [item.strip() for item in line.split('|')]

    def __call__(self, fileptr, model):
        # Write header
        if self.html_header:
            css = ''
            if self.html_css:
                css = "\n<link rel='stylesheet' href='%s' " \
                      "type='text/css' media='screen' />" % self.html_css
            fileptr.write(HTML_HEADER % css)

        # Write body
        for item in model.childs:
            if item.name in mdHEADERS:
                index = len(item.name) - 1
                txt = self.parse_line(item.text[index + 1:].strip())
                fileptr.write('<h%d>%s</h%d>\n' % (index, txt, index))
            elif item.name == mdSPACE:
                fileptr.write('\n')
            elif item.name == mdHRULE:
                fileptr.write('<hr>\n')
            elif item.name == mdIMAGE:
                title = ''
                alt, link = [txt.strip() for txt
                             in item.text.strip()[2:-1].strip().split('](')]
                alt = " alt='%s'" if alt else alt
                if ' ' in link:
                    index = link.index(' ')
                    title = " title='%s'" % link[index:].strip()[1:-1]
                    link = link[:index]
                txt = "<center><img src='%s'%s%s></center>\n" % \
                      (link, alt, title)
                fileptr.write(txt)
            elif item.name == mdUL:
                fileptr.write('<ul>\n')
                for line in item.childs:
                    txt = self.parse_line(line.text[2:].strip())
                    fileptr.write('%s<li>%s</li>\n' % (self.indent, txt))
                fileptr.write('</ul>\n')
            elif item.name == mdOL:
                fileptr.write('<ol>\n')
                for line in item.childs:
                    index = line.text.index(' ')
                    txt = self.parse_line(line.text[index + 1:].strip())
                    fileptr.write('%s<li>%s</li>\n' % (self.indent, txt))
                fileptr.write('</ol>\n')
            elif item.name == mdQB:
                fileptr.write('<blockquote>\n')
                fileptr.write('%s<p>\n' % self.indent)
                for line in item.childs:
                    suffix = '<br>\n' if line.text.endswith('   ') else '\n'
                    txt = self.parse_line(line.text[1:].strip())
                    fileptr.write('%s%s%s' % (self.indent, txt, suffix))
                fileptr.write('</blockquote>\n')
            elif item.name == mdHB:
                for line in item.childs:
                    fileptr.write('%s\n' % line.text)
            elif item.name == mdCODE:
                fileptr.write('<pre>')
                for line in item.childs[1:-1]:
                    fileptr.write('%s\n' % line.text)
                fileptr.write('</pre>\n')
            elif item.name == mdTABLE:
                marks = self.parse_tr(item.childs[1].text)
                aligns = []
                for mark in marks:
                    if mark.startswith(':') and mark.enswith(':'):
                        aligns.append(" align='center'")
                    elif mark.enswith(':'):
                        aligns.append(" align='right'")
                    else:
                        aligns.append('')

                fileptr.write('<table>\n')
                fileptr.write(self.indent + '<thead>\n')
                fileptr.write(self.indent * 2 + '<tr>\n')
                ths = self.parse_tr(item.childs[0].text)
                for th in ths:
                    indx = ths.index(th)
                    align = aligns[indx] if indx < len(aligns) else ''
                    fileptr.write(self.indent * 3 + '<th%s>' % align)
                    fileptr.write(th + '</th>')
                fileptr.write(self.indent * 2 + '</tr>\n')
                fileptr.write(self.indent + '</thead>\n')

                fileptr.write(self.indent + '<tbody>\n')
                for child in item.childs[2:]:
                    tds = self.parse_tr(child.text)
                    fileptr.write(self.indent * 2 + '<tr>\n')
                    for td in tds:
                        indx = tds.index(td)
                        align = aligns[indx] if indx < len(aligns) else ''
                        fileptr.write(self.indent * 3 + '<td%s>' % align)
                        fileptr.write(td + '</td>')
                    fileptr.write(self.indent * 2 + '</tr>\n')
                fileptr.write(self.indent + '</tbody>\n')
                fileptr.write('</table>\n')
            else:
                indent = all(line.text.startswith(' ') for line in item.childs)
                fileptr.write('<ul>\n') if indent else None
                fileptr.write('<p>\n')
                for line in item.childs:
                    suffix = '<br>\n' if line.text.endswith('   ') else '\n'
                    txt = self.parse_line(line.text.strip())
                    fileptr.write('%s%s' % (txt, suffix))
                fileptr.write('</p>\n')
                fileptr.write('</ul>\n') if indent else None

        # Write footer
        if self.html_footer:
            fileptr.write(HTML_FOOTER)


save_html = MdToHtmlConverter()
