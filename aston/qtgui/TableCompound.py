# -*- coding: utf-8 -*-

#    Copyright 2011-2014 Roderick Bovee
#
#    This file is part of Aston.
#
#    Aston is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    Aston is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with Aston.  If not, see <http://www.gnu.org/licenses/>.

"""
Model for handling display of compound lists.
"""

from __future__ import unicode_literals
from aston.qtgui.TableModel import TableModel


class CompoundTreeModel(TableModel):
    def __init__(self, database=None, tree_view=None, master_window=None, \
                 *args):
        super(CompoundTreeModel, self).__init__(database, tree_view, \
                                            master_window, *args)
        #TODO: handle JCAMP
        #TODO: handle AMSDIS
        #TODO: handle Aston?
