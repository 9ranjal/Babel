import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { AlertTriangle, X } from 'lucide-react';

interface ConfirmationModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  title: string;
  message: string;
  confirmText?: string;
  cancelText?: string;
  variant?: 'danger' | 'warning' | 'info';
  isLoading?: boolean;
}

export default function ConfirmationModal({
  isOpen,
  onClose,
  onConfirm,
  title,
  message,
  confirmText = 'Confirm',
  cancelText = 'Cancel',
  variant = 'danger',
  isLoading = false
}: ConfirmationModalProps) {
  if (!isOpen) return null;

  const getVariantStyles = () => {
    switch (variant) {
      case 'danger':
        return {
          icon: AlertTriangle,
          iconColor: 'text-red-500',
          confirmBg: 'bg-red-600 hover:bg-red-700',
          confirmText: 'text-white',
          border: 'border-red-500/20'
        };
      case 'warning':
        return {
          icon: AlertTriangle,
          iconColor: 'text-yellow-500',
          confirmBg: 'bg-yellow-600 hover:bg-yellow-700',
          confirmText: 'text-white',
          border: 'border-yellow-500/20'
        };
      case 'info':
        return {
          icon: AlertTriangle,
          iconColor: 'text-blue-500',
          confirmBg: 'bg-blue-600 hover:bg-blue-700',
          confirmText: 'text-white',
          border: 'border-blue-500/20'
        };
    }
  };

  const styles = getVariantStyles();
  const Icon = styles.icon;

  return (
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
            <div className={`bg-white rounded-lg shadow-xl max-w-md w-full border ${styles.border}`}>
              {/* Header */}
              <div className="flex items-center justify-between p-6 pb-4">
                <div className="flex items-center gap-3">
                  <div className={`p-2 rounded-full bg-gray-100`}>
                    <Icon className={`w-5 h-5 ${styles.iconColor}`} />
                  </div>
                  <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
                </div>
                <button
                  onClick={onClose}
                  className="text-gray-400 hover:text-gray-600 transition-colors"
                  disabled={isLoading}
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
              
              {/* Content */}
              <div className="px-6 pb-6">
                <p className="text-gray-600 leading-relaxed">{message}</p>
                
                {/* Actions */}
                <div className="flex gap-3 mt-6">
                  <button
                    onClick={onClose}
                    disabled={isLoading}
                    className="flex-1 px-4 py-2 text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-md transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {cancelText}
                  </button>
                  <button
                    onClick={onConfirm}
                    disabled={isLoading}
                    className={`flex-1 px-4 py-2 ${styles.confirmBg} ${styles.confirmText} rounded-md transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2`}
                  >
                    {isLoading && (
                      <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    )}
                    {confirmText}
                  </button>
                </div>
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}

