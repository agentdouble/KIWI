import { useState } from 'react'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { vscDarkPlus, vs } from 'react-syntax-highlighter/dist/esm/styles/prism'
import { Copy, Check, Terminal } from 'lucide-react'
import { useTheme } from '@/hooks/useTheme'
import { toast } from 'sonner'
import { cn } from '@/lib/utils'

interface CodeBlockProps {
  language?: string
  value: string
}

export const CodeBlock = ({ language = 'plaintext', value }: CodeBlockProps) => {
  const [copied, setCopied] = useState(false)
  const { theme } = useTheme()

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(value)
      setCopied(true)
      toast.success('Code copié')
      setTimeout(() => setCopied(false), 2000)
    } catch (error) {
      toast.error('Erreur lors de la copie')
    }
  }

  return (
    <div className="relative group my-4">
      <div className="absolute top-0 left-0 right-0 flex items-center justify-between px-4 py-2 bg-gray-800 dark:bg-gray-900 rounded-t-lg">
        <div className="flex items-center gap-2 text-gray-400 text-sm">
          <Terminal className="w-4 h-4" />
          <span>{language}</span>
        </div>
        
        <button
          onClick={handleCopy}
          className={cn(
            "flex items-center gap-1 px-2 py-1 text-xs rounded transition-all",
            "text-gray-400 hover:text-white hover:bg-gray-700",
            "opacity-0 group-hover:opacity-100"
          )}
        >
          {copied ? (
            <>
              <Check className="w-3 h-3" />
              Copié!
            </>
          ) : (
            <>
              <Copy className="w-3 h-3" />
              Copier
            </>
          )}
        </button>
      </div>

      <div className="pt-10">
        <SyntaxHighlighter
          language={language}
          style={theme === 'dark' ? vscDarkPlus : vs}
          customStyle={{
            margin: 0,
            borderRadius: '0 0 0.5rem 0.5rem',
            fontSize: '0.875rem',
          }}
          showLineNumbers
        >
          {value}
        </SyntaxHighlighter>
      </div>
    </div>
  )
}

// Composant inline pour le code
export const InlineCode = ({ children }: { children: React.ReactNode }) => {
  return (
    <code className="px-1.5 py-0.5 rounded bg-gray-100 dark:bg-gray-800 text-sm font-mono text-gray-800 dark:text-gray-200">
      {children}
    </code>
  )
}