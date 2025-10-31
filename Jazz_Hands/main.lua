--[[pod_format="raw",created="2025-09-24 15:09:21",modified="2025-10-30 03:29:49",revision=533]]
-- Quick Listener Test (Server)


function _init()
	--Globals
	Sock = nil
	IP = "localhost"
	Port = 8899
	clients = {}
	Info = nil
	Notes = {}
	Channels = {}
end


function _update()
	--Make socket if one does nto exist
	if not Sock then
		Sock = socket("tcp://"..IP..":"..Port)
	end
		
	--Scan for new clients
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
		end
	end
end


function _draw()
	cls(0)
	print("Sock: " .. tostring(Sock), 0, 0, Sock and 11 or 8)
	print("Info: " .. tostring(Info))
	
	for i = 1, 2 do
		for j = 1, 4 do
			print("Channel "..j*i..": Held " ..			stat(400+(j*i), 0), -100+(i*200),  0+(j*50), 7)
			print("Channel "..j*i..": Instrument " ..	stat(400+(j*i), 1), -100+(i*200), 10+(j*50), 7)
			print("Channel "..j*i..": Volume " ..		stat(400+(j*i), 2), -100+(i*200), 20+(j*50), 7)
			print("Channel "..j*i..": Volume " ..		stat(400+(j*i), 3), -100+(i*200), 30+(j*50), 7)
		end
	end
	
--	print("Channel 2: Held " ..			stat(401, 0), 300, 50, 7)
--	print("Channel 2: Instrument " ..	stat(401, 1), 300, 60, 7)
--	print("Channel 2: Volume " ..			stat(401, 2), 300, 70, 7)
--	print("Channel 2: Volume " ..			stat(401, 3), 300, 80, 7)
--	
--	print("Channel 3: Held " ..			stat(402, 0), 300, 100, 7)
--	print("Channel 3: Instrument " ..	stat(402, 1), 300, 110, 7)
--	print("Channel 3: Volume " ..			stat(402, 2), 300, 120, 7)
--	print("Channel 3: Volume " ..			stat(402, 3), 300, 130, 7)
--	
--	print("Channel 4: Held " ..			stat(403, 0), 300, 150, 7)
--	print("Channel 4: Instrument " ..	stat(403, 1), 300, 160, 7)
--	print("Channel 4: Volume " ..			stat(403, 2), 300, 170, 7)
--	print("Channel 4: Volume " ..			stat(403, 3), 300, 180, 7)
end


function spawn_note(_state, _note, _velocity, _channel)
	if _state == "NOTE_ON" then
		Notes[_note] = {state=_state, note=_note, channel=_channel}
		note(Notes[_note].note, 8, 20, nil, nil, Notes[_note].channel)
	elseif _state == "NOTE_OFF" then
		note(0, 0, 0, nil, nil, Notes[_note].channel)
	end
end

