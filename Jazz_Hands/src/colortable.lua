--[[pod_format="raw",created="2025-07-27 03:34:13",modified="2025-10-26 00:40:31",revision=42]]
--Color tables

--[[pod_type="gfx",content={"Add this to your init to","enable ColorTables."},flavor=1,flipped="false",font=1,head=1006,mono="true",style=2,swapped="false",tab=0,tail=2,text_d=false,text_f=true,text_l=false]]unpod("b64:bHo0AOgCAAANBAAA8whweHUAQyCCPgTwdPduIBfwbBcQB-BuBwUA8Q1AF0AHMAdgByAHQAfAB-AXB3AHIAeAB8AHEAcwBAACHQBX8AMH8CQYAPACECcQJ1A3ACcQFyAnUDcQF2AUAPQCFxAHEAcABwAXUBcQJxAXEDcaADEwNwAaABEQTAAREAIAEZAKABNQGAABBAAjF4AcAACCAAQeAABuAAw_ADUgF3AgABUABAA-kAcQPgASE0AKAD9gJwA8AA4A6AAhcBckAJAnACeAFxAXkAf0ADIAB4A_AFInIBdwF_YAVPAwF-AsWAEHBQDyAQMHMBfAF2AXsEdQBzAX8B4UADFAB7CUAGHQB3AHQAcWAFBAFxAnIAQAcAcgF2AHQBcIAAAXATMgBzAWAEcgJ-AT1gAzMAcAuAAAsgABsAABAgBXABdAB1AcAEUAB-AWhwEyECcAFwAZNzMAAEEABRoAQxAX8BT_AQAbACMQBxkAJweADAACNQAXIBIAIWAHnwAjQCdoAAHOAGBgFyAXIBcdAgFiAAEUAGgAJyAH8BAnAQCYAoAg90xQ9wzwUBABg2wHMAfwbQcgIgDwJW8HAAdgvyDwXRdgDg8cB30O8F4HcA4dB00O8GcODXwNDvBlDg0cB2wNDvBkDjwYHAgPGBwLAGAsCAcoCywKAGEcCwgOKDwUADELKBsTAFA8GxwbGQkAYA8ZGUwpCkQAMAp5ClIA8AwaORoO8Gl_8GkuBB8fBC7waA4fDQQPDw8fBB9iAPAITgYHBB8PBAcGTvBfDgYvBgYPEgc1BwUKAPIWDvBdDgNHBQMHFgcDBUcDDvBbDgZnBQMXAwVnBg7wWg4DRwPXAwkAQhNnA0cLAJEHAwYlHx9XQwcPANATBjIFDw8CByITJQYTEQDABgUCMQIBEiECBTIFRQDwEh4EURJBBAIhBB7wWw4EkQIUAjEEDvBcDgQCYQIUEjECBIUA8AcSQQI0MRIO8F8OUgQ_BDIO8GFuME5w")

--if ColorTable and ColorTable.apply then
--	ColorTable:apply(get_spr(255), 0)
--end


ColorTable = {
	----------------
	table = {[0]=get_spr(255)},
	----------------
	apply = function(self, tab_ud, table_num)
		--Color table to poke into
		local _address = 0x8000 + table_num * 0x1000
		memmap(tab_ud, _address)
		
		--Apply to shapes
		poke(0x550b, 0x3f)
	end,
	----------------
	stash = function(self, tab_ud, num)
		self.table[num] = tab_ud
	end,
	----------------
	--[ ] Make .reset function
	----------------
}

