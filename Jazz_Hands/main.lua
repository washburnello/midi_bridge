--[[pod_format="raw",created="2025-09-24 15:09:21",modified="2025-11-02 17:37:17",revision=648,xstickers={}]]
-- Quick Listener Test (Server)
poke(0x5f2d, 1)

include "sock_troll.lua"
include "gooey.lua"
include "lib/pgui.lua"


function _init()
	--Globals
	Sock = nil
	IP = "localhost"
	Port = 8899
	clients = {}
	Info = nil
	Notes = {}
	Channels = {}
	
	-- Create 
	
	
	-- Control variables
	controls = {
		pitchwheel = max(8191),
		modwheel = max(127),
		masterVol = max(127)
	}
		-- No Pad Support at this time.
	conMap = {
		-- Mappings for test purposes on Code 49 MIDI keyboard.
		-- Needs a dynamic mapper for custom control schemes.
	}
	
	
	
end


function _update()
	--Make socket if one does nto exist
	--[[
	if not Sock then
		Sock = socket("tcp://"..IP..":"..Port)
	end
		
	if Sock then
		Info = Sock:read()
	end
	
	--Parse info
	--Midi events come formated as strings 'NOTE_ON:00:00:00'
	if Info then
		local _raw_midi = split(Info, ",")
		
		for i = 1, #_raw_midi do
			local _midi_event = {}
			_midi_event = split(_raw_midi[i], ":")
			spawn_note(unpack(_midi_event))
			update_controls(unpack(_midi_event))
			
		end
		
		--Update Controls
		
	end
	--]]
	
	win:update_all()

   if win.w ~= last_w or win.h ~= last_h then
       last_w, last_h = win.w, win.h
       --win:refresh()
	end
end


function _draw()
--[[
	cls(0)
	print("Sock: " .. tostring(Sock.addr..":"..Sock.port), 0, 0, Sock and 11 or 8)
	print("Info: " .. tostring(Info))
	
	for i = 1, 2 do
		for j = 1, 4 do
			print("Channel "..j*i..": Held " ..			stat(400+(j*i), 0), -100+(i*200),  0+(j*50), 7)
			print("Channel "..j*i..": Instrument " ..	stat(400+(j*i), 1), -100+(i*200), 10+(j*50), 7)
			print("Channel "..j*i..": Volume " ..		stat(400+(j*i), 2), -100+(i*200), 20+(j*50), 7)
			print("Channel "..j*i..": Volume " ..		stat(400+(j*i), 3), -100+(i*200), 30+(j*50), 7)
			
		end
	end
	--]]
	cls(0)
	win:update_all()

   if win.w ~= last_w or win.h ~= last_h then
       last_w, last_h = win.w, win.h
       win:update_all()       -- <-- re-run all function() attributes
   end
	print(window_width)
	print(window_height)
end


function spawn_note(_state, _note, _velocity, _channel)
	if _state == "NOTE_ON" then
		Notes[_note] = {state=_state, note=_note + (controls.pitchwheel / 8191), channel=_channel}
		note(Notes[_note].note, 8, controls.masterVol * (_velocity/255), nil, nil, Notes[_note].channel)
	elseif _state == "NOTE_OFF" then
		note(0, 0, 0, nil, nil, Notes[_note].channel)
	end
end


function update_controls(_state, _control, _value)
	if _state == "CONTROL_CHANGE" then
		controls._control = _value
		print("Control Change   " .. tostring(_control) .. " " .. tostring(_value))
	elseif _state == "PITCHWHEEL" then
		controls.pitchwheel = _value
		print("Pitchwheel:   " .. tostring(_value))
	end
end