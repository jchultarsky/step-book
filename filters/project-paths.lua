--[[
An `include` path that starts with "/" is relative to the project root.

HTML renders each chapter from its own directory and the PDF renders the whole
book from the project root, so a path relative to the chapter resolved in one
and not the other: Appendix A came out empty in the PDF.  This runs before the
include-code-files filter and makes such paths absolute.
]]

function CodeBlock(block)
  local path = block.attributes["include"]
  if path and path:sub(1, 1) == "/" and quarto.project.directory then
    block.attributes["include"] = pandoc.path.join({ quarto.project.directory, path:sub(2) })
    return block
  end
end
