#!/usr/bin/env python
#
# -*- coding: utf-8 -*-
#
#   sK1 help index build
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

import os
import shutil

import utils


SOURCE_PATH = 'test/'
BUILD_PATH = 'build/'

if os.path.lexists(BUILD_PATH):
    shutil.rmtree(BUILD_PATH)

shutil.copytree(SOURCE_PATH, BUILD_PATH)

md_files = utils.get_files_tree(BUILD_PATH, 'md')

utils.save_html.setup(html_css='markdown.css')

for item in md_files:
    dest = item[:-2] + 'html'
    print item, '==>', dest
    with open(item, 'rb') as fp:
        model = utils.parse_md(fp)
        with open(dest, 'wb') as res_fp:
            utils.save_html(res_fp, model)
    os.remove(item)
