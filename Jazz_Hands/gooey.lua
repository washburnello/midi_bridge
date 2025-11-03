--[[pod_format="raw",created="2025-11-02 05:15:26",modified="2025-11-03 04:03:32",revision=340,xstickers={}]]
-- Nothing to see here..

--[[pod_type="gfx"]]unpod("b64:bHo0AEQAAABCAAAA8DNweHUAQyAQEATwFV8VkG5wHj8PHoANDyAdDA0OgF2QXXAMIByQDBA8kBwAHAAMsBwADKAxDKABEAGwARABsAUQBVA=") 

-- Just turning the gears..
--include "main.lua"





function GUI_LEFT()
	
	local horz_bar = {		}
	
	local contents = {
		{"text", {text="Pitch Wheel"}},
		{"hslider",{value=controls.pitchwheel.value}},
		{"line",{size=vec(100,0)}},
		{"line",{size=vec(100,0)}},
		{"text", {text="Mod Wheel"}},
		{"hslider",{value=controls.modwheel.value}},
		{"line",{size=vec(100,0)}},
		{"line",{size=vec(100,0)}},
		{"text", {text="Master Volume"}},
		{"hslider",{value=controls.masterVol.value}},
		{"input",{label="myinput",text=tostr(midi_bindings.masterVol)}},
		{"line",{size=vec(100,0)}},
		{"line",{size=vec(100,0)}},
		{"button",{text="Next Instrument",stroke=false}},
		{"button",{text="Previous Instrument",stroke=false}},
	}
	
	
	stack = pgui:component("vstack",{pos=vec(0,0),contents=contents})
	
	midi_bindings.masterVol = tonumber(stack[11])
	
	controls.pitchwheel = {stack[2], stack[3]}
	controls.masterVol.value = stack[10]
	controls.modwheel.value = stack[6]
	controls.masterVol.value = stack[10]
	temp1 = stack
	
	--pgui:set_store("disable_drop",#contents[3] > 0) --to disable the menu dropdown when the overlapping topbar menu is open
	
	--Logic
	if stack[14] and inst_num < 64 then
		inst_num = inst_num + 1
	elseif stack[15] and inst_num > 1 then
		inst_num = inst_num - 1
	end
end

function GUI_TOP()

	local contents = {
	
		{"dropdown",{label="menu", text="Set Input:",stroke=false,contents = {
		
			{"button",{text="Master Volume",stroke=false}},
			{"button",{text="Pitch Wheel",stroke=false}},
			{"button",{text="Mod Wheel",stroke=false}},
			
			{"dropdown",{label="submenu",text="Faders",stroke=false,contents = {
			
				{"button",{text="Fader 1",stroke=false}},
				{"button",{text="Fader 2",stroke=false}},
				{"button",{text="Fader 3",stroke=false}},
				{"button",{text="Fader 4",stroke=false}},
				{"button",{text="Fader 5",stroke=false}}
				
			}}},
			
			{"button",{text="Knobs",stroke=false}},
			disable=pgui:get_store("disable_drop")
			
		}}},
		
	}
	stack = pgui:component("vstack",{pos=vec(120,0),contents=contents})
--	pgui:set_store("disable_drop",#contents[3] > 0)
	
end

function table_tree(table)
	--Get a string representing the tree structure of a table
	local level = 0
	local tree = ""

	if type(table) != "table" then
		return tostring(table)
	end
	
	local function recTree(table, level)
		local tabs = ""
		for i=1,level do tabs = tabs.."	" end	
		
		for k,v in pairs(table) do
			if type(v) == "table" then
				tree = tree..tabs.."<"..k..">\n"
				recTree(v, level + 1)
			else
				tree = tree..tabs.."["..k.."]: "..tostring(v).."\n"
			end
		end
	end
	
	recTree(table, level)
	return tree
end

