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

import commands
import time
import os

import dbus

# Work around a bug in python-distutils-extra auto, fixed in p-d-e rev 258
# org.freedesktop.PolicyKit1


class Firewall():
    """Set or get the Firewall properties"""
    
    WIN_WIDTH = 336
    WIN_HEIGHT = 334
    WIN_VPANEL = 153
    
    def __init__(self):
        bus = dbus.SystemBus()
        remote_object = bus.get_object("gufw.Daemon", "/Gufw_daemon")
        self.iface = dbus.Interface(remote_object, "gufw.SampleInterface")
        
        self.gufw_logging     = "disable"
        self.listening_status = "disable"
        self.notify_popup     = "disable"
        self.width            = self.WIN_WIDTH
        self.height           = self.WIN_HEIGHT
        self.vpanel           = self.WIN_VPANEL
        self._read_config_file()
    
    def unlock(self):
        """Unlock by PolicyKit"""
        try:
            self.iface.fw_unlock()
        except:
            return "no_access"
            
        self.status           = self.iface.get_status()
        self.incoming_policy  = self.iface.get_policy("incoming")
        self.outgoing_policy  = self.iface.get_policy("outgoing")
        self.ufw_logging      = self.iface.get_ufw_logging()
        return "access"
    
    def get_window_size(self):
        """Return the width & height"""
        return self.width, self.height
    
    def get_vpanel_pos(self):
        """Return the Vpanel position"""
        return self.vpanel
        
    def get_status(self):
        """Get status FW (enable/disable)"""
        return self.status
    
    def set_status(self, status):
        """Set status FW (enable/disable)"""
        self.status = status
        self._add_gufw_log(self.iface.set_status(status))
    
    def get_policy(self, policy):
        """Get Policy (Incoming & Outgoing = allow/deny/reject)"""
        if policy == "incoming":
            return self.incoming_policy
        elif policy == "outgoing":
            return self.outgoing_policy
    
    def set_policy(self, direction, policy):
        """Set Policy (Incoming & Outgoing = allow/deny/reject)"""
        if direction == "incoming":
            if policy == "allow":
                self.incoming_policy = "allow"
            elif policy == "deny":
                self.incoming_policy = "deny"
            elif policy == "reject":
                self.incoming_policy = "reject"
                
        elif direction == "outgoing":
            if policy == "allow":
                self.outgoing_policy = "allow"
            elif policy == "deny":
                self.outgoing_policy = "deny"
            elif policy == "reject":
                self.outgoing_policy = "reject"
        
        self._add_gufw_log(self.iface.set_policy(direction, policy))
    
    def get_ufw_logging(self):
        """Get logging (enable/disable)"""
        return self.ufw_logging
    
    def set_ufw_logging(self, logging):
        """Get log level (off/on/low/medium/high/full)"""
        self.ufw_logging = logging
        self._add_gufw_log(self.iface.set_ufw_logging(logging))
    
    def get_listening_report(self):
        """Get listening report"""
        return self.iface.get_listening_report()
            
    def get_listening_status(self):
        """Get listening status (enable/disable)"""
        return self.listening_status
    
    def set_listening_status(self, status):
        """Set listening status (enable/disable)"""
        self.listening_status = status
    
    def get_notify_popup(self):
        """Get notify popup status (enable/disable)"""
        return self.notify_popup
    
    def set_notify_popup(self, status):
        """Set notify popup status (enable/disable)"""
        self.notify_popup = status
    
    def reset_ufw(self):
        """Reset cofig ufw"""
        self._add_gufw_log(self.iface.reset_ufw())
        
    def get_gufw_logging(self):
        """Get the Gufw Logging Status (enable/disable)"""
        return self.gufw_logging
        
    def set_gufw_logging(self, status):
        """Set the Gufw Logging Status (enable/disable)"""
        self.gufw_logging = status
    
    def get_gufw_log(self, log = 'local'):
        """Get Gufw Log"""
        return self.iface.get_gufw_log(log)
    
    def _add_gufw_log(self, line):
        """Add a command to Gufw Log"""
        self.iface.add_gufw_log(self.gufw_logging, line)
        
    def erase_gufw_log(self):
        """Erase all Gufw Logs"""
        self.iface.erase_gufw_log()
        
    def add_rule(self, is_program, insert_number, action, direction, log, protocol, fromip, fromport, toip, toport):
        """Add rule to firewall"""
        self._add_gufw_log(self.iface.add_rule(is_program, insert_number, action, direction, log, protocol, fromip, fromport, toip, toport))
    
    def remove_rule(self, number):
        """Remove rule from firewall"""
        self._add_gufw_log(self.iface.remove_rule(str(number)))
    
    def get_number_rules(self):
        """Get the actual number of rules"""
        return self.iface.get_number_rules()
    
    def get_rule_list(self):
        """Get all List Rules"""
        return self.iface.get_rule_list()
    
    def update_config_file(self, width, height, vpanel):
        """Save actual FW config when quitting Gufw"""
        self.iface.update_config_file(width, height, vpanel, self.gufw_logging, self.listening_status, self.notify_popup)
        self.iface.Exit()
    
    def _read_config_file(self):
        """Get previous values from config file """
        file = commands.getstatusoutput("cat /etc/gufw/gufw.cfg")
        if file[0] != 0:
            return
        cfg_file = file[1].split("\n")
        for line in cfg_file:
            # Width & height
            if line.find("sizewin=") != -1:
                width_height_split = (line.replace("sizewin=", "")).split("x")
                self.width = int(width_height_split[0])
                self.height = int(width_height_split[1])
            # Vpanel position
            if line.find("vpanel=") != -1:
                self.vpanel = int(line.replace("vpanel=", ""))
            # Gufw Logging
            if line.find("log=enable") != -1:
                self.gufw_logging = "enable"
            # Listening Status
            if line.find("listening=enable") != -1:
                self.listening_status = "enable"
            # Notify Status
            if line.find("notify_popup=enable") != -1:
                self.notify_popup = "enable"
