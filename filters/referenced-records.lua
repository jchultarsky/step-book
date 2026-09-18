--[[
Show, beneath a Part 21 listing, the records it refers to but does not show.

A listing names the example file it is taken from, or builds on:

    ```{.step source="bracket.step"}

Every #n the listing's records mention that the listing does not define is
looked up in examples/<source>, and so is everything those records refer to in
turn, until nothing is left unresolved.  The HTML book shows all of them in a
collapsed panel.  The PDF and the EPUB, where a panel cannot be relied on to
open, print them all when they fit in PRINT_BUDGET, and otherwise print the
records the listing points at directly and summarise the rest by entity type.  tools/check_references.py checks in CI
that every such record exists and is of a type its attribute admits.
]]

local PRINT_BUDGET = 40

local repo_url = nil
local cache = {}

-- Split Part 21 text into records.  Returns id -> { text = ..., refs = {...} }.
local function parse(text)
  local records = {}
  local buffer = {}
  local i, n = 1, #text
  local function finish()
    local record = table.concat(buffer):gsub("^%s+", ""):gsub("%s+$", "")
    buffer = {}
    local id = record:match("^#(%d+)%s*=")
    if id then
      local bare = record:gsub("'[^']*'", "''")
      local refs, seen = {}, {}
      for ref in bare:sub(#id + 2):gmatch("#(%d+)") do
        if not seen[ref] then
          seen[ref] = true
          refs[#refs + 1] = tonumber(ref)
        end
      end
      records[tonumber(id)] = { text = record .. ";", refs = refs }
    end
    return record
  end
  while i <= n do
    local c = text:sub(i, i)
    if c == "/" and text:sub(i + 1, i + 1) == "*" then
      local close = text:find("*/", i + 2, true)
      i = (close or n) + 2
    elseif c == "'" then
      local j = i + 1
      while j <= n do
        if text:sub(j, j) == "'" then
          if text:sub(j + 1, j + 1) == "'" then j = j + 2 else break end
        else
          j = j + 1
        end
      end
      buffer[#buffer + 1] = text:sub(i, j)
      i = j + 1
    elseif c == ";" then
      if finish() == "ENDSEC" and next(records) then break end
      i = i + 1
    else
      buffer[#buffer + 1] = c
      i = i + 1
    end
  end
  return records
end

local function project_path(relative)
  local root = quarto and quarto.project and quarto.project.directory
  if root then return pandoc.path.join({ root, relative }) end
  return relative
end

local function load(name)
  if cache[name] == nil then
    local handle = io.open(project_path(pandoc.path.join({ "examples", name })), "r")
    if not handle then
      cache[name] = false
    else
      local text = handle:read("a")
      handle:close()
      local data = text:find("DATA;", 1, true)
      cache[name] = parse(data and text:sub(data + 5) or text)
    end
  end
  return cache[name] or nil
end

-- Records reachable from the listing's unresolved references, nearest first.
-- Returns a list of { id, depth } in breadth-first order.
local function reachable(shown, file)
  local order, seen, frontier = {}, {}, {}
  for _, record in pairs(shown) do
    for _, ref in ipairs(record.refs) do
      if not shown[ref] and not seen[ref] and file[ref] then
        seen[ref] = true
        frontier[#frontier + 1] = ref
      end
    end
  end
  local depth = 1
  while #frontier > 0 do
    table.sort(frontier)
    local next_frontier = {}
    for _, id in ipairs(frontier) do
      order[#order + 1] = { id = id, depth = depth }
      for _, ref in ipairs(file[id].refs) do
        if not shown[ref] and not seen[ref] and file[ref] then
          seen[ref] = true
          next_frontier[#next_frontier + 1] = ref
        end
      end
    end
    frontier, depth = next_frontier, depth + 1
  end
  return order
end

local function entity_of(text)
  return text:match("^#%d+%s*=%s*%(?%s*([%u%d_]+)") or "?"
end

-- The records to print, and a summary of those left out.  A set that fits the
-- budget is printed whole; a larger one, which usually means the listing
-- reaches a whole solid, is cut to the records the listing points at directly.
local function select_for_print(order, file)
  if #order <= PRINT_BUDGET then return order, nil end
  local keep, kept = {}, {}
  for _, entry in ipairs(order) do
    if entry.depth == 1 then
      keep[#keep + 1] = entry
      kept[entry.id] = true
    end
  end
  local tally, left = {}, 0
  for _, entry in ipairs(order) do
    if not kept[entry.id] then
      local entity = entity_of(file[entry.id].text)
      tally[entity] = (tally[entity] or 0) + 1
      left = left + 1
    end
  end
  local kinds = {}
  for entity, number in pairs(tally) do kinds[#kinds + 1] = { entity, number } end
  table.sort(kinds, function(a, b)
    if a[2] ~= b[2] then return a[2] > b[2] end
    return a[1] < b[1]
  end)
  local parts = {}
  for k = 1, math.min(4, #kinds) do
    parts[#parts + 1] = kinds[k][2] .. " " .. kinds[k][1]
  end
  if #kinds > 4 then parts[#parts + 1] = "..." end
  return keep, { left = left, kinds = table.concat(parts, ", ") }
end

local function listing_text(entries, file)
  table.sort(entries, function(a, b) return a.id < b.id end)
  local lines = {}
  for _, entry in ipairs(entries) do lines[#lines + 1] = file[entry.id].text end
  return table.concat(lines, "\n")
end

local function file_url(name)
  if not repo_url then return nil end
  return repo_url:gsub("/$", "") .. "/blob/main/examples/" .. name
end

local function panel(block)
  local name = block.attributes["source"]
  if not name then return nil end
  local file = load(name)
  if not file then
    io.stderr:write("referenced-records: examples/" .. name .. " not found\n")
    return nil
  end
  local shown = parse(block.text)
  local order = reachable(shown, file)
  if #order == 0 then return nil end

  local url = file_url(name)
  local noun = #order == 1 and "record" or "records"
  if quarto.doc.is_format("html") and not quarto.doc.is_format("epub") then
    local summary = string.format(
      '<details class="referenced-records"><summary>Referred to above: %d %s from <code>%s</code></summary>',
      #order, noun, name)
    local blocks = {
      block,
      pandoc.RawBlock("html", summary),
      pandoc.CodeBlock(listing_text(order, file), pandoc.Attr("", { "step" })),
    }
    if url then
      blocks[#blocks + 1] = pandoc.RawBlock("html",
        string.format('<p class="referenced-records-file"><a href="%s">The complete file</a></p>', url))
    end
    blocks[#blocks + 1] = pandoc.RawBlock("html", "</details>")
    return blocks
  end

  local keep, rest = select_for_print(order, file)
  local text = listing_text(keep, file)
  if rest then
    text = text .. string.format("\n/* ... and %d more: %s */", rest.left, rest.kinds)
  end
  local caption = { pandoc.Str(string.format("Referred to above: %d %s from ", #order, noun)), pandoc.Code(name) }
  if rest then
    caption[#caption + 1] = pandoc.Str(string.format("; the %d it points to directly are shown", #keep))
  end
  caption[#caption + 1] = pandoc.Str(".")
  if url then
    caption[#caption + 1] = pandoc.Space()
    caption[#caption + 1] = pandoc.Link("The complete file.", url)
  end
  if not quarto.doc.is_format("typst") then
    return {
      block,
      pandoc.Div({
        pandoc.Para({ pandoc.Emph(caption) }),
        pandoc.CodeBlock(text, pandoc.Attr("", { "step" })),
      }, pandoc.Attr("", { "referenced-records" })),
    }
  end
  return {
    block,
    pandoc.RawBlock("typst", "#block(width: 100%, inset: (left: 0.8em), stroke: (left: 0.6pt + luma(170)))[#set text(size: 0.82em)"),
    pandoc.RawBlock("typst", "#block(sticky: true)["),
    pandoc.Para({ pandoc.Emph(caption) }),
    pandoc.RawBlock("typst", "]"),
    pandoc.CodeBlock(text, pandoc.Attr("", { "step" })),
    pandoc.RawBlock("typst", "]"),
  }
end

return {
  {
    Meta = function(meta)
      local book = meta.book
      if book and book["repo-url"] then
        repo_url = pandoc.utils.stringify(book["repo-url"])
      elseif meta["repo-url"] then
        repo_url = pandoc.utils.stringify(meta["repo-url"])
      end
    end,
  },
  {
    CodeBlock = function(block)
      if block.classes:includes("step") then return panel(block) end
    end,
  },
}
