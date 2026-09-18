--[[
Adjustments for the PDF (Typst) edition only; the HTML is styled by CSS.

- The lead-in under each chapter title, `::: {.chapter-abstract}`, loses its
  class in Typst and runs straight into the first paragraph.  Give it the
  treatment it has in HTML: italic, a rule on the left, and space below.
- Inline code such as `NEXT_ASSEMBLY_USAGE_OCCURRENCE` is one unbreakable word,
  and in justified text it stretches the rest of the line into wide gaps.
  Allow a break after each underscore.  Only inline code in prose is touched;
  listings are code blocks, and copying them must give back exactly the file.
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

function Code(code)
  if not quarto.doc.is_format("typst") or not code.text:find("_", 1, true) then
    return nil
  end
  local breakable = code.text:gsub("_", "_\u{200B}")
  return pandoc.RawInline("typst", "#raw(" .. typst_string(breakable) .. ")")
end
