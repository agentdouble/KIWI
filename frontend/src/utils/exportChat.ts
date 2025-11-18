import type { Chat } from '@/types/chat'

export const exportChat = (chat: Chat, format: 'json' | 'markdown' | 'txt' = 'markdown') => {
  const timestamp = new Date().toISOString().replace(/[:.]/g, '-')
  const filename = `chat-${chat.title.replace(/[^a-z0-9]/gi, '-')}-${timestamp}`

  switch (format) {
    case 'json':
      return exportAsJSON(chat, filename)
    case 'markdown':
      return exportAsMarkdown(chat, filename)
    case 'txt':
      return exportAsText(chat, filename)
    default:
      throw new Error(`Format non supporté: ${format}`)
  }
}

const exportAsJSON = (chat: Chat, filename: string) => {
  const data = JSON.stringify(chat, null, 2)
  downloadFile(data, `${filename}.json`, 'application/json')
}

const exportAsMarkdown = (chat: Chat, filename: string) => {
  let markdown = `# ${chat.title}\n\n`
  markdown += `_Créé le ${new Date(chat.createdAt).toLocaleString('fr-FR')}_\n\n`
  markdown += `---\n\n`

  chat.messages.forEach((message) => {
    const role = message.role === 'user' ? '**Vous**' : '**Assistant**'
    const time = new Date(message.createdAt).toLocaleTimeString('fr-FR')
    
    markdown += `### ${role} - ${time}\n\n`
    markdown += `${message.content}\n\n`
    markdown += `---\n\n`
  })

  downloadFile(markdown, `${filename}.md`, 'text/markdown')
}

const exportAsText = (chat: Chat, filename: string) => {
  let text = `${chat.title}\n`
  text += `${'='.repeat(chat.title.length)}\n\n`
  text += `Créé le ${new Date(chat.createdAt).toLocaleString('fr-FR')}\n\n`
  text += `${'-'.repeat(50)}\n\n`

  chat.messages.forEach((message) => {
    const role = message.role === 'user' ? 'VOUS' : 'ASSISTANT'
    const time = new Date(message.createdAt).toLocaleTimeString('fr-FR')
    
    text += `[${role} - ${time}]\n`
    text += `${message.content}\n\n`
    text += `${'-'.repeat(50)}\n\n`
  })

  downloadFile(text, `${filename}.txt`, 'text/plain')
}

const downloadFile = (content: string, filename: string, type: string) => {
  const blob = new Blob([content], { type })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}