import { MessageSquare, Trash2, Clock, MoreVertical, FolderPlus, ChevronRight, ChevronDown } from 'lucide-react';
import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

import ConfirmationModal from './ConfirmationModal';
import { useToast } from '../hooks/useToast';
import { useChatSessionsContext } from '../hooks/ChatSessionsContext';
import { useChatFolders } from '../hooks/useChatFolders';
import ChatManagementModalEnhanced from './ChatManagementModalEnhanced';

interface ChatHistoryProps {
  onSelectChat?: (chatId: string) => void;
  currentModule?: string;
}

const ChatHistory: React.FC<ChatHistoryProps> = ({ onSelectChat, currentModule = 'search' }) => {
  const { sessions, currentSession, selectSession, deleteSession, createSession, createFreshSession, updateSessionTitle } = useChatSessionsContext();
  const { folders, createFolder, getChatFolder, renameFolder, deleteFolder } = useChatFolders();
  const { showSuccess, showError } = useToast();
  const [isLoading, setIsLoading] = useState(false);
  const [deleteModal, setDeleteModal] = useState<{ isOpen: boolean; chatId: string | null }>({
    isOpen: false,
    chatId: null
  });
  const [managementModal, setManagementModal] = useState<{ isOpen: boolean; chat: any | null }>({
    isOpen: false,
    chat: null
  });
  const [expandedFolders, setExpandedFolders] = useState<Set<string>>(new Set());

  const formatTimestamp = (date: Date) => {
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const minutes = Math.floor(diff / (1000 * 60));
    const hours = Math.floor(diff / (1000 * 60 * 60));
    const days = Math.floor(diff / (1000 * 60 * 60 * 24));

    if (minutes < 60) return `${minutes}m ago`;
    if (hours < 24) return `${hours}h ago`;
    if (days < 7) return `${days}d ago`;
    return date.toLocaleDateString();
  };

  const handleNewChat = () => {
    const newChatId = createSession('New conversation', currentModule);
    selectSession(newChatId);
  };

  const handleDeleteChat = (chatId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    setDeleteModal({ isOpen: true, chatId });
  };

  const confirmDeleteChat = () => {
    if (!deleteModal.chatId) return;
    
    const chatId = deleteModal.chatId;
    
    const currentIndex = sessions.findIndex(chat => chat.id === chatId);
    const nextChat = sessions.find((chat, index) => 
      index !== currentIndex && index > currentIndex
    ) || sessions.find((chat, index) => 
      index !== currentIndex && index < currentIndex
    );
    
    deleteSession(chatId);
    
    setTimeout(() => {
      if (nextChat) {
        selectSession(nextChat.id);
      } else {
        const newChatId = createSession('New conversation', currentModule);
        selectSession(newChatId);
      }
    }, 0);
    
    setDeleteModal({ isOpen: false, chatId: null });
    showSuccess('Chat deleted', 'The conversation has been successfully deleted.');
  };

  const cancelDeleteChat = () => {
    setDeleteModal({ isOpen: false, chatId: null });
  };

  const handleManageChat = (chat: any, e: React.MouseEvent) => {
    e.stopPropagation();
    setManagementModal({ isOpen: true, chat });
  };

  const handleRenameChat = (chatId: string, newTitle: string) => {
    try {
      updateSessionTitle(chatId, newTitle);
      setManagementModal({ isOpen: false, chat: null });
      showSuccess('Chat renamed', 'The conversation title has been updated.');
    } catch (error) {
      showError('Failed to rename', 'There was an error updating the chat title.');
    }
  };

  const toggleFolder = (folderId: string) => {
    setExpandedFolders(prev => {
      const newSet = new Set(prev);
      if (newSet.has(folderId)) {
        newSet.delete(folderId);
      } else {
        newSet.add(folderId);
      }
      return newSet;
    });
  };

  // Organize chats by folder
  const chatsByFolder: { [key: string]: typeof sessions } = {
    'no-folder': []
  };
  
  folders.forEach(folder => {
    chatsByFolder[folder.id] = [];
  });

  sessions.forEach(chat => {
    const folderId = getChatFolder(chat.id);
    if (folderId && chatsByFolder[folderId]) {
      chatsByFolder[folderId].push(chat);
    } else {
      chatsByFolder['no-folder'].push(chat);
    }
  });

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
    <div className="h-full flex flex-col sidebar-gradient sidebar-typography">
      {/* Header */}
      <div className="px-4 h-12 border-b border-[color:var(--border)] flex items-center">
        <div className="flex items-center justify-between w-full">
          <h2 className="text-base font-bold uppercase font-mono heading tracking-widest text-left">
            Recents
          </h2>
          <div className="flex items-center gap-2">
            {/* Buttons moved to top bar */}
          </div>
        </div>
      </div>

      {/* Chat List */}
      <div className="flex-1 overflow-y-auto">
        {isLoading ? (
          <div className="flex items-center justify-center h-32">
            <div className="empty">Loading chats...</div>
          </div>
        ) : sessions.length === 0 ? (
          <div className="text-center py-8">
            <div className="empty mb-4">No conversations yet</div>
            <button
              onClick={handleNewChat}
              className="px-4 py-2 rounded text-sm transition-colors tutor-btn"
            >
              Start your first chat
            </button>
          </div>
        ) : (
          <div className="space-y-1 p-2">
            {/* Uncategorized Chats */}
            {chatsByFolder['no-folder'].length > 0 && (
              <div className="mb-2">
                {chatsByFolder['no-folder'].map((chat) => (
                  <div
                    key={chat.id}
                    className={`chat-history-item flex items-center justify-between rounded-lg cursor-pointer group ${
                      currentSession?.id === chat.id 
                        ? 'elevated bg-[color:var(--panel)]' 
                        : ''
                    }`}
                    onClick={() => {
                      selectSession(chat.id);
                    }}
                  >
                    <div className="flex items-center space-x-3 flex-1 min-w-0">
                      <div className="flex-1 min-w-0">
                        <div className={`text-[13px] font-normal truncate ${
                          chat.title === 'New conversation' ? 'empty' : 'text-[color:var(--ink-700)]'
                        }`}>
                          {chat.title}
                        </div>
                        <div className="meta text-gray-500">
                          {formatTimestamp(chat.timestamp)} • {chat.messageCount} messages
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-all">
                      <button
                        onClick={(e) => handleManageChat(chat, e)}
                        className="p-1.5 hover:bg-gray-100 rounded transition-all text-gray-500 hover:text-gray-700"
                        title="Manage chat"
                      >
                        <MoreVertical className="w-4 h-4" />
                      </button>
                      <button
                        onClick={(e) => handleDeleteChat(chat.id, e)}
                        className="p-1.5 hover:bg-red-50 rounded transition-all text-red-500 hover:text-red-600"
                        title="Delete chat"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* Folders */}
            {folders.map(folder => (
              <div key={folder.id} className="mb-2">
                {/* Folder Header */}
                <button
                  onClick={() => toggleFolder(folder.id)}
                  className="w-full flex items-center gap-2 px-2 py-2 hover:bg-gray-100/50 rounded transition-colors"
                >
                  {expandedFolders.has(folder.id) ? (
                    <ChevronDown className="w-4 h-4 text-gray-500" />
                  ) : (
                    <ChevronRight className="w-4 h-4 text-gray-500" />
                  )}
                  <div
                    className="w-3 h-3 rounded-full"
                    style={{ backgroundColor: folder.color }}
                  />
                  <span className="text-[13px] font-normal text-gray-700 flex-1 text-left truncate">
                    {folder.name}
                  </span>
                  <span className="meta text-gray-500">
                    {chatsByFolder[folder.id]?.length || 0}
                  </span>
                </button>

                {/* Folder Contents */}
                <AnimatePresence>
                  {expandedFolders.has(folder.id) && (
                    <motion.div
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: 'auto' }}
                      exit={{ opacity: 0, height: 0 }}
                      transition={{ duration: 0.2 }}
                      className="ml-4"
                    >
                      {chatsByFolder[folder.id]?.map((chat) => (
                        <div
                          key={chat.id}
                          className={`chat-history-item flex items-center justify-between rounded-lg cursor-pointer group ${
                            currentSession?.id === chat.id 
                              ? 'elevated bg-[color:var(--panel)]' 
                              : ''
                          }`}
                          onClick={() => {
                            selectSession(chat.id);
                          }}
                        >
                          <div className="flex items-center space-x-3 flex-1 min-w-0">
                            <div className="flex-1 min-w-0">
                              <div className={`text-[13px] font-medium truncate ${
                                chat.title === 'New conversation' ? 'empty' : 'text-[color:var(--ink-700)]'
                              }`}>
                                {chat.title}
                              </div>
                              <div className="meta text-gray-500">
                                {formatTimestamp(chat.timestamp)} • {chat.messageCount} messages
                              </div>
                            </div>
                          </div>

                          <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-all">
                            <button
                              onClick={(e) => handleManageChat(chat, e)}
                              className="p-1.5 hover:bg-gray-100 rounded transition-all text-gray-500 hover:text-gray-700"
                              title="Manage chat"
                            >
                              <MoreVertical className="w-4 h-4" />
                            </button>
                            <button
                              onClick={(e) => handleDeleteChat(chat.id, e)}
                              className="p-1.5 hover:bg-red-50 rounded transition-all text-red-500 hover:text-red-600"
                              title="Delete chat"
                            >
                              <Trash2 className="w-4 h-4" />
                            </button>
                          </div>
                        </div>
                      ))}
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            ))}
          </div>
        )}
      </div>
      
      {/* Delete Confirmation Modal */}
      <ConfirmationModal
        isOpen={deleteModal.isOpen}
        onClose={cancelDeleteChat}
        onConfirm={confirmDeleteChat}
        title="Delete Conversation"
        message="Are you sure you want to delete this conversation? This action cannot be undone."
        confirmText="Delete"
        cancelText="Cancel"
        variant="danger"
      />

      {/* Chat Management Modal */}
      <ChatManagementModalEnhanced
        isOpen={managementModal.isOpen}
        onClose={() => setManagementModal({ isOpen: false, chat: null })}
        chat={managementModal.chat}
        onDelete={(chatId) => {
          setManagementModal({ isOpen: false, chat: null });
          setDeleteModal({ isOpen: true, chatId });
        }}
        onRename={handleRenameChat}
      />

    </div>
  );
};

export default ChatHistory;
