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

import time
import commands

from gi.repository import GObject
import dbus
import dbus.service
import dbus.mainloop.glib
from dbus.exceptions import DBusException

class DemoException(dbus.DBusException):
    _dbus_error_name = 'gufw.DemoException'



class PermissionDeniedByPolicy(dbus.DBusException):
    _dbus_error_name = 'com.ubuntu.DeviceDriver.PermissionDeniedByPolicy'



class Gufw_daemon(dbus.service.Object):
    
    def __init__(self, conn=None, object_path=None, bus_name=None):
        dbus.service.Object.__init__(self, conn, object_path, bus_name)
        self.enforce_polkit = True
        self.dbus_info      = None
        self.polkit         = None
        self.__caller_pid__ = 0
        
    @dbus.service.method("gufw.SampleInterface",
                         in_signature='', out_signature='',
                         sender_keyword='sender', connection_keyword='conn')
    def RaiseException(self, sender=None, conn=None):
        raise DemoException('RaiseException Gufw method')
    
    @dbus.service.method("gufw.SampleInterface",
                         in_signature='', out_signature='',
                         sender_keyword='sender', connection_keyword='conn')
    def Exit(self, sender=None, conn=None):
        mainloop.quit()
            
    def _check_polkit_privilege(self, sender, conn, privilege):
        """Verify that sender has a given PolicyKit privilege."""
        if sender is None and conn is None:
            raise
        
        # Get peer PID
        if self.dbus_info is None:
            self.dbus_info = dbus.Interface(conn.get_object('org.freedesktop.DBus',
                '/org/freedesktop/DBus/Bus', False), 'org.freedesktop.DBus')
        pid = self.dbus_info.GetConnectionUnixProcessID(sender)
        
        # Query PolicyKit
        if self.polkit is None:
            self.polkit = dbus.Interface(dbus.SystemBus().get_object(
                'org.freedesktop.PolicyKit1',
                '/org/freedesktop/PolicyKit1/Authority', False),
                'org.freedesktop.PolicyKit1.Authority')
        try:
            # Don't need is_challenge return here, since we call with AllowUserInteraction
            (is_auth, _, details) = self.polkit.CheckAuthorization(
                    ('unix-process', {'pid': dbus.UInt32(pid, variant_level=1),
                    'start-time': dbus.UInt64(0, variant_level=1)}), 
                    privilege, {'': ''}, dbus.UInt32(1), '', timeout=600)
        except:
            raise
        
        if not is_auth:
            raise
            
        if self.__caller_pid__ == 0:
            self.__caller_pid__ = pid
            
    @dbus.service.method("gufw.SampleInterface",
                     in_signature='', out_signature='',
                     sender_keyword='sender', connection_keyword='conn')
    def fw_unlock(self, sender=None, conn=None):
        """PolicyKit"""
        self._check_polkit_privilege(sender, conn, 'gufw.daemon.start')
            
    @dbus.service.method("gufw.SampleInterface",
                     in_signature='', out_signature='s',
                     sender_keyword='sender', connection_keyword='conn')
    def get_status(self, sender=None, conn=None):
        """Get Initial status"""
        dbus_info_aux = dbus.Interface(conn.get_object('org.freedesktop.DBus', '/org/freedesktop/DBus/Bus', False), 'org.freedesktop.DBus')
        if ( self.__caller_pid__ == 0 ) or ( self.__caller_pid__ != dbus_info_aux.GetConnectionUnixProcessID(sender) ):
            return "no_access"
        
        ufw_status = commands.getstatusoutput("LANGUAGE=C ufw status")
        if ufw_status[1].find("Status: active") != -1:
            return "enable"
        else:
            return "disable"

    @dbus.service.method("gufw.SampleInterface",
                     in_signature='s', out_signature='s',
                     sender_keyword='sender', connection_keyword='conn')
    def get_policy(self, policy, sender=None, conn=None):
        """Get Initial incoming policy"""
        dbus_info_aux = dbus.Interface(conn.get_object('org.freedesktop.DBus', '/org/freedesktop/DBus/Bus', False), 'org.freedesktop.DBus')
        if ( self.__caller_pid__ == 0 ) or ( self.__caller_pid__ != dbus_info_aux.GetConnectionUnixProcessID(sender) ):
            return "no_access"
        
        if policy == "incoming":
            ufw_default_incoming = commands.getstatusoutput("grep DEFAULT_INPUT_POLICY /etc/default/ufw")
            if ufw_default_incoming[1].find("ACCEPT") != -1:
                return "allow"
            elif ufw_default_incoming[1].find("DROP") != -1:
                return "deny"
            elif ufw_default_incoming[1].find("REJECT") != -1:
                return "reject"
        
        elif policy == "outgoing":
            ufw_default_outgoing = commands.getstatusoutput("grep DEFAULT_OUTPUT_POLICY /etc/default/ufw")
            if ufw_default_outgoing[1].find("ACCEPT") != -1:
                return "allow"
            elif ufw_default_outgoing[1].find("DROP") != -1:
                return "deny"
            elif ufw_default_outgoing[1].find("REJECT") != -1:
                return "reject"

    @dbus.service.method("gufw.SampleInterface",
                     in_signature='', out_signature='s',
                     sender_keyword='sender', connection_keyword='conn')
    def get_ufw_logging(self, sender=None, conn=None):
        """Get Initial ufw Logging"""
        dbus_info_aux = dbus.Interface(conn.get_object('org.freedesktop.DBus', '/org/freedesktop/DBus/Bus', False), 'org.freedesktop.DBus')
        if ( self.__caller_pid__ == 0 ) or ( self.__caller_pid__ != dbus_info_aux.GetConnectionUnixProcessID(sender) ):
            return "no_access"
        
        ufw_cmd = commands.getstatusoutput("cat /etc/ufw/ufw.conf")
        if ufw_cmd[1].find("LOGLEVEL=full") != -1:
            return "full"
        elif ufw_cmd[1].find("LOGLEVEL=high") != -1:
            return "high"
        elif ufw_cmd[1].find("LOGLEVEL=medium") != -1:
            return "medium"
        elif ufw_cmd[1].find("LOGLEVEL=low") != -1:
            return "low"
        else:
            return "off"
    
    @dbus.service.method("gufw.SampleInterface",
                     in_signature='s', out_signature='s',
                     sender_keyword='sender', connection_keyword='conn')
    def set_status(self, status, sender=None, conn=None):
        """Set status FW (enable/disable)"""
        dbus_info_aux = dbus.Interface(conn.get_object('org.freedesktop.DBus', '/org/freedesktop/DBus/Bus', False), 'org.freedesktop.DBus')
        if ( self.__caller_pid__ == 0 ) or ( self.__caller_pid__ != dbus_info_aux.GetConnectionUnixProcessID(sender) ):
            return "no_access"
        
        if status == "enable":
            cmd = "ufw enable"
        else:
            cmd = "ufw disable"
            
        commands.getstatusoutput(cmd)
        return cmd
    
    @dbus.service.method("gufw.SampleInterface",
                     in_signature='ss', out_signature='s',
                     sender_keyword='sender', connection_keyword='conn')
    def set_policy(self, direction, policy, sender=None, conn=None):
        """Set Policy (Incoming & Outgoing = allow/deny/reject)"""
        dbus_info_aux = dbus.Interface(conn.get_object('org.freedesktop.DBus', '/org/freedesktop/DBus/Bus', False), 'org.freedesktop.DBus')
        if ( self.__caller_pid__ == 0 ) or ( self.__caller_pid__ != dbus_info_aux.GetConnectionUnixProcessID(sender) ):
            return "no_access"
        
        if direction == "incoming":
            if policy == "allow":
                cmd = "ufw default allow incoming"
            elif policy == "deny":
                cmd = "ufw default deny incoming"
            elif policy == "reject":
                cmd = "ufw default reject incoming"
                
        elif direction == "outgoing":
            if policy == "allow":
                cmd = "ufw default allow outgoing"
            elif policy == "deny":
                cmd = "ufw default deny outgoing"
            elif policy == "reject":
                cmd = "ufw default reject outgoing"
        
        commands.getstatusoutput(cmd)
        return cmd
    
    @dbus.service.method("gufw.SampleInterface",
                     in_signature='s', out_signature='s',
                     sender_keyword='sender', connection_keyword='conn')
    def set_ufw_logging(self, logging, sender=None, conn=None):
        """Get log level (off/low/medium/high/full)"""
        dbus_info_aux = dbus.Interface(conn.get_object('org.freedesktop.DBus', '/org/freedesktop/DBus/Bus', False), 'org.freedesktop.DBus')
        if ( self.__caller_pid__ == 0 ) or ( self.__caller_pid__ != dbus_info_aux.GetConnectionUnixProcessID(sender) ):
            return "no_access"
        
        if logging == "off":
            cmd = "ufw logging off"
        elif logging == "low":
            cmd = "ufw logging low"
        elif logging == "medium":
            cmd = "ufw logging medium"
        elif logging == "high":
            cmd = "ufw logging high"
        elif logging == "full":
            cmd = "ufw logging full"
        
        commands.getstatusoutput(cmd)
        return cmd
    
    @dbus.service.method("gufw.SampleInterface",
                     in_signature='', out_signature='s',
                     sender_keyword='sender', connection_keyword='conn')
    def reset_ufw(self, sender=None, conn=None):
        """Reset ufw config"""
        dbus_info_aux = dbus.Interface(conn.get_object('org.freedesktop.DBus', '/org/freedesktop/DBus/Bus', False), 'org.freedesktop.DBus')
        if ( self.__caller_pid__ == 0 ) or ( self.__caller_pid__ != dbus_info_aux.GetConnectionUnixProcessID(sender) ):
            return "no_access"
        
        cmd = "ufw --force reset"
        commands.getstatusoutput(cmd)
        return cmd
    
    @dbus.service.method("gufw.SampleInterface",
                     in_signature='', out_signature='',
                     sender_keyword='sender', connection_keyword='conn')
    def erase_gufw_log(self, sender=None, conn=None):
        """Erase all Gufw Logs"""
        dbus_info_aux = dbus.Interface(conn.get_object('org.freedesktop.DBus', '/org/freedesktop/DBus/Bus', False), 'org.freedesktop.DBus')
        if ( self.__caller_pid__ == 0 ) or ( self.__caller_pid__ != dbus_info_aux.GetConnectionUnixProcessID(sender) ):
            return
            
        commands.getstatusoutput("rm /var/log/gufw_log.txt")
    
    @dbus.service.method("gufw.SampleInterface",
                     in_signature='s', out_signature='s',
                     sender_keyword='sender', connection_keyword='conn')
    def remove_rule(self, number, sender=None, conn=None):
        """Remove rule from firewall"""
        dbus_info_aux = dbus.Interface(conn.get_object('org.freedesktop.DBus', '/org/freedesktop/DBus/Bus', False), 'org.freedesktop.DBus')
        if ( self.__caller_pid__ == 0 ) or ( self.__caller_pid__ != dbus_info_aux.GetConnectionUnixProcessID(sender) ):
            return "no_access"
        
        cmd = "ufw --force delete &number".replace("&number", number)
        commands.getstatusoutput(cmd)
        return cmd
    
    @dbus.service.method("gufw.SampleInterface",
                     in_signature='ss', out_signature='',
                     sender_keyword='sender', connection_keyword='conn')
    def add_gufw_log(self, gufw_logging, line, sender=None, conn=None):
        """Add a command to Gufw Log"""
        dbus_info_aux = dbus.Interface(conn.get_object('org.freedesktop.DBus', '/org/freedesktop/DBus/Bus', False), 'org.freedesktop.DBus')
        if ( self.__caller_pid__ == 0 ) or ( self.__caller_pid__ != dbus_info_aux.GetConnectionUnixProcessID(sender) ):
            return
            
        if gufw_logging == "enable":
            msg = "[" + time.strftime('%x %X') + "] " + line
            cmd = "echo '&' >> /var/log/gufw_log.txt".replace("&", msg)
            commands.getstatusoutput(cmd)
    
    @dbus.service.method("gufw.SampleInterface",
                     in_signature='', out_signature='i',
                     sender_keyword='sender', connection_keyword='conn')
    def get_number_rules(self, sender=None, conn=None):
        """Get the actual number of rules"""
        dbus_info_aux = dbus.Interface(conn.get_object('org.freedesktop.DBus', '/org/freedesktop/DBus/Bus', False), 'org.freedesktop.DBus')
        if ( self.__caller_pid__ == 0 ) or ( self.__caller_pid__ != dbus_info_aux.GetConnectionUnixProcessID(sender) ):
            return 0
        
        rules = commands.getstatusoutput("LANGUAGE=C ufw status numbered")
        rules_lines = rules[1].split("\n")
        return_number = 0
        
        for rule in rules_lines:
            if rule.find("ALLOW")  != -1 or \
               rule.find("DENY")   != -1 or \
               rule.find("LIMIT")  != -1 or \
               rule.find("REJECT") != -1:
                
                return_number += 1
        
        return return_number
    
    @dbus.service.method("gufw.SampleInterface",
                     in_signature='', out_signature='as',
                     sender_keyword='sender', connection_keyword='conn')
    def get_rule_list(self, sender=None, conn=None):
        """Get all List Rules"""
        return_rules = []
        dbus_info_aux = dbus.Interface(conn.get_object('org.freedesktop.DBus', '/org/freedesktop/DBus/Bus', False), 'org.freedesktop.DBus')
        if ( self.__caller_pid__ == 0 ) or ( self.__caller_pid__ != dbus_info_aux.GetConnectionUnixProcessID(sender) ):
            return return_rules
        
        rules = commands.getstatusoutput("LANGUAGE=C ufw status numbered")
        rules_lines = rules[1].split("\n")
        
        for rule in rules_lines:
            if rule.find("ALLOW")  != -1 or \
               rule.find("DENY")   != -1 or \
               rule.find("LIMIT")  != -1 or \
               rule.find("REJECT") != -1:
                
                rule_aux = rule.split("] ")
                return_rules.append(rule_aux[1])
        
        return return_rules
    
    @dbus.service.method("gufw.SampleInterface",
                     in_signature='', out_signature='as',
                     sender_keyword='sender', connection_keyword='conn')
    def get_listening_report(self, sender=None, conn=None):
        """Get listening report"""
        return_report = []
        dbus_info_aux = dbus.Interface(conn.get_object('org.freedesktop.DBus', '/org/freedesktop/DBus/Bus', False), 'org.freedesktop.DBus')
        if ( self.__caller_pid__ == 0 ) or ( self.__caller_pid__ != dbus_info_aux.GetConnectionUnixProcessID(sender) ):
            return return_report
        
        actual_protocol = "None"
        ufw_report = commands.getstatusoutput("LANGUAGE=C ufw show listening")
        report_lines = ufw_report[1].replace("\n   [","%")
        report_lines = report_lines.split("\n")
        
        for descomponent_report in report_lines:
            # Set actual protocol
            if descomponent_report == "":
                continue
            if descomponent_report.find("tcp6:") != -1:
                actual_protocol = "TCP6"
                continue
            if descomponent_report.find("tcp:") != -1:
                actual_protocol = "TCP"
                continue
            if descomponent_report.find("udp6:") != -1:
                actual_protocol = "UDP6"
                continue
            if descomponent_report.find("udp:") != -1:
                actual_protocol = "UDP"
                continue
                
            policy = "None"
            descomponent_report = descomponent_report.strip()
            descomponent_report = descomponent_report.replace("(","")
            descomponent_report = descomponent_report.replace(")","")
            
            if descomponent_report.find("]") != -1:
                descomponent_policy = descomponent_report.split("]")
                if descomponent_policy[1].find("allow") != -1:
                    policy = "allow"
                elif descomponent_policy[1].find("deny") != -1:
                    policy = "deny"
                elif descomponent_policy[1].find("reject") != -1:
                    policy = "reject"
                elif descomponent_policy[1].find("limit") != -1:
                    policy = "limit"
            
            descomponent_report = descomponent_report.split("%")
            descomponent_fields = descomponent_report[0].split(" ")
            # Order: protocol % port % address % application % policy
            return_report.append(actual_protocol + "%" + descomponent_fields[0] + "%" + descomponent_fields[1] + "%" + descomponent_fields[2] + "%" + policy)
        
        return return_report
    
    @dbus.service.method("gufw.SampleInterface",
                     in_signature='s', out_signature='s',
                     sender_keyword='sender', connection_keyword='conn')
    def get_gufw_log(self, log , sender=None, conn=None):
        """Get Gufw Log"""
        dbus_info_aux = dbus.Interface(conn.get_object('org.freedesktop.DBus', '/org/freedesktop/DBus/Bus', False), 'org.freedesktop.DBus')
        if ( self.__caller_pid__ == 0 ) or ( self.__caller_pid__ != dbus_info_aux.GetConnectionUnixProcessID(sender) ):
            return "no_access"
        
        cmd = commands.getstatusoutput("cat /var/log/gufw_log.txt")
        if cmd[0] != 0:
            return ""
        
        if log == 'local':
            return cmd[1]
        else:
            log_txt = ""
            for line in cmd[1].split('\n'):
                line = line.split('] ')
                if log_txt == "":
                    log_txt = line[1]
                else:
                    log_txt = log_txt + '\n' + line[1]
            return log_txt
    
    @dbus.service.method("gufw.SampleInterface",
                     in_signature='iiisss', out_signature='',
                     sender_keyword='sender', connection_keyword='conn')
    def update_config_file(self, width, height, vpanel, gufw_logging, listening_status, notify_popup, sender=None, conn=None):
        """Save actual FW config when quit Gufw"""
        dbus_info_aux = dbus.Interface(conn.get_object('org.freedesktop.DBus', '/org/freedesktop/DBus/Bus', False), 'org.freedesktop.DBus')
        if ( self.__caller_pid__ == 0 ) or ( self.__caller_pid__ != dbus_info_aux.GetConnectionUnixProcessID(sender) ):
            return
            
        commands.getstatusoutput("mkdir /etc/gufw")
        size = "&1x&2"
        size = size.replace("&1", str(width))
        size = size.replace("&2", str(height))
        commands.getstatusoutput("echo 'sizewin=&' > /etc/gufw/gufw.cfg".replace('&', size))
        commands.getstatusoutput("echo 'vpanel=&' >> /etc/gufw/gufw.cfg".replace('&', str(vpanel)))
        commands.getstatusoutput("echo 'log=&' >> /etc/gufw/gufw.cfg".replace('&', gufw_logging))
        commands.getstatusoutput("echo 'listening=&' >> /etc/gufw/gufw.cfg".replace('&', listening_status))
        commands.getstatusoutput("echo 'notify_popup=&' >> /etc/gufw/gufw.cfg".replace('&', notify_popup))
    
    @dbus.service.method("gufw.SampleInterface",
                     in_signature='bsssssssss', out_signature='s',
                     sender_keyword='sender', connection_keyword='conn')
    def add_rule(self, is_program, insert_number, action, direction, log, protocol, fromip, fromport, toip, toport, sender=None, conn=None):
        """Add rule to firewall"""
        dbus_info_aux = dbus.Interface(conn.get_object('org.freedesktop.DBus', '/org/freedesktop/DBus/Bus', False), 'org.freedesktop.DBus')
        if ( self.__caller_pid__ == 0 ) or ( self.__caller_pid__ != dbus_info_aux.GetConnectionUnixProcessID(sender) ):
            return "no_access"
        
        # Component rule
        if is_program:
            rule = "ufw insert &insert &action &direction &log proto &protocol from &fromIP port &fromPort to &toIP port &toPort"
        else:
            rule = "ufw insert &insert &action &direction &log &toPort" 
        # Insert Number
        if insert_number != "0":
            rule = rule.replace("&insert", insert_number)
        else:
            rule = rule.replace("insert &insert ", "")
        # Action
        rule = rule.replace("&action", action)
        # Direction
        rule = rule.replace("&direction", direction)
        # Log
        if log != "log-default":
            rule = rule.replace("&log", log)
        else:
            rule = rule.replace("&log ", "")
        # Protocol
        if protocol != "both":
            rule = rule.replace("&protocol", protocol)
        else:
            rule = rule.replace(" proto &protocol ", " ")
        # FROM
        if fromip != "":
            rule = rule.replace("&fromIP", fromip)
        else:
            rule = rule.replace("&fromIP", "any")
        if fromport != "":
            rule = rule.replace("&fromPort", fromport)
        else:
            rule = rule.replace(" port &fromPort ", " ")
        # TO
        if toip != "":
            rule = rule.replace("&toIP", toip)
        else:
            rule = rule.replace("&toIP", "any")
        if toport != "":
            rule = rule.replace("&toPort", toport)
        else:
            rule = rule.replace(" port &toPort", "")
        
        commands.getstatusoutput(rule)
        return rule


if __name__ == '__main__':
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
    
    bus = dbus.SystemBus()
    name = dbus.service.BusName("gufw.Daemon", bus)
    object = Gufw_daemon(bus, '/Gufw_daemon')

    mainloop = GObject.MainLoop()
    mainloop.run()
