#!/bin/env -S nvim --clean -l
local parser = require "parser"

local is_scripting_mode = #vim.api.nvim_list_uis() == 0
if is_scripting_mode then
	local filename = _G.arg[1]
	if not filename then
		print("No file passed in scripting mode")
		os.exit(1)
	end
	if filename == "-" then
		-- Read from stdin
		local content = io.read("*a")
		if content then
			vim.api.nvim_buf_set_lines(0, 0, -1, false, vim.split(content, "\n"))
			vim.api.nvim_set_option_value('filetype', 'lua', {})
		else
			print("No file passed in stdin")
			os.exit(1)
		end
	else
		-- Open the file
		vim.cmd('edit ' .. filename)
		vim.api.nvim_set_option_value('filetype', 'lua', {})
	end
end

local data = parser()

local out = vim.json.encode(data)
if is_scripting_mode then
	-- Workaround printing goes to stderr
	-- See: https://github.com/neovim/neovim/issues/37187
	io.write(out)
else
	print(out)
end
