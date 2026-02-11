/**
 * Normalizes string to capitalize case while preserving content inside braces
 * Examples:
 * - "grossWeight" → "Gross Weight"
 * - "Dimensions UOM" → "Dimensions Uom"
 * - "UOM_1" → "Uom_1"
 * - "UPPER_0" → "Upper_0"
 * - "Serial/Batch#_0" → "Serial/Batch#_0"
 * - "Test (ABC)" → "Test (ABC)" - preserves content in braces
 */
const normalizeCase = str => {
  if (!str) return str

  if (str.length === 1) return str.toUpperCase()

  // Split by braces to preserve content inside them
  const parts = []
  let current = ''
  let insideBraces = false

  for (let i = 0; i < str.length; i += 1) {
    const char = str[i]

    if (char === '(' || char === '[' || char === '{') {
      if (current) {
        parts.push({ text: current, preserve: false })
        current = ''
      }
      current += char
      insideBraces = true
    } else if (char === ')' || char === ']' || char === '}') {
      current += char
      parts.push({ text: current, preserve: true })
      current = ''
      insideBraces = false
    } else {
      current += char
    }
  }

  if (current) {
    parts.push({ text: current, preserve: insideBraces })
  }

  // Process each part
  const result = parts.map(part => {
    if (part.preserve) {
      return part.text
    }

    const { text: partText } = part
    // Handle camelCase
    let text = partText.replace(/([a-z])([A-Z])/g, '$1 $2')

    // Split by delimiters and capitalize
    text = text
      .split(/(\s+|_|\/|#)/)
      .map(word => {
        if (!word || /^\s+$/.test(word) || word === '_' || word === '/' || word === '#') {
          return word
        }
        return word.charAt(0).toUpperCase() + word.slice(1).toLowerCase()
      })
      .join('')

    // ✅ Add a space before any trailing number at the end
    // e.g. "GrossWeight10" → "GrossWeight 10"
    text = text.replace(/([A-Za-z])(\d+)$/, '$1 $2')

    return text
  }).join('')

  return result
}

export default normalizeCase
