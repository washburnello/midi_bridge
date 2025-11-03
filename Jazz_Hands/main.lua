--[[pod_format="raw",created="2025-09-24 15:09:21",modified="2025-11-03 04:09:27",revision=736,xstickers={}]]
-- Quick Listener Test (Server)
poke(0x5f2d, 1)

include "sock_troll.lua"
include "gooey.lua"
include "lib/pgui.lua"


function _init()
	--Globals
	pgui:set_store("disable_drop",false)
	Sock = nil
	IP = "localhost"
	Port = 8899
	clients = {}
	Info = nil
	Notes = {}
	Channels = {}
	temp1 = ""
	temp2 = ""
	inst_num = 1
	-- Create 
	
	
	-- Control variables
	controls = {
		pitchwheel = {value = 0, control = nil},
		modwheel = {value = 0, control = 1},
		masterVol = {value = 127, control = nil}
	}
		-- No Pad Support at this time.
	midi_bindings = {
		pitchwheel = (controls.pitchwheel.value + 8191) / 256,
		modwheel = 1,
		masterVol = 118,
		fader1 = nil,
		fader2 = nil,
		fader3 = nil,
		fader4 = nil,
		fader5 = nil,
		fader6 = nil,
		fader7 = nil,
		fader8 = nil,
		con1 = nil,
		con2 = nil,
		con3 = nil,
		con4 = nil,
		con5 = nil,
		con6 = nil,
		con7 = nil,
		con8 = nil
	}
	
	
end



function _update()
	--Make socket if one does not exist

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

	pgui:refresh() 
	GUI_LEFT()
	GUI_TOP()
	if midi_bindings.masterVol == nil then
		midi_bindings.masterVol = 1
	end
end


function _draw()

	cls(0)
	print("Sock: " .. tostring(Sock.addr..":"..Sock.port), 0, 0, Sock and 11 or 8)
	
	
	for i = 1, 2 do
		for j = 1, 4 do
			print("Channel "..j*i..": Held " ..			stat(400+(j*i), 0), -100+(i*200),  0+(j*50), 7)
			print("Channel "..j*i..": Instrument " ..	stat(400+(j*i), 1), -100+(i*200), 10+(j*50), 7)
			print("Channel "..j*i..": Volume " ..		stat(400+(j*i), 2), -100+(i*200), 20+(j*50), 7)
			print("Channel "..j*i..": Volume " ..		stat(400+(j*i), 3), -100+(i*200), 30+(j*50), 7)
			
		end
	end

	cls(6)
	print("SIDEBAR OUTPUT:\n"..table_tree(temp1),300,20,8)
	print(stack[2], 200, 200, 8)
	print("Info: " .. tostring(Info))
	print(test)
	pgui:draw()
end

test = ""
function spawn_note(_state, _note, _velocity, _channel)
	if _state == "NOTE_ON" then
		Notes[_note] = {state=_state, note=_note, channel=_channel}
		note(Notes[_note].note, inst_num, controls.masterVol.value * (_velocity/255), nil, nil, Notes[_note].channel)
	elseif _state == "NOTE_OFF" then
		note(0, 0, 0, nil, nil, Notes[_note].channel)
	end
end


function update_controls(_state, _channel, _control, _value)
	if _state == "CC" then
		if _control == midi_bindings.masterVol then
			controls.masterVol.value = _value
		elseif _control == midi_bindings.modwheel then
			controls.modwheel.value = _value
		end
		test = midi_bindings.masterVol
		
		print("Control Change   " .. tostring(_control) .. " " .. tostring(_value))
	elseif _state == "PITCHWHEEL" then
		controls.pitchwheel.value = _value
		print("Pitchwheel:   " .. tostring(_value))
	end
end