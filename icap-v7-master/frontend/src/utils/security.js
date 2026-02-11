const isBlockedHref = value => /^\s*javascript:/i.test(value || '')

const sanitizeNodeAttributes = node => {
  Array.from(node.attributes || []).forEach(attr => {
    if (/^on/i.test(attr.name) || isBlockedHref(attr.value)) {
      node.removeAttribute(attr.name)
    }
  })
}

const sanitizeTree = root => {
  const walker = document.createTreeWalker(root, NodeFilter.SHOW_ELEMENT, null, false)
  const nodesToRemove = []

  let current = walker.currentNode
  while (current) {
    if (current.tagName && current.tagName.toLowerCase() === 'script') {
      nodesToRemove.push(current)
    } else {
      sanitizeNodeAttributes(current)
    }
    current = walker.nextNode()
  }

  nodesToRemove.forEach(node => node.parentNode?.removeChild(node))
}

export default function sanitizeHtml(html) {
  if (typeof window === 'undefined' || typeof document === 'undefined') {
    return typeof html === 'string' ? html : ''
  }

  const template = document.createElement('template')
  template.innerHTML = typeof html === 'string' ? html : ''

  sanitizeTree(template.content)

  return template.innerHTML
}
