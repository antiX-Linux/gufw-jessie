# -*- coding: utf-8 -*-
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

import gettext
import threading
import webbrowser

from gi.repository import Gtk, Gdk, GLib
from gi.repository import GObject
from gi.repository import Polkit
import dbus

from util import Path

from gettext import gettext as _
gettext.textdomain('gufw')

__color__ = { "gray"   : "#BAB5AB",  # Basic 3D Medium
              "green"  : "#267726",  # Accent Green Dark
              "red"    : "#DF421E",  # Accent Red
              "orange" : "#D1940C",  # Accent Yellow Dark
              "blue"   : "#314E6C" } # Blue Shadow


class GuiGufw:
    """All events"""
    FONT = "ubuntu 10"
    TIME_REFRESH_REPORT = 2500
    TIME_STATUS_BAR = 8
    
    def __init__(self, firewall):
        self.fw = firewall
        self.path = Path()
        self.ui_builder = Gtk.Builder()
        self._set_ui(self.ui_builder)
        GLib.set_application_name("Gufw")
        Gtk.main()
    
    def _set_ui(self, builder):
        """Set the interfaces"""
        builder.set_translation_domain("gufw")
        # Set windows
        self._set_ui_main(builder)
        self._set_ui_models(builder)
        self._set_ui_add(builder)
        self._set_ui_preferences(builder)
        self._set_ui_log(builder)
        self.win_main.show()
    
    def _set_ui_main(self, builder):
        """Set the window Main"""
        self.first_run_report = True
        self.previous_report = []
        builder.add_from_file(self.path.get_ui_path('main.ui'))
        self.win_main = builder.get_object('winMain')
        # Window size
        width, height = self.fw.get_window_size()
        if width == Gdk.Screen.width() and height== Gdk.Screen.height():
            self.win_main.maximize()
        else:
            self.win_main.resize(width, height)
        # Icon
        self.win_main.set_default_icon_from_file("/usr/share/icons/hicolor/48x48/apps/gufw.png")
        # Switch ON/OFF
        self.switchFirewall = builder.get_object("switchStatus")
        # Panel
        self.panelmain = builder.get_object("panelListeningRules")
        self.panelmain.set_position(self.fw.get_vpanel_pos())
        # Main Window Objects 
        self.cb_policy_incoming  = builder.get_object("cbPolicyIncoming")
        self.cb_policy_outgoing  = builder.get_object("cbPolicyOutgoing")
        self.image_shield        = builder.get_object("imgShield")
        self.block_report        = builder.get_object("blockReport")
        self.btn_add_window      = builder.get_object("btnAddWindow")
        self.btn_remove_rule     = builder.get_object("btnRemove")
        self.status_bar          = builder.get_object("statusBar")
        self.progress_bar        = builder.get_object("progressBar")
        self.progress_bar_block  = builder.get_object("progressBarBlock")
        self.btn_unlock          = builder.get_object("btnUnlock")
        # Needed for firewall switch & lock button
        self.block_status        = builder.get_object("blockStatus")
        # Objects for Global Menu in Unity
        self.menu_file      = builder.get_object("menu_file")
        self.menu_edit      = builder.get_object("menu_edit")
        self.menu_help      = builder.get_object("menu_help")
        # Menu
        self.menu_log       = builder.get_object("menuLog")
        self.menu_quit      = builder.get_object("actionQuit")
        self.menu_add       = builder.get_object("menuAdd")
        self.menu_remove    = builder.get_object("menuRemove")
        self.menu_reload    = builder.get_object("menuReload")
        self.menu_reset     = builder.get_object("menuReset")
        self.menu_pref      = builder.get_object("menuPreferences")
        self.menu_doc       = builder.get_object("menuDoc")
        self.menu_answers   = builder.get_object("menuAnswers")
        self.menu_bug       = builder.get_object("menuBug")
        self.menu_translate = builder.get_object("menuTranslate")
        self.menu_about     = builder.get_object("actionAbout")
        # Set minimal signals to launch Gufw
        self.win_main.connect('delete-event', self.on_winMain_delete_event)
        self.menu_quit.connect('activate', self.on_menuQuit_activate)
        self.menu_about.connect('activate', self.on_menuAbout_activate)
        self.btn_unlock.connect('clicked', self.on_btnUnlock_clicked)
        # Show Listening report
        if self.fw.get_listening_status() == "enable":
            self.block_report.show()
        # Focus
        self.btn_unlock.grab_focus()
            
    def _set_ui_models(self, builder):
        """Set the models in main window"""
        self.render_txt = Gtk.CellRendererText()
        self.render_txt.set_property("font", self.FONT)
        
        self.rules_model = Gtk.ListStore(GObject.TYPE_INT,    GObject.TYPE_STRING, GObject.TYPE_STRING,
                                         GObject.TYPE_STRING, GObject.TYPE_STRING)
        
        self.tv_rules = builder.get_object("tvRules")
        self.tv_rules.set_model(self.rules_model)
        self.tv_rules.get_selection().set_mode(Gtk.SelectionMode.MULTIPLE)
        
        tree_header = Gtk.TreeViewColumn (_("To"), self.render_txt, text=1, foreground=4)
        tree_header.set_expand(True)
        tree_header.set_resizable(True)
        self.tv_rules.append_column (tree_header)
        tree_header = Gtk.TreeViewColumn (_("Action"), self.render_txt, text=2, foreground=4)
        tree_header.set_expand(True)
        tree_header.set_resizable(True)
        self.tv_rules.append_column (tree_header)
        tree_header = Gtk.TreeViewColumn (_("From"), self.render_txt, text=3, foreground=4)
        tree_header.set_expand(True)
        self.tv_rules.append_column (tree_header)
        
        # Listening Report
        self.report_model = Gtk.ListStore(GObject.TYPE_INT,    GObject.TYPE_STRING, GObject.TYPE_STRING,
                                          GObject.TYPE_STRING, GObject.TYPE_STRING, GObject.TYPE_STRING) 
        self.tv_report = builder.get_object("tvReport")
        self.tv_report.set_model(self.report_model)
        self.tv_report.get_selection().set_mode(Gtk.SelectionMode.NONE)
        
        tree_header = Gtk.TreeViewColumn (_("Protocol"), self.render_txt, text=1, foreground=5)
        tree_header.set_resizable(True)
        self.tv_report.append_column (tree_header)
        tree_header = Gtk.TreeViewColumn (_("Port"), self.render_txt, text=2, foreground=5)
        tree_header.set_resizable(True)
        self.tv_report.append_column (tree_header)
        tree_header = Gtk.TreeViewColumn (_("Address"), self.render_txt, text=3, foreground=5)
        tree_header.set_resizable(True)
        self.tv_report.append_column (tree_header)
        tree_header = Gtk.TreeViewColumn (_("Application"), self.render_txt, text=4, foreground=5)
        self.tv_report.append_column (tree_header)
    
    def _set_ui_add(self, builder):
        """Set the window Add"""
        builder.add_from_file(self.path.get_ui_path('add.ui'))
        self.dlg_add = builder.get_object('dlgAdd')
        self.dlg_add.set_transient_for(self.win_main)
        # Preconf
        self.insert_number_preconf = builder.get_object("sbInsertNumberPreconf")
        self.direction_preconf     = builder.get_object("cbDirectionPreconf")
        self.direction_preconf.set_active(0)
        self.action_preconf        = builder.get_object("cbActionPreconf")
        self.action_preconf.set_active(0)
        self.log_preconf           = builder.get_object("cbLogPreconf")
        self.log_preconf.set_active(0)
        self.type_preconf          = builder.get_object("cbTypePreconf")
        self.type_preconf.set_active(0)
        self.program_preconf       = builder.get_object("cbProgramPreconf")
        self.program_preconf.set_active(6)
        self.service_preconf       = builder.get_object("cbServicePreconf")
        self.service_preconf.set_active(7)

        # Simple
        self.insert_number_simple = builder.get_object("sbInsertNumberSimple")
        self.direction_simple     = builder.get_object("cbDirectionSimple")
        self.direction_simple.set_active(0)
        self.action_simple        = builder.get_object("cbActionSimple")
        self.action_simple.set_active(0)
        self.log_simple           = builder.get_object("cbLogSimple")
        self.log_simple.set_active(0)
        self.port_simple          = builder.get_object("entryPortSimple")
        self.proto_simple         = builder.get_object("cbProtoSimple")
        self.proto_simple.set_active(0)
        # Advanced
        self.insert_number_advanced = builder.get_object("sbInsertNumberAdvanced")
        self.action_advanced        = builder.get_object("cbActionAdvanced")
        self.action_advanced.set_active(0)
        self.direction_advanced     = builder.get_object("cbDirectionAdvanced")
        self.direction_advanced.set_active(0)
        self.log_advanced           = builder.get_object("cbLogAdvanced")
        self.log_advanced.set_active(0)
        self.proto_advanced         = builder.get_object("cbProtoAdvanced")
        self.proto_advanced.set_active(0)
        self.fromip_advanced        = builder.get_object("entryFromIpAdvanced")
        self.portfrom_advanced      = builder.get_object("entryPortFromAdvanced")
        self.toip_advanced          = builder.get_object("entryToIpAdvanced")
        self.portto_advanced        = builder.get_object("entryPortToAdvanced")
        # Others
        self.rules_notebook   = builder.get_object("rulesNotebook")
        self.add_btn_add      = builder.get_object("btnAddRule")
        self.extended_actions = builder.get_object("cbExtendedActions")
        
    def _set_ui_preferences(self, builder):
        """Set the window Preferences"""
        builder.add_from_file(self.path.get_ui_path('preferences.ui'))
        self.dlg_preferences = builder.get_object('dlgPreferences')
        self.dlg_preferences.set_transient_for(self.win_main)
        # Preference Window
        self.cb_report       = builder.get_object("cbReport")
        self.cb_notify_popup = builder.get_object("cbNotifyPopup")
        self.lbl_ufw_level   = builder.get_object("lblLogLevel")
        self.cb_ufw_level    = builder.get_object("cbLogLevel")
        self.cb_gufw_log     = builder.get_object("cbGufwLog") 
        self.pref_btn_close  = builder.get_object("btnClosePref")
            
    def _set_ui_log(self, builder):
        """Set the window Log"""
        builder.add_from_file(self.path.get_ui_path('log.ui'))
        self.dlg_log = builder.get_object('dlgLog')
        self.dlg_log.set_transient_for(self.win_main)
        # Log Window
        self.log_txt        = builder.get_object("logTxt")
        self.log_txt_buffer = self.log_txt.get_buffer()
        self.log_btn_close  = builder.get_object("btnCloseLog")
        self.server_script  = builder.get_object("cbServerScript")
    
    def _set_main_values(self, statusbar_msg):
        """Set initial status for GUI"""
        # Set sensitive values by status firewall
        if self.fw.get_status() == "enable":
            # Shield / Dropbox / Buttons / Menus
            incoming = self.fw.get_policy("incoming")
            outgoing = self.fw.get_policy("outgoing")
            self.image_shield.set_from_file(self.path.get_shield_path(incoming, outgoing))
            self.cb_policy_incoming.set_sensitive(True)
            self.cb_policy_outgoing.set_sensitive(True)
            self.add_btn_add.set_sensitive(True)
            if self.fw.get_number_rules() == 0:
                self.btn_remove_rule.set_sensitive(False)
                self.menu_remove.set_sensitive(False)
            else:
                self.btn_remove_rule.set_sensitive(True)
                self.menu_remove.set_sensitive(True)
        else:
            # Shield / Dropbox / Buttons / Menus
            self.image_shield.set_from_file(self.path.get_shield_path("disable", "disable"))
            self.cb_policy_incoming.set_sensitive(False)
            self.cb_policy_outgoing.set_sensitive(False)
            self.add_btn_add.set_sensitive(False)
            self.btn_remove_rule.set_sensitive(False)
            self.menu_remove.set_sensitive(False)
        # Gufw menu sensitive values by Gufw Log status
        if self.fw.get_gufw_logging() == "enable":
            self.menu_log.set_sensitive(True)
        else:
            self.menu_log.set_sensitive(False)
        # Rules
        self._set_rules_list()
        # StatusBar
        self._set_statusbar_msg(statusbar_msg)
    
    def _set_statusbar_msg(self, msg):
        cid = self.status_bar.get_context_id('default context')
        mid = self.status_bar.push(cid, msg)
        GObject.timeout_add_seconds(self.TIME_STATUS_BAR, self.status_bar.remove, cid, mid)
    
    def _set_rules_list(self):
        """Set rules in main window"""
        row = 0
        self.rules_model.clear()
        rules = self.fw.get_rule_list()
        for rule in rules:
            row += 1
            iterador = self.rules_model.insert(row)
            # Set value txt
            rule_formated = self._get_format_rules_txt(rule)
            # Get color
            color = self._get_rule_color(rule_formated[1])            
            # Set values
            self.rules_model.set_value(iterador, 0, row) # Use for remove rule
            self.rules_model.set_value(iterador, 1, _(rule_formated[0].strip()))
            self.rules_model.set_value(iterador, 2, _(rule_formated[1].strip()))
            self.rules_model.set_value(iterador, 3, _(rule_formated[2].strip()))
            self.rules_model.set_value(iterador, 4, color) # Foreground color rule
    
    def _get_rule_color(self, rule):
        """Return color rule"""
        # Color Allow/Deny/Reject/Limit
        # IN mode (equal to normal mode, persist code for clear read)
        if rule == "ALLOW IN":
            if self.fw.get_policy("incoming") != "allow":
                return __color__["red"]
            else:
                return __color__["gray"]
        # Deny?
        elif rule == "DENY IN":
            if self.fw.get_policy("incoming") != "deny":
                return __color__["green"]
            else:
                return __color__["gray"]
        # Reject
        elif rule == "REJECT IN":
            if self.fw.get_policy("incoming") != "reject":
                return __color__["blue"]
            else:
                return __color__["gray"]
        # Limit?
        elif rule == "LIMIT IN":
            return __color__["orange"]
        
        # OUT mode
        elif rule == "ALLOW OUT": 
            if self.fw.get_policy("outgoing") != "allow":
                return __color__["red"]
            else:
                return __color__["gray"]
        # Deny?
        elif rule == "DENY OUT":
            if self.fw.get_policy("outgoing") != "deny":
                return __color__["green"]
            else:
                return __color__["gray"]
        # Reject
        elif rule == "REJECT OUT":
            if self.fw.get_policy("outgoing") != "reject":
                return __color__["blue"]
            else:
                return __color__["gray"]
        # Limit?
        elif rule == "LIMIT OUT":
            return __color__["orange"]
            
        # NORMAL mode
        # Allow?
        elif rule == "ALLOW": 
            if self.fw.get_policy("incoming") != "allow":
                return __color__["red"]
            else:
                return __color__["gray"]
        # Deny?
        elif rule == "DENY":
            if self.fw.get_policy("incoming") != "deny":
                return __color__["green"]
            else:
                return __color__["gray"]
        # Reject
        elif rule == "REJECT":
            if self.fw.get_policy("incoming") != "reject":
                return __color__["blue"]
            else:
                return __color__["gray"]
        # Limit?
        elif rule == "LIMIT":
            return __color__["orange"]
        
    def _get_format_rules_txt(self, rule):
        # IN mode (equal to normal mode, persist code for clear read)
        if rule.find("ALLOW IN") != -1:
            split_str = "ALLOW IN"
        # Deny?
        elif rule.find("DENY IN") != -1:
            split_str = "DENY IN"
        # Reject
        elif rule.find("REJECT IN") != -1:
            split_str = "REJECT IN"
        # Limit?
        elif rule.find("LIMIT IN") != -1:
            split_str = "LIMIT IN"
        
        # OUT mode
        elif rule.find("ALLOW OUT") != -1: 
            split_str = "ALLOW OUT"
        # Deny?
        elif rule.find("DENY OUT") != -1:
            split_str = "DENY OUT"
        # Reject
        elif rule.find("REJECT OUT") != -1:
            split_str = "REJECT OUT"
        # Limit?
        elif rule.find("LIMIT OUT") != -1:
            split_str = "LIMIT OUT"
            
        # NORMAL mode
        # Allow?
        elif rule.find("ALLOW") != -1: 
            split_str = "ALLOW"
        # Deny?
        elif rule.find("DENY") != -1:
            split_str = "DENY"
        # Reject
        elif rule.find("REJECT") != -1:
            split_str = "REJECT"
        # Limit?
        elif rule.find("LIMIT") != -1:
            split_str = "LIMIT"
        
        # Values
        rule_split = rule.split(split_str)
        return rule_split[0].strip(), split_str, rule_split[1].strip()
    
    def _do_refresh_report(self):
        """Refresh method in background (no freeze)"""
        if self.fw.get_listening_status() == "disable":
            self.previous_report = []
            self.first_run_report = True
            self.report_model.clear()
            return False
        
        lines = self.fw.get_listening_report()
        background_job = RefreshReport(self.fw.get_status(), self.report_model, lines, self.previous_report, self.first_run_report, self.fw.get_notify_popup())
        background_job.start()
        self.previous_report = lines
        if self.fw.get_listening_status() == "enable":
            self.first_run_report = False
            return True
        
    def _refresh_report(self):
        """Refresh Listening Report"""
        GObject.timeout_add(self.TIME_REFRESH_REPORT, self._do_refresh_report)
        
    def _remove_rule(self):
        """Remove Rules Method"""
        number_rules = self.fw.get_number_rules()
        tree, iter = self.tv_rules.get_selection().get_selected_rows()
        removed = 0
        actual_row = 0
        total_rows = len(iter)
           
        if total_rows == 0:
            self._set_main_values(_("Select rule(s)"))
            yield None
            return

        # No sensitive buttons & msg
        self.progress_bar_block.show()
        self.switchFirewall.set_sensitive(False)
        self.cb_policy_incoming.set_sensitive(False)
        self.cb_policy_outgoing.set_sensitive(False)
        self.btn_remove_rule.set_sensitive(False)
        self.menu_remove.set_sensitive(False)
        self.add_btn_add.set_sensitive(False)
        self.menu_pref.set_sensitive(False)
        self.menu_reload.set_sensitive(False)
        self.menu_reset.set_sensitive(False)
        self._set_statusbar_msg(_("Removing rules..."))

        # For one row selected
        iter.reverse() # Remove first the last rules for not overwrite rules
        for item in iter:
            
            # Get rule selected (row number)
            number_rule_row = tree.get_value(tree.get_iter(item), 0)
            
            # Move Progress Bar
            actual_row += 1
            progress = float(actual_row) / float(total_rows)
            if progress > 1:
                progress = 1.0
            self.progress_bar.set_fraction(progress)
            yield True
            
            self.fw.remove_rule(number_rule_row)

        # Clean Progress Bar
        self.progress_bar.set_fraction(0)
        self.progress_bar_block.hide()
        self.switchFirewall.set_sensitive(True)
        self.menu_pref.set_sensitive(True)
        self.menu_reload.set_sensitive(True)
        self.menu_reset.set_sensitive(True)
        
        if number_rules != self.fw.get_number_rules():
            self._set_main_values(_("Rule(s) removed"))
        else:
            self._set_main_values(_("Error performing operation"))
        
        yield None

    def _add_rule_preconf(self):
        """Add a preconfigured rule"""
        number_rules = self.fw.get_number_rules()
        # Insert Number
        if self.extended_actions.get_active() != 0: # Visible?
            insert_number = str(self.insert_number_preconf.get_value_as_int())
        else:
            insert_number = "0"
        # Allow|deny|Limit
        if self.action_preconf.get_active() == 0:
            action = "allow"
        elif self.action_preconf.get_active() == 1:
            action = "deny"
        elif self.action_preconf.get_active() == 2:
            action = "reject"
        else:
            action = "limit"
        # IN/OUT
        if self.direction_preconf.get_active() == 0:
            direction = "in"
        else:
            direction = "out"
        # Log
        log = "log-default"
        if self.extended_actions.get_active() != 0: # Visible?
            if self.log_preconf.get_active() == 1:
                log = "log"
            elif self.log_preconf.get_active() == 2:
                log = "log-all"
        
        # Service?
        if self.type_preconf.get_active() == 1:
            SERVICES = { 0 : "ftp",
                         1 : "http",
                         2 : "https",
                         3 : "imap",
                         4 : "nfs",
                         5 : "pop3",
                         #Samba > Changes number? > Changes hack below
                         6 : "135,139,445tcp|137,138udp",
                         7 : "smtp",
                         8 : "ssh",
                         #VNC
                         9 : "5900tcp",
                         #CUPS
                         10: "631" }
            service_txt = SERVICES[self.service_preconf.get_active()]
            all_ports = service_txt.split("|")
            for port_proto in all_ports:
                if port_proto.find("tcp") != -1:
                    port     = port_proto.replace("tcp", "")
                    protocol = "tcp"
                    is_program = True
                elif port_proto.find("udp") != -1:
                    port     = port_proto.replace("udp", "")
                    protocol = "udp"
                    is_program = True
                elif port_proto.find("both") != -1:
                    port     = port_proto.replace("both", "")
                    protocol = "both"
                    is_program = True
                else:
                    port     = port_proto
                    protocol = ""
                    is_program = False
                
                self.fw.add_rule(is_program, insert_number, action, direction, log, protocol, "", "", "", port)
                if self.service_preconf.get_active() == 6: #Samba > Special command. Bug #72444
                    self.fw.add_rule(is_program, insert_number, action, "", log, protocol, "any", port, "", "")
            
            if number_rules != self.fw.get_number_rules():
                self._set_main_values(_("Rule added"))
            else:
                self._set_main_values(_("Error performing operation"))
                
        # Program?
        else:
            PROGRAMS = { #Amule        
                         0 : "4662tcp#4672udp",
                         #Deluge
                         1 : "6881:6891tcp#6881:6891udp",
                         #KTorrent
                         2 : "6881tcp#4444udp",
                         #Nicotine
                         3 : "2234:2239tcp#2242tcp#2240tcp",
                         #qBittorent
                         4 : "6881tcp#6881udp",
                         #Skype
                         5 : "443tcp",
                         #Transmission
                         6 : "51413tcp#51413udp",
                         #Ubuntu One
                         7 : "443tcp#443udp" }
            port_proto = PROGRAMS[self.program_preconf.get_active()]
            ports_protos = port_proto.split("#")
            for prog in ports_protos:
                if prog.find("tcp") != -1:
                    port     = prog.replace("tcp", "")
                    protocol = "tcp"
                elif prog.find("udp") != -1:
                    port     = prog.replace("udp", "")
                    protocol = "udp"
                elif prog.find("both") != -1:
                    port     = prog.replace("both", "")
                    protocol = "both"
                    
                self.fw.add_rule(True, insert_number, action, direction, log, protocol, "", "", "", port)
                    
            if number_rules != self.fw.get_number_rules(): 
                self._set_main_values(_("Rule added"))
            else:
                self._set_main_values(_("Error performing operation"))
    
    def _add_rule_simple(self):
        """Add a simple rule"""
        number_rules = self.fw.get_number_rules()
        # Insert Number
        if self.extended_actions.get_active() != 0: # Visible?
            insert_number = str(self.insert_number_simple.get_value_as_int())
        else:
            insert_number = "0"
        # Allow|deny|Limit
        if self.action_simple.get_active() == 0:
            action = "allow"
        elif self.action_simple.get_active() == 1:
            action = "deny"
        elif self.action_simple.get_active() == 2:
            action = "reject"
        else:
            action = "limit"
        # IN/OUT
        if self.direction_simple.get_active() == 0:
            direction = "in"
        else:
            direction = "out"
        # Log
        log = "log-default"
        if self.extended_actions.get_active() != 0: # Visible?
            if self.log_simple.get_active() == 1:
                log = "log"
            elif self.log_simple.get_active() == 2:
                log = "log-all"
        # Protocol
        if self.proto_simple.get_active() == 0:
            protocol = "tcp"
        elif self.proto_simple.get_active() == 1:
            protocol = "udp"
        else:
            protocol = "both"
        # Port
        port = self.port_simple.get_text()
        # ? -> ! Don't read the next!!
        if port == "stallman":
            dlg_egg = Gtk.MessageDialog(self.win_main, 
            Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
            Gtk.MessageType.WARNING, Gtk.ButtonsType.CLOSE, 
            "'Value your freedom or you will lose it,' teaches history.\n'Don't bother us with politics,' respond those who \ndon't want to learn.")
            dlg_egg.format_secondary_markup("Richard Stallman")
            dlg_egg.set_title("It's time to think!")
            dlg_egg.run()
            dlg_egg.destroy()
            return
        # Validate port
        if port == "":
            self._set_statusbar_msg(_("Error: Insert a port number"))
            return
        # Validate both and not range ports
        if ( port.find(":") != -1 ) and protocol == "both":
            self._set_statusbar_msg(_("Error: Range ports only with tcp or udp protocol"))
            return
        # Add rule
        self.fw.add_rule(True, insert_number, action, direction, log, protocol, "", "", "", port)
        
        if number_rules != self.fw.get_number_rules():
            self._set_main_values(_("Rule added"))
        else:
            self._set_main_values(_("Error performing operation"))
        
    def _add_rule_advanced(self):
        """Add an advanced rule"""
        number_rules = self.fw.get_number_rules()
        # Insert Number
        if self.extended_actions.get_active() != 0: # Visible?
            insert_number = str(self.insert_number_advanced.get_value_as_int())
        else:
            insert_number = "0"
        # Deny|Reject|Allow|Limit
        if self.action_advanced.get_active() == 0:
            action = "allow"
        elif self.action_advanced.get_active() == 1:
            action = "deny"
        elif self.action_advanced.get_active() == 2:
            action = "reject"
        else:
            action = "limit"
        # IN/OUT
        if self.direction_advanced.get_active() == 0:
            direction = "in"
        else:
            direction = "out"
        # Log
        log = "log-default"
        if self.extended_actions.get_active() != 0: # Visible?
            if self.log_advanced.get_active() == 1:
                log = "log"
            elif self.log_advanced.get_active() == 2:
                log = "log-all"
        # Protocol
        if self.proto_advanced.get_active() == 0:
            protocol = "tcp"
        elif self.proto_advanced.get_active() == 1:
            protocol = "udp"
        else:
            protocol = "both"
        # From
        fromip   = self.fromip_advanced.get_text()
        fromport = self.portfrom_advanced.get_text()
        # To
        toip   = self.toip_advanced.get_text()
        toport = self.portto_advanced.get_text() 
        # Validate values
        if fromip == "" and fromport == "" and toip == "" and toport == "":
            self._set_statusbar_msg(_("Error: Fields filled out incorrectly"))
            return
        # Validate both and not range ports in FROM
        if ( fromport != "" and fromport.find(":") != -1 ) and protocol == "both":
            self._set_statusbar_msg(_("Error: Range ports only with tcp or udp protocol"))
            return
        # Validate both and not range ports in TO            
        if ( toport != "" and toport.find(":") != -1 ) and protocol == "both":
            self._set_statusbar_msg(_("Error: Range ports only with tcp or udp protocol"))
            return
        # Add rule program
        result = self.fw.add_rule(True, insert_number, action, direction, log, protocol, fromip, fromport, toip, toport)
        if number_rules != self.fw.get_number_rules():
            self._set_main_values(_("Rule added"))
        else:
            self._set_main_values(_("Error performing operation"))
    
    def on_btnAddWindow_clicked(self, widget):
        """Button Add"""
        self.btn_add_window.set_sensitive(False)
        self.menu_add.set_sensitive(False)
        self.dlg_add.show()
    
    def on_btnCloseAdd_clicked(self, widget):
        """Button Close Add Rules"""
        self.btn_add_window.set_sensitive(True)
        self.menu_add.set_sensitive(True)
        self.dlg_add.hide()
        return True
    
    def on_btnClosePref_clicked(self, widget):
        """Closes preferences dialog when close button is clicked."""
        self.dlg_preferences.hide()
        return True

    def on_dlgPref_delete_event(self, widget, event):
        """Closes preferences dialog for all close events except clicking the 
        close button.
        """
        self.dlg_preferences.hide()
        return True

    def on_btnCloseLog_clicked(self, widget):
        """Closes log dialog when close button is clicked"""
        self.dlg_log.hide()
        return True

    def on_dlgLog_delete_event(self, widget, event):
        """Closes log dialog for all close events except clicking the 
        close button.
        """
        self.dlg_log.hide()
        return True

    def on_btnClearLog_clicked(self, widget):
        """Clear Log"""
        self.fw.erase_gufw_log()
        self.log_txt_buffer.set_text("")
        self.log_btn_close.grab_focus()

    def on_btnRemove_clicked(self, widget):
        """Remove rules in background"""
        task = self._remove_rule()
        GObject.idle_add(task.next)
    
    def on_btnAddRule_clicked(self, widget):
        """Add rule Button"""
        # Simple rule
        if self.rules_notebook.get_current_page() == 0:
            self._add_rule_preconf()
        # Preconfigured rule
        elif self.rules_notebook.get_current_page() == 1:
            self._add_rule_simple()
        # Advanced rule
        elif self.rules_notebook.get_current_page() == 2:
            self._add_rule_advanced()
    
    def on_btnCleanAdvanced_clicked(self, widget):
        """Clear values in advanced tab"""
        self.fromip_advanced.set_text("")
        self.portfrom_advanced.set_text("")
        self.toip_advanced.set_text("")
        self.portto_advanced.set_text("")
    
    def on_btnUnlock_clicked(self, widget):
        if self.fw.unlock() == "access":
            self._set_initial_objects_main()
            self._set_initial_objects_preferences()
            self._set_main_values("")
            self.ui_builder.connect_signals(self)
            # Glade event button_press_event not works with keyboard. Future TODO: Remove this line
            self.switchFirewall.connect("notify::active", self.on_switchFirewall_toggled)
            self._refresh_report()
        else:
            self._set_statusbar_msg(_("Wrong identification"))
        
    def _set_initial_objects_main(self):
        """Set the initial "unlocked" status"""
        # Hiden buttons
        self.btn_unlock.hide()
        # Sensitive buttons
        self.menu_add.set_sensitive(True)
        self.menu_reload.set_sensitive(True)
        self.menu_reset.set_sensitive(True)
        self.menu_pref.set_sensitive(True)
        self.btn_add_window.set_sensitive(True)
        # Problems with Glade events
        self.menu_doc.set_sensitive(True)
        self.menu_answers.set_sensitive(True)
        self.menu_bug.set_sensitive(True)
        self.menu_translate.set_sensitive(True)
        # Status
        self.switchFirewall.set_sensitive(True)
        if self.fw.get_status() == "enable":
            self.switchFirewall.set_active(True)
        else:
            self.switchFirewall.set_active(False)
        # Policy
        incoming = self.fw.get_policy("incoming")
        outgoing = self.fw.get_policy("outgoing")
        if incoming == "deny":
            self.cb_policy_incoming.set_active(0)
        elif incoming == "reject":
            self.cb_policy_incoming.set_active(1)
        elif incoming == "allow":
            self.cb_policy_incoming.set_active(2)
        if outgoing == "deny":
            self.cb_policy_outgoing.set_active(0)
        elif outgoing == "reject":
            self.cb_policy_outgoing.set_active(1)
        elif outgoing == "allow":
            self.cb_policy_outgoing.set_active(2)
    
    def _set_initial_objects_preferences(self):
        """Set the initial "locked" status"""
        # Listening report
        if self.fw.get_listening_status() == "enable":
            self.cb_report.set_active(True)
        else:
            self.cb_report.set_active(False)
            self.cb_notify_popup.set_sensitive(False)            
        # Show Notify popups
        if self.fw.get_notify_popup() == "enable":
            self.cb_notify_popup.set_active(True)
        else:
            self.cb_notify_popup.set_active(False)
        # ufw Log
        if self.fw.get_ufw_logging() == "off":
            self.cb_ufw_level.set_active(0)
        elif self.fw.get_ufw_logging() == "low":
            self.cb_ufw_level.set_active(1)
        elif self.fw.get_ufw_logging() == "medium":
            self.cb_ufw_level.set_active(2)
        elif self.fw.get_ufw_logging() == "high":
            self.cb_ufw_level.set_active(3)
        else:
            self.cb_ufw_level.set_active(4)
        if self.fw.get_status() == "disable":
            self.cb_ufw_level.set_sensitive(False)
            self.lbl_ufw_level.set_sensitive(False)
        # Gufw Log
        if self.fw.get_gufw_logging() == "enable":
            self.cb_gufw_log.set_active(True)
        else:
            self.cb_gufw_log.set_active(0)
    
    def on_cbLogLevel_changed(self, widget):
        """Change Logging Level"""
        if ( self.cb_ufw_level.get_active() == 0 ):
            self.fw.set_ufw_logging("off")
        elif ( self.cb_ufw_level.get_active() == 1 ):
            self.fw.set_ufw_logging("low")
        elif ( self.cb_ufw_level.get_active() == 2 ):
            self.fw.set_ufw_logging("medium")
        elif ( self.cb_ufw_level.get_active() == 3 ):
            self.fw.set_ufw_logging("high")
        elif ( self.cb_ufw_level.get_active() == 4 ):
            self.fw.set_ufw_logging("full")
    
    def on_cbGufwLog_toggled(self, widget):
        """Gufw Log CheckButton"""
        if self.cb_gufw_log.get_active() == 1:
            self.fw.set_gufw_logging("enable")
            self.menu_log.set_sensitive(True)
        elif self.cb_gufw_log.get_active() == 0:
            self.fw.set_gufw_logging("disable")
            self.menu_log.set_sensitive(False)
    
    def on_cbReport_toggled(self, widget):
        """Listening report"""
        if self.cb_report.get_active() == 1:
            self.fw.set_listening_status("enable")
            self.cb_notify_popup.set_sensitive(True)
            self.block_report.show()
        else:
            self.fw.set_listening_status("disable")
            self.cb_notify_popup.set_sensitive(False)
            self.block_report.hide()
        self._refresh_report()
    
    def on_cbNotifyPopup_toggled(self, widget):
        """Show Notify Popups for Listening reports"""
        if self.cb_notify_popup.get_active() == 1:
            self.fw.set_notify_popup("enable")
        else:
            self.fw.set_notify_popup("disable")
        
    def on_cbServerScript_toggled(self, widget):
        """View Gufw Log as Server Script"""
        if self.server_script.get_active():
            self.log_txt_buffer.set_text(self.fw.get_gufw_log('server'))
        else:
            self.log_txt_buffer.set_text(self.fw.get_gufw_log('local'))
    
    def on_switchFirewall_toggled(self, widget, data):
        """Changed FW Status"""
        if self.switchFirewall.get_active() == True:
            self.fw.set_status("enable")
            self.cb_ufw_level.set_sensitive(True)
            self.lbl_ufw_level.set_sensitive(True)            
            self._set_main_values(_("Enabled firewall"))
        else:
            self.fw.set_status("disable")
            self.cb_ufw_level.set_sensitive(False)
            self.lbl_ufw_level.set_sensitive(False)
            self._set_main_values(_("Disabled firewall"))
    
    def on_cbPolicyIncoming_changed(self, widget):
        """Policy (Deny/Allow/Reject All) Incoming"""
        # Apply?
        if self.fw.get_policy("incoming") == "deny" and self.cb_policy_incoming.get_active() == 0:
            return
        if self.fw.get_policy("incoming") == "reject" and self.cb_policy_incoming.get_active() == 1:
            return
        if self.fw.get_policy("incoming") == "allow" and self.cb_policy_incoming.get_active() == 2:
            return
        
        if self.cb_policy_incoming.get_active() == 0:
            self.fw.set_policy("incoming", "deny")
            self._set_main_values(_("Deny all INCOMING traffic"))
            return
        elif self.cb_policy_incoming.get_active() == 1:
            self.fw.set_policy("incoming", "reject")
            self._set_main_values(_("Reject all INCOMING traffic"))
            return
        elif self.cb_policy_incoming.get_active() == 2:
            self.fw.set_policy("incoming", "allow")
            self._set_main_values(_("Allow all INCOMING traffic"))
            
    def on_cbPolicyOutgoing_changed(self, widget):
        """Policy (Deny/Allow/Reject All) Outgoing"""
        # Apply?
        if self.fw.get_policy("outgoing") == "deny" and self.cb_policy_outgoing.get_active() == 0:
            return
        if self.fw.get_policy("outgoing") == "reject" and self.cb_policy_outgoing.get_active() == 1:
            return
        if self.fw.get_policy("outgoing") == "allow" and self.cb_policy_outgoing.get_active() == 2:
            return
        
        if self.cb_policy_outgoing.get_active() == 0:
            self.fw.set_policy("outgoing", "deny")
            self._set_main_values(_("Deny all OUTGOING traffic"))
            return
        elif self.cb_policy_outgoing.get_active() == 1:
            self.fw.set_policy("outgoing", "reject")
            self._set_main_values(_("Reject all OUTGOING traffic"))
            return
        elif self.cb_policy_outgoing.get_active() == 2:
            self.fw.set_policy("outgoing", "allow")
            self._set_main_values(_("Allow all OUTGOING traffic"))
    
    def on_cbTypePreconf_changed(self, widget):
        """Change between Service/Program"""
        if self.type_preconf.get_active() == 0:
            self.service_preconf.hide()
            self.program_preconf.show()
        else:
            self.service_preconf.show()
            self.program_preconf.hide()
    
    def on_cbExtendedActions_toggled(self, widget):
        """Extended actions"""
        # Set hide extended actions
        if self.extended_actions.get_active() == 0:
            self.insert_number_preconf.hide()
            self.insert_number_simple.hide()
            self.insert_number_advanced.hide()
            self.log_preconf.hide()
            self.log_simple.hide()
            self.log_advanced.hide()
        else:
            self.insert_number_preconf.show()
            self.insert_number_simple.show()
            self.insert_number_advanced.show()
            self.log_preconf.show()
            self.log_simple.show()
            self.log_advanced.show()
    
    def on_menuQuit_activate(self, widget):
        """Menu Quit"""
        width, height = self.win_main.get_size()
        self.fw.update_config_file(width, height, self.panelmain.get_position())
        if self.fw.get_listening_status() != "disable":
            self.fw.set_listening_status("disable")
            self._refresh_report()
        Gtk.main_quit()
    
    def on_menuPreferences_activate(self, widget):            
        """Show Window Preferences"""
        self.pref_btn_close.grab_focus()
        self.dlg_preferences.show()
    
    def on_menuAbout_activate(self, widget):
        """View About Window"""
        about = Gtk.AboutDialog()
        about.set_copyright(_("© 2008-2012 The Gufw Project\nShield logo © 2007 Michael Spiegel"))
        about.set_comments(_("Graphical user interface for ufw"))
        about.set_version("12.10.0")
        about.set_website("http://gufw.tuxfamily.org/")
        about.set_authors([_('''Lead developer:
Marcos Alvarez Costales https://launchpad.net/~costales

Developers (in alphabetical order):
David Planella https://launchpad.net/~dpm
Emilio López https://launchpad.net/~turl
Giacomo Picchiarelli https://launchpad.net/~gpicchiarelli
Jeremy Bicha https://launchpad.net/~jbicha
Raúl Soriano https://launchpad.net/~gatoloko
Rogério Vicente https://launchpad.net/~rogeriopvl
Rubén Megido https://launchpad.net/~runoo
Vadim Peretokin https://launchpad.net/~vperetokin

Contributors:
Cedrick Hannier https://launchpad.net/~cedynamix

MOTU
Devid Antonio Filoni https://launchpad.net/~d.filoni''')])
        about.set_translator_credits(_("translator-credits"))
        about.set_artists([_("Shield logo by myke http://michael.spiegel1.at/"), 
("Tutorial http://www.gimpusers.com/tutorials/create-a-shield-symbol.html")])
        about.set_license('''The shield logo is licensed under a Creative Commons
Attribution 3.0 Unported License. See for more information:
http://creativecommons.org/licenses/by/3.0/

All other content is licensed under the GPL-3+.

Gufw is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as
published by the Free Software Foundation; either version 3
of the License, or (at your option) any later version.

Gufw is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied
warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
PURPOSE.
See the GNU General Public License for more details.

You should have received a copy of the GNU General Public
License along with Gufw; if not, see for more information:
http://www.gnu.org/licenses''')
        about.connect("response", lambda d, r: d.destroy())
        about.set_transient_for(self.win_main)
        about.show()

    def on_menuLog_activate(self, widget):
        """View Gufw Log Window"""
        if self.server_script.get_active():
            self.log_txt_buffer.set_text(self.fw.get_gufw_log('server'))
        else:
            self.log_txt_buffer.set_text(self.fw.get_gufw_log('local'))
        
        self.log_btn_close.grab_focus()
        self.dlg_log.show()
    
    def on_menuReload_activate(self, widget):
        """Reload the ufw rules"""
        self._set_main_values(_("Reloaded ufw rules"))
        
    def on_menuReset_activate(self, widget):
        """Reset ufw"""
        reset_dialog = Gtk.MessageDialog(self.win_main,
                Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
                Gtk.MessageType.WARNING, Gtk.ButtonsType.NONE,
                _("This will remove all rules and disable the firewall!"))
        reset_dialog.format_secondary_markup(_("Do you want to continue?"))
        reset_dialog.set_title(_("Reset Firewall"))
        reset_dialog.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_YES, Gtk.ResponseType.YES)
        reset_answer = reset_dialog.run()
        reset_dialog.destroy()
        if reset_answer == Gtk.ResponseType.YES:
            if self.fw.get_status() == "enable":
                self.switchFirewall.set_active(False)
            self.fw.reset_ufw()
            self._set_main_values(_("Removed rules and reset firewall!"))
    
    def on_menuDoc_activate(self, widget):
        """Launch browser with Documentation web"""
        webbrowser.open_new("https://help.ubuntu.com/community/Gufw")
        
    def on_menuAnswers_activate(self, widget):
        """Launch browser with Documentation web"""
        webbrowser.open_new("https://answers.launchpad.net/gui-ufw")
        
    def on_menuTranslate_activate(self, widget):
        """Launch browser with Documentation web"""
        webbrowser.open_new("https://translations.launchpad.net/gui-ufw/trunk/+translations")
        
    def on_menuBug_activate(self, widget):
        """Launch browser with Bug Report web"""
        webbrowser.open_new("https://bugs.launchpad.net/gui-ufw")
        
    def on_winMain_delete_event(self, widget, event):
        """Close Button Main Window"""
        width, height = self.win_main.get_size()
        self.fw.update_config_file(width, height, self.panelmain.get_position())
        if self.fw.get_listening_status() != "disable":
            self.fw.set_listening_status("disable")
            self._refresh_report()
        Gtk.main_quit()
    
    def on_dlgAdd_delete_event(self, widget, event):
        """Close Button Window Add Rules"""
        self.btn_add_window.set_sensitive(True)
        self.menu_add.set_sensitive(True)
        self.dlg_add.hide()
        return True
    
class RefreshReport(threading.Thread):
    """Refresh Listening report in background"""
    def __init__(self, fw_status, model, lines, previous_lines, first_run, show_popups):
        threading.Thread.__init__(self)
        bus = dbus.SessionBus()
        notify_object = bus.get_object('org.freedesktop.Notifications', '/org/freedesktop/Notifications')
        self.notify_interface = dbus.Interface(notify_object, 'org.freedesktop.Notifications')
        self.path = Path()
        self.firewall_status = fw_status
        self.listening_model = model
        self.lines = lines
        self.previous_lines = previous_lines
        self.first_run = first_run
        self.show_popup = show_popups
    
    def run(self):
        """Show listening report in GUI"""
        self.listening_model.clear() 
        row = 0
        notif_msg = ""
        for line in self.lines:
            # Component lines for next notify
            if ( self.show_popup == "enable" ) and ( not line in self.previous_lines ) and ( not self.first_run ):
                msg_split = line.split("%")
                if msg_split[3] == '-' and msg_split[2] != '*':
                    msg = msg_split[2] + _(" on ") + msg_split[1] + " " + msg_split[0] # IP
                else:
                    msg = msg_split[3] + _(" on ") + msg_split[1] + " " + msg_split[0] # App
                
                if notif_msg == "":
                    notif_msg = msg
                else:
                    notif_msg = "\n".join([notif_msg, msg])
            
            # Update the Listening Report
            row += 1
            iter = self.listening_model.insert(row)
            line_split = line.split("%")
                        
            self.listening_model.set_value(iter, 0, row)
            self.listening_model.set_value(iter, 1, line_split[0].strip()) # Protocol
            self.listening_model.set_value(iter, 2, line_split[1].strip()) # Port
            self.listening_model.set_value(iter, 3, line_split[2].strip()) # Address
            self.listening_model.set_value(iter, 4, line_split[3].strip()) # App
            
            if self.firewall_status == "enable":
                if line_split[4] == "allow":
                    self.listening_model.set_value(iter, 5, __color__["red"])
                elif line_split[4] == "deny":
                    self.listening_model.set_value(iter, 5, __color__["green"])
                elif line_split[4] == "reject":
                    self.listening_model.set_value(iter, 5, __color__["blue"])
                elif line_split[4] == "limit":
                    self.listening_model.set_value(iter, 5, __color__["orange"])
                    
        # Notifications system for new connections        
        if ( self.show_popup == "enable" ) and ( not notif_msg == "" ):
            self.notify_interface.Notify("Gufw", 0, self.path.get_icon_path(), _("Firewall"), notif_msg, '', {"x-canonical-append": dbus.String("allowed")}, -1) # Expired time notification blocked by bug #390508
