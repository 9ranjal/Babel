import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Trash2, Edit3, Copy, X, Check, FolderOpen, ChevronDown, Plus } from 'lucide-react';
import ConfirmationModal from './ConfirmationModal';
import { useChatFolders } from '../hooks/useChatFolders';

interface ChatSession {
  id: string;
  title: string;
  timestamp: Date;
  messageCount: number;
  module: string;
  messages: any[];
}

interface ChatManagementModalEnhancedProps {
  isOpen: boolean;
  onClose: () => void;
  chat: ChatSession | null;
  onDelete: (chatId: string) => void;
  onRename: (chatId: string, newTitle: string) => void;
}

export default function ChatManagementModalEnhanced({
  isOpen,
  onClose,
  chat,
  onDelete,
  onRename
}: ChatManagementModalEnhancedProps) {
  const { folders, createFolder, getChatFolder, moveChatToFolder } = useChatFolders();
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [editTitle, setEditTitle] = useState('');
  const [copied, setCopied] = useState(false);
  const [showFolderMenu, setShowFolderMenu] = useState(false);
  const [showNewFolderModal, setShowNewFolderModal] = useState(false);
  const [newFolderName, setNewFolderName] = useState('');
  const [newFolderColor, setNewFolderColor] = useState('#3B82F6');

  if (!isOpen || !chat) return null;

  const currentFolderId = getChatFolder(chat.id);
  const currentFolder = folders.find(f => f.id === currentFolderId);

  const handleDelete = () => {
    onDelete(chat.id);
    setShowDeleteModal(false);
    onClose();
  };

  const handleRename = () => {
    if (editTitle.trim() && editTitle.trim() !== chat.title) {
      onRename(chat.id, editTitle.trim());
    }
    setIsEditing(false);
  };

  const handleCopyId = async () => {
    try {
      await navigator.clipboard.writeText(chat.id);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy chat ID:', err);
    }
  };

  const handleMoveToFolder = (folderId: string | null) => {
    moveChatToFolder(chat.id, folderId);
    setShowFolderMenu(false);
  };

  const handleCreateFolder = () => {
    if (newFolderName.trim()) {
      const folderId = createFolder(newFolderName.trim(), newFolderColor);
      moveChatToFolder(chat.id, folderId);
      setShowNewFolderModal(false);
      setNewFolderName('');
      setNewFolderColor('#3B82F6');
      setShowFolderMenu(false);
    }
  };

  const colors = [
    '#3B82F6', '#10B981', '#F59E0B', '#EF4444',
    '#8B5CF6', '#EC4899', '#06B6D4', '#F97316'
  ];

  const formatTimestamp = (date: Date) => {
    return new Intl.DateTimeFormat('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    }).format(date);
  };

  const getModuleIcon = (module: string) => {
    switch (module) {
      case 'quiz': return 'Q';
      case 'notes': return '▤';
      case 'flashcards': return '⧉';
      case 'search': return '⌕';
      default: return '💬';
    }
  };

  return (
    <>
      <AnimatePresence>
        {isOpen && (
          <>
            {/* Backdrop */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 bg-black/50 backdrop-blur-sm z-[1000002]"
              onClick={onClose}
            />
            
            {/* Modal */}
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 20 }}
              transition={{ type: "spring", damping: 25, stiffness: 300 }}
              className="fixed inset-0 z-[1000002] flex items-center justify-center p-4"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="bg-white rounded-lg shadow-xl max-w-md w-full border border-gray-200">
                {/* Header */}
                <div className="flex items-center justify-between p-6 pb-4">
                  <div className="flex items-center gap-3">
                    <div className="p-2 rounded-full bg-blue-100">
                      <span className="text-lg">{getModuleIcon(chat.module)}</span>
                    </div>
                    <div>
                      <h3 className="text-lg font-semibold text-gray-900">Chat Options</h3>
                      <p className="text-sm text-gray-500">{formatTimestamp(chat.timestamp)}</p>
                    </div>
                  </div>
                  <button
                    onClick={onClose}
                    className="text-gray-400 hover:text-gray-600 transition-colors"
                  >
                    <X className="w-5 h-5" />
                  </button>
                </div>
                
                {/* Content */}
                <div className="px-6 pb-6">
                  {/* Chat Title */}
                  <div className="mb-6">
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Chat Title
                    </label>
                    {isEditing ? (
                      <div className="flex gap-2">
                        <input
                          type="text"
                          value={editTitle}
                          onChange={(e) => setEditTitle(e.target.value)}
                          className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                          autoFocus
                          onKeyDown={(e) => {
                            if (e.key === 'Enter') handleRename();
                            if (e.key === 'Escape') setIsEditing(false);
                          }}
                        />
                        <button
                          onClick={handleRename}
                          className="px-3 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
                        >
                          <Check className="w-4 h-4" />
                        </button>
                      </div>
                    ) : (
                      <div className="flex items-center gap-2">
                        <span className="text-gray-900 flex-1 truncate">{chat.title}</span>
                        <button
                          onClick={() => {
                            setIsEditing(true);
                            setEditTitle(chat.title);
                          }}
                          className="p-1 text-gray-400 hover:text-gray-600 transition-colors"
                        >
                          <Edit3 className="w-4 h-4" />
                        </button>
                      </div>
                    )}
                  </div>

                  {/* Chat Info */}
                  <div className="mb-6 space-y-3">
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-500">Messages:</span>
                      <span className="text-gray-900">{chat.messageCount}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-500">Module:</span>
                      <span className="text-gray-900 capitalize">{chat.module}</span>
                    </div>
                    {currentFolder && (
                      <div className="flex justify-between text-sm">
                        <span className="text-gray-500">Folder:</span>
                        <div className="flex items-center gap-2">
                          <div
                            className="w-3 h-3 rounded-full"
                            style={{ backgroundColor: currentFolder.color }}
                          />
                          <span className="text-gray-900">{currentFolder.name}</span>
                        </div>
                      </div>
                    )}
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-500">Chat ID:</span>
                      <div className="flex items-center gap-2">
                        <span className="text-gray-900 font-mono text-xs">{chat.id.slice(0, 8)}...</span>
                        <button
                          onClick={handleCopyId}
                          className="p-1 text-gray-400 hover:text-gray-600 transition-colors"
                          title="Copy full ID"
                        >
                          {copied ? (
                            <Check className="w-3 h-3 text-green-500" />
                          ) : (
                            <Copy className="w-3 h-3" />
                          )}
                        </button>
                      </div>
                    </div>
                  </div>
                  
                  {/* Actions */}
                  <div className="mb-4">
                    {/* Move to Folder Button with Dropdown */}
                    <div className="relative mb-3">
                      <button
                        onClick={() => setShowFolderMenu(!showFolderMenu)}
                        className="w-full flex items-center justify-center gap-2 px-4 py-3 text-purple-600 bg-purple-50 hover:bg-purple-100 rounded-md transition-colors"
                      >
                        <FolderOpen className="w-4 h-4" />
                        <span className="text-sm font-medium">Move to Folder</span>
                        <ChevronDown className="w-3 h-3" />
                      </button>

                      {/* Folder Submenu */}
                      <AnimatePresence>
                        {showFolderMenu && (
                          <motion.div
                            initial={{ opacity: 0, y: -10 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0, y: -10 }}
                            className="absolute top-full left-0 mt-2 w-full bg-white rounded-md shadow-lg border border-gray-200 overflow-hidden z-10 max-h-64 overflow-y-auto"
                          >
                            {/* No Folder Option */}
                            <button
                              onClick={() => handleMoveToFolder(null)}
                              className={`w-full px-4 py-2 flex items-center gap-2 hover:bg-gray-50 transition-colors text-left ${
                                !currentFolderId ? 'bg-gray-50' : ''
                              }`}
                            >
                              <div className="w-3 h-3 rounded-full bg-gray-400" />
                              <span className="text-sm text-gray-700">No folder</span>
                            </button>

                            {/* Existing Folders */}
                            {folders.map(folder => (
                              <button
                                key={folder.id}
                                onClick={() => handleMoveToFolder(folder.id)}
                                className={`w-full px-4 py-2 flex items-center gap-2 hover:bg-gray-50 transition-colors text-left ${
                                  currentFolderId === folder.id ? 'bg-gray-50' : ''
                                }`}
                              >
                                <div
                                  className="w-3 h-3 rounded-full"
                                  style={{ backgroundColor: folder.color }}
                                />
                                <span className="text-sm text-gray-700">{folder.name}</span>
                              </button>
                            ))}

                            {/* Create New Folder */}
                            <div className="border-t border-gray-200">
                              <button
                                onClick={() => {
                                  setShowNewFolderModal(true);
                                  setShowFolderMenu(false);
                                }}
                                className="w-full px-4 py-2 flex items-center gap-2 hover:bg-gray-50 transition-colors text-left"
                              >
                                <Plus className="w-4 h-4 text-purple-500" />
                                <span className="text-sm text-purple-600">New folder</span>
                              </button>
                            </div>
                          </motion.div>
                        )}
                      </AnimatePresence>
                    </div>

                    {/* Delete Button */}
                    <button
                      onClick={() => setShowDeleteModal(true)}
                      className="w-full flex items-center justify-center gap-2 px-4 py-3 text-red-600 bg-red-50 hover:bg-red-100 rounded-md transition-colors"
                    >
                      <Trash2 className="w-4 h-4" />
                      <span className="text-sm font-medium">Delete Chat</span>
                    </button>
                  </div>
                </div>
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>

      {/* Delete Confirmation Modal */}
      <ConfirmationModal
        isOpen={showDeleteModal}
        onClose={() => setShowDeleteModal(false)}
        onConfirm={handleDelete}
        title="Delete Conversation"
        message="Are you sure you want to delete this conversation? This action cannot be undone."
        confirmText="Delete"
        cancelText="Cancel"
        variant="danger"
      />

      {/* New Folder Modal */}
      <AnimatePresence>
        {showNewFolderModal && (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 bg-black/50 backdrop-blur-sm z-[60]"
              onClick={() => setShowNewFolderModal(false)}
            />
            
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 20 }}
              transition={{ type: "spring", damping: 25, stiffness: 300 }}
              className="fixed inset-0 z-[60] flex items-center justify-center p-4"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="bg-white rounded-lg shadow-xl max-w-md w-full border border-gray-200">
                <div className="flex items-center justify-between p-6 pb-4">
                  <h3 className="text-lg font-semibold text-gray-900">Create New Folder</h3>
                  <button
                    onClick={() => setShowNewFolderModal(false)}
                    className="text-gray-400 hover:text-gray-600 transition-colors"
                  >
                    <X className="w-5 h-5" />
                  </button>
                </div>
                
                <div className="px-6 pb-6">
                  <div className="mb-4">
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Folder Name
                    </label>
                    <input
                      type="text"
                      value={newFolderName}
                      onChange={(e) => setNewFolderName(e.target.value)}
                      placeholder="Enter folder name"
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                      autoFocus
                      onKeyDown={(e) => {
                        if (e.key === 'Enter') handleCreateFolder();
                        if (e.key === 'Escape') setShowNewFolderModal(false);
                      }}
                    />
                  </div>

                  <div className="mb-6">
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Color
                    </label>
                    <div className="flex gap-2 flex-wrap">
                      {colors.map(color => (
                        <button
                          key={color}
                          onClick={() => setNewFolderColor(color)}
                          className={`w-8 h-8 rounded-full transition-transform ${
                            newFolderColor === color ? 'ring-2 ring-offset-2 ring-gray-400 scale-110' : ''
                          }`}
                          style={{ backgroundColor: color }}
                        />
                      ))}
                    </div>
                  </div>
                  
                  <div className="flex gap-3">
                    <button
                      onClick={() => setShowNewFolderModal(false)}
                      className="flex-1 px-4 py-2 text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-md transition-colors"
                    >
                      Cancel
                    </button>
                    <button
                      onClick={handleCreateFolder}
                      disabled={!newFolderName.trim()}
                      className="flex-1 px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-md transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      Create
                    </button>
                  </div>
                </div>
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </>
  );
}

