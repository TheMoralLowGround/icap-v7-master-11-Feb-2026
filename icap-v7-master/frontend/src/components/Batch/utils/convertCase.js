const toCamelCase = str => str
  .replace(/[-_ ](.)/g, (_, group1) => group1.toUpperCase())
  .replace(/^(.)/, match => match.toLowerCase())

export default toCamelCase
