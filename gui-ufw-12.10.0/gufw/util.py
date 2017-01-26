# Gufw 12.10.0 - http://gufw.tuxfamily.org
# Copyright (C) 2008-2011 Raul Soriano https://launchpad.net/~gatoloko
#                         Marcos Alvarez Costales https://launchpad.net/~costales
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

import os



class Validation:
    """Manages application instances & config file"""
    def __init__(self):
        self.pid_file = '/tmp/gufw.pid'
        self._check_instance()
        self._start_application()
    
    def _check_instance(self):
        """Check whether the app is running"""
        if not os.path.isfile(self.pid_file):
            return

        # Read the pid from file
        pid = 0
        try:
            file = open(self.pid_file, 'rt')
            data = file.read()
            file.close()
            pid = int(data)
        except:
            pass
        
        # Check whether the process specified exists
        if 0 == pid:
            return
        try:
            os.kill(pid, 0) # exception if the pid is invalid
        except:
            return
        
        exit(0)
    
    def _start_application(self):
        """Called when there is no running instances, storing the new pid"""
        file = open(self.pid_file, 'wt')
        file.write(str(os.getpid()))
        file.close()
    
    def exit_application(self):
        """Close app"""
        try:
            os.remove(self.pid_file)
        except:
            pass



class Path:
    """Return app paths"""
    def get_ui_path(self, file_name):
        """Return Path GUI"""
        path = os.path.join('/usr', 'share', 'gufw', 'ui', file_name)
        if not os.path.exists(path):
            path = os.path.join('data', 'ui', file_name)
        return path
    
    def get_shield_path(self, incoming, outgoing):
        """Return Path Shields"""
        file_name = incoming + '_' + outgoing + '.png'
        path = os.path.join('/usr', 'share', 'gufw', 'media', file_name)
        if not os.path.exists(path):
            path = os.path.join('data', 'media', file_name)
        return path
        
    def get_icon_path(self):
        """Return Icon app"""
        path = os.path.join('/usr', 'share', 'icons', 'hicolor', '48x48', 'apps', 'gufw.png')
        if not os.path.exists(path):
            path = os.path.join('data', 'media', 'gufw.png')
        return path
