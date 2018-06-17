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
HEADERS = (mdH1, mdH2, mdH3, mdH4, mdH5, mdH6)
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


class MdObject(object):
    name = mdOBJ
    text = ''
    childs = []

    def __init__(self, name=mdOBJ, text=''):
        self.text = text
        self.name = name

    def write(self, fileptr):
        if isinstance(self.childs, list):
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
            return line.split(' ')[0] + ' ' in HEADERS
        return False

    def add_line(self, group_name, name, line):
        if group_name is None:
            self.last = None
            self.model.append(MdLine(name, line))
        else:
            if not self.last or self.last.name != group_name:
                self.last = MdGroup(group_name)
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
            elif line.startswith(mdHRULE):
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
            elif line.startswith(mdLI):
                self.add_line(mdUL, mdLI, line)
            # Quote
            elif line.startswith(mdQL):
                self.add_line(mdQB, mdQL, line)
            # HTML block
            elif line.strip().startswith('<') and line.strip().endswith('>'):
                self.add_line(mdHB, mdLINE, line)
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
