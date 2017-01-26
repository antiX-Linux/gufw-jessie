# Gufw 12.10.0 - http://gufw.tuxfamily.org
# Copyright (C) 2008-2011 Marcos Alvarez Costales https://launchpad.net/~costales
#
# Gufw is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
# 
# Gufw is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with Gufw; if not, see http://www.gnu.org/licenses for more
# information.

from model.Firewall import Firewall


class Controller:
    
    def __init__(self):
        self.firewall = Firewall()

    def get_firewall(self):
        return self.firewall
        
