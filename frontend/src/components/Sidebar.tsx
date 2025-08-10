import React from 'react'
import { Link, useLocation } from 'react-router-dom'
import { 
  Home, 
  Upload, 
  FileText, 
  Clock, 
  Settings,
  X 
} from 'lucide-react'

interface SidebarProps {
  isOpen: boolean
  onClose: () => void
}

const Sidebar: React.FC<SidebarProps> = ({ isOpen, onClose }) => {
  const location = useLocation()

  const navigation = [
    { name: 'Dashboard', href: '/', icon: Home },
    { name: 'Upload Audio', href: '/upload', icon: Upload },
    { name: 'Meeting Minutes', href: '/minutes', icon: FileText },
    { name: 'Recent Meetings', href: '/recent', icon: Clock },
    { name: 'Settings', href: '/settings', icon: Settings },
  ]

  const isActive = (href: string) => {
    if (href === '/') {
      return location.pathname === '/'
    }
    return location.pathname.startsWith(href)
  }

  return (
    <>
      {/* Overlay for mobile */}
      {isOpen && (
        <div 
          className="fixed inset-0 bg-gray-600 bg-opacity-75 z-40 lg:hidden"
          onClick={onClose}
        />
      )}

      {/* Sidebar */}
      <div className={`
        fixed inset-y-0 left-0 z-50 w-64 bg-white shadow-lg transform transition-transform duration-300 ease-in-out lg:translate-x-0 lg:static lg:inset-0
        ${isOpen ? 'translate-x-0' : '-translate-x-full'}
      `}>
        <div className="flex items-center justify-between p-4 border-b border-gray-200 lg:hidden">
          <div className="flex items-center space-x-2">
            <div className="w-8 h-8 bg-gradient-to-br from-india-saffron via-india-white to-india-green rounded-full flex items-center justify-center">
              <span className="text-india-blue font-bold text-sm">M</span>
            </div>
            <span className="text-lg font-bold text-gray-900">MeetNotes</span>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-md text-gray-600 hover:text-gray-900 hover:bg-gray-100"
          >
            <X size={20} />
          </button>
        </div>

        <nav className="mt-8 px-4">
          <div className="space-y-2">
            {navigation.map((item) => {
              const Icon = item.icon
              return (
                <Link
                  key={item.name}
                  to={item.href}
                  onClick={() => {
                    if (window.innerWidth < 1024) {
                      onClose()
                    }
                  }}
                  className={`
                    flex items-center space-x-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors
                    ${isActive(item.href)
                      ? 'bg-india-saffron text-white shadow-md'
                      : 'text-gray-700 hover:bg-gray-100 hover:text-gray-900'
                    }
                  `}
                >
                  <Icon size={20} />
                  <span>{item.name}</span>
                </Link>
              )
            })}
          </div>

          {/* India-specific features */}
          <div className="mt-8 pt-8 border-t border-gray-200">
            <h3 className="px-3 text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">
              India Features
            </h3>
            <div className="space-y-2">
              <div className="px-3 py-2 text-sm text-gray-600">
                <div className="flex items-center space-x-2 mb-1">
                  <span className="w-2 h-2 bg-india-saffron rounded-full"></span>
                  <span className="font-medium">Tamil Support</span>
                </div>
                <div className="flex items-center space-x-2 mb-1">
                  <span className="w-2 h-2 bg-india-green rounded-full"></span>
                  <span className="font-medium">Hindi Support</span>
                </div>
                <div className="flex items-center space-x-2">
                  <span className="w-2 h-2 bg-india-blue rounded-full"></span>
                  <span className="font-medium">English Glosses</span>
                </div>
              </div>
            </div>
          </div>
        </nav>
      </div>
    </>
  )
}

export default Sidebar