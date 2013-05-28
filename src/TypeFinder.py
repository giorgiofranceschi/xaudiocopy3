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

import gi
from gi.repository import GObject
try:
	gi.require_version('Gst', '1.0')
	from gi.repository import Gst
except:
	print("GStreamer not available")
	sys.exit(1)

### Classe che ricava il tipo del file audio ###
class TypeFinder:

	# Costruttore della classe
	def __init__(self, uri):

		self.__uri = uri

		# Inizializza Gst
		Gst.init(None)

		self.pipe = Gst.Pipeline()

		#filesource = Gst.element_factory_make("filesrc", "filesource")
		#filesource.set_property("location", self.__location)
		filesource = Gst.Element.make_from_uri(Gst.URIType.SRC, self.__uri, "filesrc")
		fakesink = Gst.ElementFactory.make("fakesink", "sink")

		typefind = Gst.ElementFactory.make("typefind", "typefinder")
		typefind.connect("have_type", self.on_find_type)

		self.pipe.add(filesource)
		self.pipe.add(typefind)
		self.pipe.add(fakesink)
		#Gst.element_link_many(filesource, typefind, fakesink)
		filesource.link(typefind)
		typefind.link(fakesink)

		self.bus = self.pipe.get_bus()
		self.bus.add_signal_watch()
		self.bus.connect("message::eos", self.on_eos)
		self.bus.connect("message::error", self.on_error)
		self.bus.connect("message::async_done", self.on_async_done)

		self.pipe.set_state(Gst.State.PLAYING)
		self.mainloop = GObject.MainLoop()
		self.mainloop.run()

	def on_find_type(self, typefind, probability, caps):
		self.__type = caps.to_string()
		print "Media type %s found, probability %d%% " %(self.__type, probability)
		self.pipe.set_state(Gst.State.NULL)
		self.mainloop.quit()

	def on_eos(self, bus, message):
		#if t == Gst.MESSAGE_EOS or t == Gst.MESSAGE_ASYNC_DONE:
		self.pipe.set_state(Gst.State.NULL)
		self.mainloop.quit()

	def on_async_done(self, bus, message):
		#if t == Gst.MESSAGE_EOS or t == Gst.MESSAGE_ASYNC_DONE:
		self.pipe.set_state(Gst.State.NULL)
		self.mainloop.quit()

	def on_error(self, bus, message):
		self.pipe.set_state(Gst.State.NULL)
		self.mainloop.quit()
		err, debug = message.parse_error()
		print "Error: %s" % err, debug

	def get_type(self):
		if self.__type:
			return self.__type
		else:
			return None

### Test ###
#tf=TypeFinder("cdda://01")
#tf=TypeFinder("file:///mnt/VboxCondivisa/Musica/01 - Chega de saudade.mp3")

