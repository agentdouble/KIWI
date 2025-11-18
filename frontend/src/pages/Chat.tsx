import { useParams } from 'react-router-dom'
import { ChatContainer } from '@/components/chat/ChatContainer'
import { ChatErrorBoundary } from '@/components/ErrorBoundary/ChatErrorBoundary'

export const Chat = () => {
  const { chatId } = useParams<{ chatId?: string }>()
  
  return (
    <ChatErrorBoundary>
      <ChatContainer initialChatId={chatId} />
    </ChatErrorBoundary>
  )
}