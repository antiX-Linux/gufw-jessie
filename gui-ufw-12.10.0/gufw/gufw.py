#!/usr/bin/env python
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

from util         import Validation
from controller   import Controller 
from view.guiGufw import GuiGufw


if __name__ == "__main__":
    
    # Check config file & is running previously
    appInstance = Validation()
    
    # Controller
    controler = Controller()
    
    # Firewall
    firewall = controler.get_firewall()
    
    # Show GUI
    app = GuiGufw(firewall)
    
    # Remove current instance
    appInstance.exit_application()
    
