import { FileDown, Presentation, Check } from 'lucide-react'
import { cn } from '@/lib/utils'

interface PowerPointResultProps {
  filename: string
  downloadUrl: string
  slidesCount?: number
  title?: string
  className?: string
}

export const PowerPointResult = ({ 
  filename, 
  downloadUrl, 
  slidesCount,
  title,
  className 
}: PowerPointResultProps) => {
  return (
    <div className={cn(
      "border border-gray-200 rounded-lg p-4 bg-gradient-to-r from-blue-50 to-indigo-50",
      className
    )}>
      <div className="flex items-start gap-4">
        <div className="flex-shrink-0">
          <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-lg flex items-center justify-center text-white">
            <Presentation className="w-6 h-6" />
          </div>
        </div>
        
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <Check className="w-4 h-4 text-green-500" />
            <p className="text-sm font-medium text-gray-900">
              Présentation générée avec succès
            </p>
          </div>
          
          {title && (
            <h3 className="text-lg font-semibold text-gray-900 mb-1 truncate">
              {title}
            </h3>
          )}
          
          <p className="text-sm text-gray-600 mb-3">
            {filename} 
            {slidesCount && ` • ${slidesCount} slides`}
          </p>
          
          <a
            href={downloadUrl}
            download={filename}
            className={cn(
              "inline-flex items-center gap-2 px-4 py-2",
              "bg-gradient-to-r from-blue-500 to-indigo-600",
              "text-white font-medium text-sm rounded-lg",
              "hover:from-blue-600 hover:to-indigo-700",
              "transition-all duration-200",
              "shadow-lg hover:shadow-xl"
            )}
          >
            <FileDown className="w-4 h-4" />
            Télécharger la présentation
          </a>
        </div>
      </div>
    </div>
  )
}