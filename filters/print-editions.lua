--[[
Adjustments for the PDF (Typst) and EPUB editions; the HTML site is untouched.

- The lead-in under each chapter title, `::: {.chapter-abstract}`, loses its
  class in Typst and runs straight into the first paragraph.  Give it the
  treatment it has in HTML: italic, a rule on the left, and space below.
- Inline code such as `NEXT_ASSEMBLY_USAGE_OCCURRENCE` is one unbreakable word.
  In the PDF it stretches justified lines into wide gaps; on a phone-sized
  EPUB page it makes tables wider than the screen, so columns are cut off.
  Allow a break after each underscore: a zero-width space in Typst, a <wbr>
  in EPUB, which copies as nothing.  Only inline code is touched; listings
  are code blocks, and copying them must give back exactly the file.
]]

local function typst_string(text)
  return '"' .. text:gsub("\\", "\\\\"):gsub('"', '\\"') .. '"'
end

function Div(div)
  if not div.classes:includes("chapter-abstract") or not quarto.doc.is_format("typst") then
    return nil
  end
  local blocks = { pandoc.RawBlock("typst",
    "#block(inset: (left: 0.9em, y: 0.15em), stroke: (left: 2pt + luma(200)), below: 1.6em)[#set text(style: \"italic\")") }
  for _, block in ipairs(div.content) do blocks[#blocks + 1] = block end
  blocks[#blocks + 1] = pandoc.RawBlock("typst", "]")
  return blocks
end

local function html_escape(text)
  return (text:gsub("&", "&amp;"):gsub("<", "&lt;"):gsub(">", "&gt;"))
end

function Code(code)
  if not code.text:find("_", 1, true) then
    return nil
  end
  if quarto.doc.is_format("typst") then
    local breakable = code.text:gsub("_", "_\u{200B}")
    return pandoc.RawInline("typst", "#raw(" .. typst_string(breakable) .. ")")
  end
  if quarto.doc.is_format("epub") and #code.classes == 0 then
    local breakable = html_escape(code.text):gsub("_", "_<wbr/>")
    return pandoc.RawInline("html", "<code>" .. breakable .. "</code>")
  end
end

-- Attribute names such as application_interpreted_model_schema_name appear as
-- plain words in tables; give them the same break points in EPUB.
function Str(str)
  if quarto.doc.is_format("epub") and str.text:find("_", 1, true) then
    return pandoc.RawInline("html", (html_escape(str.text):gsub("_", "_<wbr/>")))
  end
end
