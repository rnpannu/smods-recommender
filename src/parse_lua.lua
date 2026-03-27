#!/bin/env -S nvim --clean -l

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
	end
end

local data = {
	definitions = {},
	calls = {},
}
local parser = vim.treesitter.get_parser(0)
local tree = parser:parse()[1]
local function node_text(node)
	return vim.treesitter.get_node_text(node, 0)
end
do
	local query_text = "(function_declaration) @function"
	local query = vim.treesitter.query.parse(parser:lang(), query_text)

	for id, node in query:iter_captures(tree:root(), 0, 0, -1) do
		local start_row, _, end_row, _ = node:range()
		local name = node_text(node:field("name")[1])
		table.insert(data.definitions, {line_start = start_row + 1, line_end = end_row + 1, name = name})
	end
end
local function find_name(node)
	local parent = node:parent()
	if not parent or not parent:named() then return end
	local type = parent:type()
	if type == "expression_list" then
		local found = false
		for i = 0, parent:child_count() - 1 do
			local child = parent:child(i)
			if node:equal(child) then
				found = i
				break
			end
		end
		if not found then error "Not a child of my parent?" end
		local var_list = parent:prev_named_sibling()
		if not var_list then return end
		return node_text(var_list:child(found))
	elseif type == "field" then
		local sibling = node:prev_named_sibling()
		if not sibling then return end
		local name = node_text(sibling)
		local parent_name = find_name(parent:parent())
		if parent_name then
			return parent_name .. "." .. name
		end
		return "<unk>." .. name
	end
end
do
	local query_text = "(function_definition) @function"
	local query = vim.treesitter.query.parse(parser:lang(), query_text)

	for id, node in query:iter_captures(tree:root(), 0, 0, -1) do
		local start_row, _, end_row, _ = node:range()
		local name = find_name(node)
		if name then
			table.insert(data.definitions, {line_start = start_row + 1, line_end = end_row + 1, name = name})
		end
	end
end
do
	local query_text = "(function_call) @function"
	local query = vim.treesitter.query.parse(parser:lang(), query_text)

	for id, node in query:iter_captures(tree:root(), 0, 0, -1) do
		local start_row, _, end_row, _ = node:range()
		local name = node_text(node:field("name")[1])
		table.insert(data.calls, {line = end_row + 1, name = name})
	end
end

local out = vim.json.encode(data)
if is_scripting_mode then
	-- Workaround printing goes to stderr
	-- See: https://github.com/neovim/neovim/issues/37187
	io.write(out)
else
	print(out)
end
