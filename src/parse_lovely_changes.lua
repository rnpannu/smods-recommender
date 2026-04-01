local lovely = require "lovely"
local plenary = require "plenary.init"
local parse = require"parser"
local Path = plenary.path
local Job = plenary.job

vim.env.LD_PRELOAD = "" -- Prevents lovely from injecting into child processes

local wd = assert(_G.arg[1], "Please pass the path to the tmp work dir")
local git_dir = assert(_G.arg[2], "Please pass the path to the git dir")
local hash = assert(_G.arg[3], "Please pass the commit hash")

local source = Path:new(git_dir .. "/.git")
local destination = Path:new(wd .. "/.git")

local success = source:copy{ destination = destination, recursive = true }

local function sh(cmd, ...)
	local out, code = Job:new{
		command = cmd,
		args = { ... },
		cwd = wd,
	}:sync()
	-- print(table.concat(out, "\n"))
	assert(code == 0, "child process exited with non-zero exit code " .. code)
	return out
end


sh("git", "reset", "--hard", hash)
local out = sh("git", "show", hash)

local files = {}
local curr = nil

local res = [[^\v\@\@ -(\d+)(,\d+)? \+(\d+)(,\d+)? \@\@]]
local re = vim.regex(res)
local namePattern = "^%+%+%+ b/(.*)"
for i, v in ipairs(out) do
	local nameMatch = v:match(namePattern)
	if nameMatch then
		files[nameMatch] = {}
		curr = files[nameMatch]
	elseif re:match_str(v) then
		local matches = vim.fn.matchlist(v, res)
		hunkNewStartLine = tonumber(matches[4])
		hunkNewCount = matches[5] and tonumber(matches[5]:sub(2)) or 1
		table.insert(curr, {hunkNewStartLine, hunkNewCount})
	end
end

assert(lovely.reload_patches())
local patchType = "%[patches%.(%w+)]"
local target = "target%s*=%s*[\"']+(.-)[\"']+$"
local pattern = "pattern%s*=%s*[\"']+(.-)[\"']+$"
local allWhitespace = "^%s*$"
local comment = "^%s*#"
local newPatch = "^%[%[patches]]$"

local toFind = {}
for f,lines in pairs(files) do
	if f:sub(-5) == ".toml" then
		local max = #lines
		local index = 1
		local inside = false
		local next = lines[index][1]
		local type, key, file, matched

		local path = Path:new(wd .. "/" .. f)
		for l, c in ipairs(path:readlines()) do
			if l == next then
				if inside then index = index + 1 end
				inside = not inside
				local tmp = lines[index]
				if not tmp then break end
				next = tmp[inside and 2 or 1]
				key = nil
				file = nil
				matched = false
			end
			local t = c:match(patchType)
			if inside and t then
				type = t
				key = nil
				file = nil
				matched = false
			elseif c:match(allWhitespace) or c:match(comment) or c:match(newPatch) then
				-- Skip
			elseif type == "pattern" then
				local t = c:match(target)
				if t then
					file = t
				end
				local t = c:match(pattern)
				if t then
					key = t
				end
				if not matched and key and file and inside then
					if not toFind[file] then toFind[file] = {} end
					table.insert(toFind[file], {key, type})
					matched = true
				end
			end
		end
	end
end

local definitions = {}
local calls = {}
for f,p in pairs(toFind) do
	local regions = {}
	local path = Path:new("./gamefiles/" .. f)
	if path:exists() then
		local contents = path:read()
		local buff, data = lovely.apply_patches(f, contents)
		if buff and data then
			for _, d in ipairs(data.entries) do
				if d.regions then
					for i, pat in ipairs(p) do
						if d.patch_source.patch_type == pat[2]then
							if pat[2] == "pattern" then
								if pat[1] == d.patch_source.pattern then
									table.remove(p, i)
									for _, r in ipairs(d.regions) do
										table.insert(regions, r)
									end
									break
								end
							end
						end
					end
				end
			end
		end

		vim.api.nvim_buf_set_lines(0, 0, -1, false, vim.split(buff, "\n"))
		vim.api.nvim_set_option_value('filetype', 'lua', {})
		local data = parse()


		for _, r in ipairs(regions) do
			for _, funcDef in ipairs(data.definitions) do
				if funcDef.line_start <= r.end_line and funcDef.line_end >= r.start_line then
					local name = funcDef.name
					local linesChanged = math.min(r.end_line, funcDef.line_end) - math.max(r.start_line, funcDef.line_start) + 1
					if not definitions[name] then definitions[name] = 0 end
					definitions[name] = definitions[name] + linesChanged
				end
			end

			for _, funcCall in ipairs(data.calls) do
				if r.start_line <= funcCall.line and funcCall.line <= r.end_line then
					local name = funcCall.name
					if not calls[name] then calls[name] = 0 end
					calls[name] = calls[name] + 1
				end
			end
		end
	end
end


local out = vim.json.encode({definitions = definitions, calls = calls})
io.write(out)
