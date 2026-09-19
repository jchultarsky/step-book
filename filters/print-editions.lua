--[[
Adjustments for narrow pages: the PDF (Typst), the EPUB, and the HTML site on a phone.

- The lead-in under each chapter title, `::: {.chapter-abstract}`, loses its
  class in Typst and runs straight into the first paragraph.  Give it the
  treatment it has in HTML: italic, a rule on the left, and space below.
- Inline code such as `NEXT_ASSEMBLY_USAGE_OCCURRENCE` is one unbreakable word.
  In the PDF it stretches justified lines into wide gaps; on a phone it
  makes sentences, headings and tables wider than the screen, so the EPUB
  cuts columns off and the HTML page scrolls sideways.
  Allow a break after each underscore: a zero-width space in Typst, a <wbr>
  in HTML and EPUB, which copies as nothing.  Only inline code is touched; listings
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
    -- NormalTok is how Quarto writes inline code, so it keeps the same colour.
    return pandoc.RawInline("typst", "#NormalTok(" .. typst_string(breakable) .. ");")
  end
  if quarto.doc.is_format("html") and #code.classes == 0 then
    local breakable = html_escape(code.text):gsub("_", "_<wbr/>")
    return pandoc.RawInline("html", "<code>" .. breakable .. "</code>")
  end
end

-- Attribute names such as application_interpreted_model_schema_name appear as
-- plain words in tables; give them the same break points in HTML and EPUB.
function Str(str)
  if quarto.doc.is_format("html") and str.text:find("_", 1, true) then
    return pandoc.RawInline("html", (html_escape(str.text):gsub("_", "_<wbr/>")))
  end
end

-- On the HTML site a table that still cannot fit a phone after those breaks
-- scrolls sideways in its own box, as listings do, instead of widening the
-- page.  (The EPUB fixes its tables to the page width instead, in epub.css,
-- because a reading system cannot scroll a box sideways.)
function Table(tbl)
  if quarto.doc.is_format("html") and not quarto.doc.is_format("epub") then
    return pandoc.Div({ tbl }, pandoc.Attr("", { "table-scroll" }))
  end
end
