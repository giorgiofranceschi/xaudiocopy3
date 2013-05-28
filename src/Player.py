#!/usr/bin/python -tt
# -*- coding: utf-8 -*-
#
# X Audio Copy - GTK and GNOME application for ripping CD-Audio and encoding in lossy audio format.
# Copyright 2010 Giorgio Franceschi
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 2 of the License or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307
# USA

import sys, os, time, thread

import gi
try:
	gi.require_version('Gst', '1.0')
	from gi.repository import Gst
except:
	print("GStreamer not available")
	sys.exit(1)

from AudioFile import *


### Riproduttore di file audio ###
class Player:
	"""La classe accetta come argomento un file audio di classe AudioFile 
	e gli stati "play", "stop", "forward", "rewind", "pause", "carry_on" e il livello del volume."""
	
	# Costruttore della classe
	def __init__(self, audiofile, mainapp):
		
		self.__audiofile = audiofile
		self.__mainapp = mainapp
		
		# Inizializza Gst
		Gst.init(None)

		# Crea il player
		self.player = Gst.ElementFactory.make("playbin", "player")
		fakesink = Gst.ElementFactory.make("fakesink", "fakesink")
		self.player.set_property("video-sink", fakesink)

		# Crea il bus
		bus = self.player.get_bus()
		bus.add_signal_watch()

		# Collega i messaggi
		bus.connect("message::eos", self.on_eos) #Fine dello stream
		bus.connect("message::error", self.on_error) #Errore
		self.bus = bus

		# Il player è pronto
		self.player.set_state(Gst.State.READY)
		self.state = "ready"
	
	def play(self, audiofile):
		print "PLAYING"
		self.player.set_property("uri", audiofile.get_uri())
		self.duration = audiofile.get_duration() * 1000000000
		self.duration_str = self.convert_ns(self.duration)
		self.player.set_state(Gst.State.PLAYING)
		self.state = "playing"
		if self.__mainapp:
			self.play_thread_id = thread.start_new_thread(self.__mainapp.play_thread, ())

	def pause(self):
		print "PAUSE"
		self.player.set_state(Gst.State.PAUSED)
		self.state = "paused"

	def carry_on(self):
		print "CARRY ON"
		try:
			self.player.set_state(Gst.State.PLAYING)
			self.state = "playing"
		except: pass
	
	def stop(self):
		try:
			self.player.set_state(Gst.State.NULL)
			self.state = "ready"
		except: pass
		self.play_thread_id = None

	def set_volume(self, value):
		if value < 1:
			self.player.set_property("volume", value)

	def forward(self):
		position_ns = self.player.query_position(Gst.Format.TIME, None)[0]
		if (position_ns + (5 * 1000000000)) > self.duration:
			seek_ns = position_ns
		else:
			seek_ns = position_ns + (5 * 1000000000)
		self.player.seek_simple(Gst.Format.TIME, Gst.SeekFlags.FLUSH, seek_ns)

	def rewind(self):
		position_ns = self.player.query_position(Gst.Format.TIME, None)[0]
		if position_ns > (5 * 1000000000):
			seek_ns = position_ns - (5 * 1000000000)
		else:
			seek_ns = 0
		self.player.seek_simple(Gst.Format.TIME, Gst.SeekFlags.FLUSH, seek_ns)

	def change_position(self, pos):
		seek_ns = float(pos) * float(self.duration)
		self.player.seek_simple(Gst.Format.TIME, Gst.SeekFlags.FLUSH, seek_ns)

	def on_eos(self, bus, message):
		print "FINITO"
		self.player.set_state(Gst.State.NULL)
		self.state = "ready"
		self.play_thread_id = None

	def on_error(self, bus, message):			
		self.player.set_state(Gst.State.NULL)
		err, debug = message.parse_error()
		print "Error: %s" % err, debug
		self.state = "ready"
		self.play_thread_id = None

	def convert_ns(self, t):
		# From http://pygstdocs.berlios.de/pygst-tutorial/seeking.html
		s, ns = divmod(t, 1000000000)
		m, s = divmod(s, 60)

		if m < 60:
			return "%02i:%02i" %(m, s)
		else:
			h, m = divmod(m, 60)
			return "%i:%02i:%02i" %(h, m, s)

