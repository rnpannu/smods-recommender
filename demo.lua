-- This file is for testing resolution of function names

local function one()
	local function test()
		print("hi")
	end
end

local test = function() end
local t = {
	one = function() end,
	t = {
		tt = function() end,
	},
}
t.test, t.two = function() end, function() end
t.t.test = function() end

function t:method()
end

