--[[pod_format="raw",created="2025-11-02 05:15:26",modified="2025-11-02 18:26:14",revision=111,xstickers={}]]
-- Nothing to see here..

--[[pod_type="gfx"]]unpod("b64:bHo0AEQAAABCAAAA8DNweHUAQyAQEATwFV8VkG5wHj8PHoANDyAdDA0OgF2QXXAMIByQDBA8kBwAHAAMsBwADKAxDKABEAGwARABsAUQBVA=") 

-- Just turning the gears..

include "main.lua"

window_width = 100
window_height = 100
--[[
win = create_gui({

   width = 100,
  	height = 100,
  	title = "Jazz Hands!",
	resizable = true,
	
	body = {
		{
			type="label", 
			x=0, y=0, 
			width=function() return win.w end, height=30
		}
	}
})
--]]
win = create_gui({
    title = "Responsive GUI",
    x = 100, y = 80,
    width = 400, height = 300,
    resizable = true,
    min_w = 200, min_h = 150,
    body = {
        -- Full-width header
        {type="label", text="PICOTRON RESPONSIVE",
         x=0, y=0,
         width=function() return win.w end,
         height=30,
         style={bg_color=5, text_color=0, align="center"}},

        -- Centered button
        {type="button", text="Close",
         x=function() return win.width/2 - 50 end,
         y=function() return win.height - 50 end,
         width=100, height=30,
         onclick=function() win:close() end},
    }
})

-- 2. Track size changes and refresh layout
last_w, last_h = win.width, win.height