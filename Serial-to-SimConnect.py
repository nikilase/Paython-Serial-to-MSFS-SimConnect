#################################################################
# Serial Port to Simconnect for Microsoft Flight Simulator 2020
# Serial 1 is main port for rotary encoders from esp32
# Serial 2 will be used for all sorts of buttons and switches
#
# Program automatically waits for MSFS to fully start
#
# Serial messages are UTF-8 encoded and have to be terminated by '\n'
# Can also contain '\r' which gets discarded automatically
#
# May not work reliable as it is still in development
#
# Spacing uses tab and not spaces
# Some IDE's may be confused if tab and space are mixed
#
# Only tested on GA aicraft up to the CJ4
# May not or only partially work on airliners 
#################################################################

import sys
from time import sleep
import serial
from SimConnect import *
import time
import threading
import queue

# helper for getting current time in milliseconds
current_milli_time = lambda: int(round(time.time() * 1000))

# events and requests, global because they are used in another function
ae = None
aq = None

# queue for serial commands / messages
command1 = queue.Queue()
command2 = queue.Queue()

# Definitions for the Serial Ports, change to the COM Port in use and used baudrate
com1 = 'COM4'
com2 = 'COM6'
baud1 = 115200
baud2 = 115200


# thread function for first serial port
def serial1():
	try:
		s1 = serial.Serial(com1, baud1)
	except:
		print("Could not open Serial1 on ", com1)
		sys.exit()
	print("Serial1")
	try:
		while True:
			if s1.in_waiting:
				res = s1.readline()
				res = res.decode("utf-8").replace("\n", "").replace("\r", "")
				command1.put(res)
	except KeyboardInterrupt:
		s1.close()


# thread function for first serial port
def serial2():
	try:
		s2 = serial.Serial(com2, baud2)
	except:
		print("Could not open Serial2 on ", com2)
		sys.exit()
	print("Serial2")
	try:
		while True:
			if s2.in_waiting:
				res = s2.readline()
				res = res.decode("utf-8").replace("\n", "").replace("\r", "")
				command2.put(res)
	except KeyboardInterrupt:
		s2.close()


# Main function, starts the Simconnect connection, regularly pulls new data from sim
# and executes the events, requested by the serial device
# ToDo Maybe also have the continuous requests of Aircraft data in thread
def main():
	sm = None
	while True:
		try:
			sm = SimConnect()
		except:
			print("MSFS not started")
			sleep(1)
			continue
		else:
			print("MSFS started")
			break

	# Objects used for Events and Requests of SimVars
	global ae, aq
	ae = AircraftEvents(sm)
	aq = AircraftRequests(sm, _time=10)

	# after the Sim has started the threads can start executing their respective functions
	threading.Thread(target=serial1, daemon=True).start()
	threading.Thread(target=serial2, daemon=True).start()

	# Used to time the polling of SimVars
	t = current_milli_time()

	# SimVars to be polled
	vs_active = False
	flc_active = False
	autothrottle_active = False		# maybe not needed
	autothrottle_mach = False
	autothrottle_spd = False

	# var set by serial 2, can be used to increment altitude by 1000ft instead of 100ft
	altitude_use_thousand = False

	# main loop
	try:
		while True:
			# Every second we update the used SimVars
			# as the requests are resource heavy we may only do them at most every 100ms
			if current_milli_time() - t > 1000:
				vs_active = aq.get("AUTOPILOT_VERTICAL_HOLD")
				autothrottle_active = aq.get("AUTOTHROTTLE_ACTIVE")
				autothrottle_mach = aq.get("AUTOPILOT_MACH_HOLD")
				autothrottle_spd = aq.get("AUTOPILOT_AIRSPEED_HOLD")
				flc_active = aq.get("AUTOPILOT_FLIGHT_LEVEL_CHANGE")
				t = current_milli_time()

			# These variables need to be set by serial 2, but aren't implemented right now
			# Switch in VS panel to use either vertical speed and flc or autothrottle
			autothrottle_switch = False		# Probably not used

			# Switch in CRS/VOR panel if we change CRS/VOR 1 or 2
			crs_vor_1 = True

			# First check serial 2 if it has new commands
			m = command2.qsize()
			if m:
				res = command2.get()
				print(res)
				if res == "100":
					altitude_use_thousand = False
				elif res == "1000":
					altitude_use_thousand = True

			# Do the same for serial 1, only with much more commands
			n = command1.qsize()
			if n:
				res = command1.get()
				# print(res)
				# Switch Case of commands, sorted by function area
				# These currently are only rotary encoders and therefore have three different signal types
				# Increment for clockwise rotation, decrement for counterclockwise rotation and sync for button

				###################################################
				#  Altitude
				###################################################
				if res == "alt+":
					# Check if we add 100 or thousand feet per step
					if altitude_use_thousand:
						print("ALT+ 1000:")
						for i in range(10):
							trigger_event("AP_ALT_VAR_INC")
					else:
						print("ALT+")
						trigger_event("AP_ALT_VAR_INC")

				elif res == "alt-":
					# Check if we add 100 or thousand feet per step
					if altitude_use_thousand:
						print("ALT- 1000:")
						for i in range(10):
							trigger_event("AP_ALT_VAR_DEC")
					else:
						print("ALT-")
						trigger_event("AP_ALT_VAR_DEC")

				elif res == "alt_sync":
					altitude = aq.get("INDICATED_ALTITUDE")
					print("ALT SYNC: ", altitude)
					trigger_event("AP_ALT_VAR_SET_ENGLISH", altitude)

				###################################################
				# Heading
				###################################################
				elif res == "hdg+":
					print("HDG+")
					trigger_event("HEADING_BUG_INC")
				elif res == "hdg-":
					print("HDG-")
					trigger_event("HEADING_BUG_DEC")
				elif res == "hdg_sync":
					heading = aq.get("HEADING_INDICATOR")*180/3.14159265359
					print("HDG SYNC: ", heading)
					trigger_event("HEADING_BUG_SET", heading)

				###################################################
				# Vertical Speed
				###################################################
				elif res == "vs+":
					if vs_active:
						print("VS+")
						trigger_event("AP_VS_VAR_INC")
					elif flc_active:
						print("SPD INC")
						trigger_event("AP_SPD_VAR_INC")

				elif res == "vs-":
					if vs_active:
						print("VS-")
						trigger_event("AP_VS_VAR_DEC")
					elif flc_active:
						print("SPD DEC")
						trigger_event("AP_SPD_VAR_DEC")

				elif res == "vs_sync":
					if vs_active:
						print("VS LVL")
						trigger_event("AP_VS_VAR_SET_ENGLISH", 0.0)
					elif flc_active:
						speed = aq.get("AIRSPEED_INDICATED")
						print("FLC SPD SYNC")
						trigger_event("AP_SPD_VAR_SET", speed)

				###################################################
				# Speed only for autothrottle in a320, may not work perfectly as it wasn't tested enough
				###################################################
				elif res == "spd+":
					if autothrottle_spd:
						print("SPD+")
						trigger_event("AP_SPD_VAR_INC")
					elif autothrottle_mach:
						print("MACH+")
						trigger_event("AP_MACH_VAR_INC")
				elif res == "spd-":
					if autothrottle_spd:
						print("SPD-")
						trigger_event("AP_SPD_VAR_DEC")
					elif autothrottle_mach:
						print("MACH-")
						trigger_event("AP_MACH_VAR_DEC")
				elif res == "spd_sync":
					if autothrottle_spd:
						speed = aq.get("AIRSPEED_INDICATED")
						print("SPD SYNC")
						trigger_event("AP_SPD_VAR_SET", speed)
					elif autothrottle_mach:
						mach = aq.get("AIRSPEED_MACH")
						print("MACH SYNC")
						trigger_event("AP_MACH_VAR_SET", mach)

				###################################################
				# CRS 1 / CRS 2
				# just like heading
				###################################################
				elif res == "crs+":
					if crs_vor_1:
						print("CRS/VOR1+")
						trigger_event("VOR1_OBI_INC")
					else:
						print("CRS/VOR2+")
						trigger_event("VOR2_OBI_INC")
				elif res == "crs-":
					if crs_vor_1:
						print("CRS/VOR1-")
						trigger_event("VOR1_OBI_DEC")
					else:
						print("CRS/VOR2-")
						trigger_event("VOR2_OBI_DEC")
				elif res == "crs_sync":
					heading = aq.get("HEADING_INDICATOR") * 180 / 3.14159265359
					if crs_vor_1:
						print("CRS/VOR1 SYNC: ", heading)
						trigger_event("VOR1_SET", heading)
					else:
						print("CRS/VOR2 SYNC: ", heading)
						trigger_event("VOR2_SET", heading)

				###################################################
				# QNH
				# Sync sets QNH to STD
				###################################################
				elif res == "baro+":
					print("BARO+")
					trigger_event("KOHLSMAN_INC")
				elif res == "baro-":
					print("BARO-")
					trigger_event("KOHLSMAN_DEC")
				elif res == "baro_sync":
					print("STD BARO")
					# x = 1013.25 hPa * 16
					trigger_event("KOHLSMAN_SET", 1013.25*16)

				###################################################
				# COM 1 / Com2
				# not done right now but should be simple
				###################################################


				###################################################
				# NAV COM 1 und 2
				# not done right now but should be simple
				###################################################

				else:
					# safeguard if somehow there was a wrong message sent
					print(res)

				# Maybe needed to make time for threads to execute? Not tested without yet
				sleep(0.0001)

	except KeyboardInterrupt:
		if sm is not None:
			sm.quit()
	print("MSFS Stopped!")
	return 0


# This function actually does the work of triggering the event
def trigger_event(event_name, value_to_use=None):
	EVENT_TO_TRIGGER = ae.find(event_name)
	if EVENT_TO_TRIGGER is not None:
		if value_to_use is None:
			EVENT_TO_TRIGGER()
		else:
			EVENT_TO_TRIGGER(int(value_to_use))
		status = "success"
	else:
		status = "Error: %s is not an Event" % (event_name)
	return status


# This is needed to make the file know what function to execute as main function
if __name__ == '__main__':
	main()
