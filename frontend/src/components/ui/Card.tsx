import { ReactNode } from 'react'

interface CardProps {
  children: ReactNode
  className?: string
  hover?: boolean
  padding?: 'none' | 'sm' | 'md' | 'lg'
}

export default function Card({ 
  children, 
  className = '', 
  hover = false,
  padding = 'md'
}: CardProps) {
  const paddingClasses = {
    none: '',
    sm: 'p-4',
    md: 'p-6',
    lg: 'p-8',
  }
  
  return (
    <div className={`
      bg-white rounded-xl shadow-sm border border-gray-100
      ${paddingClasses[padding]}
      ${hover ? 'card-hover cursor-pointer' : ''}
      ${className}
    `}>
      {children}
    </div>
  )
}

