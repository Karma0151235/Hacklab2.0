"use client";

import { useState } from "react";
import { Plus, MessageSquare, Trash2, MoreVertical, Edit2 } from "lucide-react";
import { useCopilotStore, ChatSession } from "@/stores/use-copilot-store";
import { cn } from "@/lib/utils";
import { motion, AnimatePresence } from "framer-motion";

export function ChatSidebar() {
  const {
    chats,
    currentChatId,
    createNewChat,
    deleteChat,
    switchChat,
    renameChat,
  } = useCopilotStore();
  const [menuOpen, setMenuOpen] = useState<string | null>(null);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editingTitle, setEditingTitle] = useState("");
  const [confirmDelete, setConfirmDelete] = useState<string | null>(null);

  const chatList = Object.values(chats).sort(
    (a, b) => new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime(),
  );

  const handleNewChat = () => {
    createNewChat();
    setMenuOpen(null);
  };

  const handleDelete = (chatId: string) => {
    deleteChat(chatId);
    setConfirmDelete(null);
    setMenuOpen(null);
  };

  const handleStartEdit = (chat: ChatSession) => {
    setEditingId(chat.id);
    setEditingTitle(chat.title);
    setMenuOpen(null);
  };

  const handleSaveEdit = (chatId: string) => {
    if (editingTitle.trim()) {
      renameChat(chatId, editingTitle);
    }
    setEditingId(null);
  };

  const handleKeyDown = (e: React.KeyboardEvent, chatId: string) => {
    if (e.key === "Enter") {
      handleSaveEdit(chatId);
    } else if (e.key === "Escape") {
      setEditingId(null);
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const today = new Date();
    const yesterday = new Date(today);
    yesterday.setDate(yesterday.getDate() - 1);

    if (date.toDateString() === today.toDateString()) {
      return date.toLocaleTimeString("en-US", {
        hour: "2-digit",
        minute: "2-digit",
      });
    } else if (date.toDateString() === yesterday.toDateString()) {
      return "Yesterday";
    } else {
      return date.toLocaleDateString("en-US", {
        month: "short",
        day: "numeric",
      });
    }
  };

  return (
    <div className="flex h-full flex-col bg-gradient-to-b from-bg-secondary to-bg-primary border-r border-border-primary">
      {/* Header */}
      <div className="border-b border-border-primary p-3 space-y-2">
        <div className="flex items-center gap-2 px-1 mb-2">
          <div className="h-2 w-2 rounded-full bg-cyan-500/60"></div>
          <h2 className="text-xs font-semibold uppercase tracking-widest text-text-secondary">
            Chats
          </h2>
        </div>
        <button
          onClick={handleNewChat}
          className="flex w-full items-center justify-center gap-2 rounded-lg bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 px-3 py-2 text-xs font-semibold text-white transition-all duration-200 shadow-lg hover:shadow-cyan-500/20 group"
        >
          <Plus className="h-3.5 w-3.5 group-hover:rotate-90 transition-transform duration-300" />
          New
        </button>
      </div>

      {/* Chat List */}
      <div className="flex-1 overflow-y-auto scrollbar-thin scrollbar-thumb-gray-700 scrollbar-track-gray-800">
        <div className="space-y-1.5 p-2.5">
          {chatList.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <MessageSquare className="h-8 w-8 text-text-dim mb-3" />
              <p className="text-xs text-text-tertiary">No chats yet</p>
              <p className="text-[10px] text-text-dim">
                Create one to get started
              </p>
            </div>
          ) : (
            <AnimatePresence mode="popLayout">
              {chatList.map((chat) => (
                <motion.div
                  key={chat.id}
                  layout
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  transition={{ duration: 0.2 }}
                  className="relative"
                >
                  {editingId === chat.id ? (
                    // Edit mode
                    <div className="flex items-center gap-2 rounded-lg bg-bg-elevated p-2.5 border border-border-secondary">
                      <input
                        autoFocus
                        value={editingTitle}
                        onChange={(e) => setEditingTitle(e.target.value)}
                        onKeyDown={(e) => handleKeyDown(e, chat.id)}
                        onBlur={() => handleSaveEdit(chat.id)}
                        className="flex-1 bg-transparent text-sm text-text-primary outline-none font-medium"
                        placeholder="Chat title..."
                      />
                    </div>
                  ) : (
                    // Display mode
                    <div
                      onClick={() => switchChat(chat.id)}
                      className={cn(
                        "w-full text-left rounded-lg px-3 py-2.5 transition-all duration-200 relative group cursor-pointer",
                        currentChatId === chat.id
                          ? "bg-gradient-to-r from-cyan-600/20 to-blue-600/20 border border-cyan-500/30 shadow-lg shadow-cyan-500/10"
                          : "hover:bg-bg-elevated border border-transparent",
                      )}
                    >
                      <div className="flex items-center justify-between gap-2">
                        <div className="flex min-w-0 flex-1 items-center gap-2">
                          <div
                            className={cn(
                              "h-4 w-4 rounded flex items-center justify-center flex-shrink-0 transition-all duration-200",
                              currentChatId === chat.id
                                ? "bg-cyan-500/30 text-cyan-400"
                                : "bg-bg-elevated text-text-tertiary group-hover:bg-bg-elevated",
                            )}
                          >
                            <MessageSquare className="h-3 w-3" />
                          </div>
                          <p
                            className={cn(
                              "truncate font-semibold text-[12.5px] leading-4 tracking-tight transition-colors duration-200",
                              currentChatId === chat.id
                                ? "text-cyan-300"
                                : "text-text-secondary group-hover:text-text-primary",
                            )}
                            title={chat.title}
                          >
                            {chat.title}
                          </p>
                        </div>
                        <p
                          className="text-[10px] text-text-dim"
                          suppressHydrationWarning
                        >
                          {formatDate(chat.updatedAt)}
                        </p>

                        {/* Actions button */}
                        <div className="relative">
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              setMenuOpen(
                                menuOpen === chat.id ? null : chat.id,
                              );
                            }}
                            className="rounded-md p-1.5 hover:bg-bg-elevated text-text-dim hover:text-text-secondary opacity-0 group-hover:opacity-100 transition-all duration-200"
                          >
                            <MoreVertical className="h-4 w-4" />
                          </button>

                          {/* Menu */}
                          <AnimatePresence>
                            {menuOpen === chat.id && (
                              <motion.div
                                initial={{ opacity: 0, scale: 0.95, y: -10 }}
                                animate={{ opacity: 1, scale: 1, y: 0 }}
                                exit={{ opacity: 0, scale: 0.95, y: -10 }}
                                transition={{ duration: 0.15 }}
                                className="absolute right-0 top-full mt-2 z-50 rounded-lg bg-gray-900/95 backdrop-blur-md border border-border-primary shadow-xl overflow-hidden min-w-[140px]"
                              >
                                <button
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    handleStartEdit(chat);
                                  }}
                                  className="flex w-full items-center gap-2 px-3 py-2 text-sm text-text-secondary hover:bg-bg-tertiary transition-colors"
                                >
                                  <Edit2 className="h-3.5 w-3.5" />
                                  Rename
                                </button>
                                <button
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    setConfirmDelete(chat.id);
                                  }}
                                  className="flex w-full items-center gap-2 px-3 py-2 text-sm text-red-400 hover:bg-red-500/10 transition-colors border-t border-border-secondary"
                                >
                                  <Trash2 className="h-3.5 w-3.5" />
                                  Delete
                                </button>
                              </motion.div>
                            )}
                          </AnimatePresence>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Delete confirmation */}
                  <AnimatePresence>
                    {confirmDelete === chat.id && (
                      <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        className="absolute inset-0 rounded-lg bg-black/80 backdrop-blur-sm flex items-center justify-center gap-2 p-2 z-50"
                        onClick={(e) => e.stopPropagation()}
                      >
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleDelete(chat.id);
                          }}
                          className="text-xs px-3 py-1.5 rounded-md bg-red-600 text-white hover:bg-red-500 transition-colors font-medium"
                        >
                          Delete
                        </button>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            setConfirmDelete(null);
                          }}
                          className="text-xs px-3 py-1.5 rounded-md bg-gray-600 text-white hover:bg-gray-500 transition-colors font-medium"
                        >
                          Cancel
                        </button>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </motion.div>
              ))}
            </AnimatePresence>
          )}
        </div>
      </div>

      {/* Footer info */}
      <div className="border-t border-border-primary bg-gradient-to-t from-bg-primary to-transparent p-3">
        <p className="text-[11px] text-text-dim font-medium">
          {chatList.length} {chatList.length === 1 ? "chat" : "chats"}
        </p>
      </div>
    </div>
  );
}
