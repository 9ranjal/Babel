import { createContext, useContext, useState, useCallback, useEffect, ReactNode } from 'react';

export interface ChatFolder {
  id: string;
  name: string;
  color?: string;
  icon?: string;
  createdAt: Date;
}

interface ChatFoldersContextType {
  folders: ChatFolder[];
  createFolder: (name: string, color?: string) => string;
  deleteFolder: (folderId: string) => void;
  renameFolder: (folderId: string, newName: string) => void;
  getChatFolder: (chatId: string) => string | null;
  moveChatToFolder: (chatId: string, folderId: string | null) => void;
}

const ChatFoldersContext = createContext<ChatFoldersContextType | undefined>(undefined);

const FOLDERS_STORAGE_KEY = 'chat_folders';
const CHAT_FOLDER_MAP_KEY = 'chat_folder_map';

export function ChatFoldersProvider({ children }: { children: ReactNode }) {
  const [folders, setFolders] = useState<ChatFolder[]>([]);
  const [chatFolderMap, setChatFolderMap] = useState<Record<string, string>>({});

  // Load folders from localStorage on mount
  useEffect(() => {
    try {
      const storedFolders = localStorage.getItem(FOLDERS_STORAGE_KEY);
      const storedMap = localStorage.getItem(CHAT_FOLDER_MAP_KEY);
      
      if (storedFolders) {
        const parsed = JSON.parse(storedFolders);
        setFolders(parsed.map((f: any) => ({
          ...f,
          createdAt: new Date(f.createdAt)
        })));
      }
      
      if (storedMap) {
        setChatFolderMap(JSON.parse(storedMap));
      }
    } catch (error) {
      console.error('Failed to load chat folders:', error);
    }
  }, []);

  // Save folders to localStorage whenever they change
  useEffect(() => {
    try {
      localStorage.setItem(FOLDERS_STORAGE_KEY, JSON.stringify(folders));
    } catch (error) {
      console.error('Failed to save chat folders:', error);
    }
  }, [folders]);

  // Save chat-folder mapping to localStorage
  useEffect(() => {
    try {
      localStorage.setItem(CHAT_FOLDER_MAP_KEY, JSON.stringify(chatFolderMap));
    } catch (error) {
      console.error('Failed to save chat folder map:', error);
    }
  }, [chatFolderMap]);

  const createFolder = useCallback((name: string, color?: string): string => {
    const newFolder: ChatFolder = {
      id: Date.now().toString() + Math.random().toString(36).substr(2, 9),
      name,
      color: color || '#3B82F6',
      createdAt: new Date()
    };
    
    setFolders(prev => [...prev, newFolder]);
    return newFolder.id;
  }, []);

  const deleteFolder = useCallback((folderId: string) => {
    setFolders(prev => prev.filter(f => f.id !== folderId));
    
    // Remove all chats from this folder
    setChatFolderMap(prev => {
      const newMap = { ...prev };
      Object.keys(newMap).forEach(chatId => {
        if (newMap[chatId] === folderId) {
          delete newMap[chatId];
        }
      });
      return newMap;
    });
  }, []);

  const renameFolder = useCallback((folderId: string, newName: string) => {
    setFolders(prev => prev.map(f => 
      f.id === folderId ? { ...f, name: newName } : f
    ));
  }, []);

  const getChatFolder = useCallback((chatId: string): string | null => {
    return chatFolderMap[chatId] || null;
  }, [chatFolderMap]);

  const moveChatToFolder = useCallback((chatId: string, folderId: string | null) => {
    setChatFolderMap(prev => {
      const newMap = { ...prev };
      if (folderId === null) {
        delete newMap[chatId];
      } else {
        newMap[chatId] = folderId;
      }
      return newMap;
    });
  }, []);

  const contextValue: ChatFoldersContextType = {
    folders,
    createFolder,
    deleteFolder,
    renameFolder,
    getChatFolder,
    moveChatToFolder
  };

  return (
    <ChatFoldersContext.Provider value={contextValue}>
      {children}
    </ChatFoldersContext.Provider>
  );
}

export function useChatFolders() {
  const context = useContext(ChatFoldersContext);
  if (context === undefined) {
    throw new Error('useChatFolders must be used within a ChatFoldersProvider');
  }
  return context;
}

