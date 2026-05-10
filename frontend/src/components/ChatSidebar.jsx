import { useEffect, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Plus, MessageSquare, Trash2, Clock, X } from 'lucide-react'
import { useAuth } from '../contexts/AuthContext'
import { watchSessions, deleteSession, MAX_SESSIONS_PER_USER } from '../firebase'

export default function ChatSidebar({
  activeSessionId,
  onSelectSession,
  onNewChat,
  open,
  onClose,
}) {
  const { user, isAuthed } = useAuth()
  const [sessions, setSessions] = useState([])

  useEffect(() => {
    if (!user) {
      setSessions([])
      return
    }
    const unsub = watchSessions(user.uid, setSessions)
    return unsub
  }, [user])

  async function handleDelete(e, sid) {
    e.stopPropagation()
    if (!user) return
    if (!confirm('Bu sohbeti silmek istiyor musun?')) return
    if (activeSessionId === sid) onSelectSession(null)
    await deleteSession(user.uid, sid)
  }

  function formatDate(ts) {
    if (!ts) return ''
    const d = ts.toDate ? ts.toDate() : new Date(ts)
    const now = new Date()
    const diff = (now - d) / 1000
    if (diff < 60) return 'şimdi'
    if (diff < 3600) return `${Math.floor(diff / 60)} dk önce`
    if (diff < 86400) return `${Math.floor(diff / 3600)} saat önce`
    if (diff < 86400 * 7) return `${Math.floor(diff / 86400)} gün önce`
    return d.toLocaleDateString('tr-TR')
  }

  if (!isAuthed) {
    return (
      <aside className="hidden lg:flex flex-col w-72 shrink-0 card mr-4 self-start sticky top-24">
        <div className="p-4 text-center">
          <MessageSquare size={28} className="mx-auto text-slate-600 mb-2" />
          <p className="text-sm text-slate-400">
            Sohbetlerini kaydetmek için giriş yap
          </p>
        </div>
      </aside>
    )
  }

  // Mobile + desktop layout
  return (
    <>
      {/* Backdrop (mobile) */}
      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="lg:hidden fixed inset-0 bg-black/60 z-40"
          />
        )}
      </AnimatePresence>

      <aside
        className={`
          card p-3 self-start
          lg:flex lg:flex-col lg:w-72 lg:shrink-0 lg:mr-4 lg:sticky lg:top-24
          ${open
            ? 'fixed top-20 bottom-4 left-4 right-20 z-50 flex flex-col overflow-y-auto'
            : 'hidden lg:flex'
          }
        `}
      >
        <div className="flex items-center justify-between mb-3">
          <h3 className="font-display font-semibold text-white text-sm flex items-center gap-2">
            <MessageSquare size={14} className="text-accent-400" />
            Sohbet Geçmişin
          </h3>
          <button
            onClick={onClose}
            className="lg:hidden text-slate-500 hover:text-white"
          >
            <X size={16} />
          </button>
        </div>

        <button
          onClick={onNewChat}
          className="btn-primary w-full mb-3 inline-flex items-center justify-center gap-2 text-sm py-2"
        >
          <Plus size={14} />
          Yeni Sohbet
        </button>

        <div className="text-[10px] text-slate-500 mb-3 text-center">
          {sessions.length}/{MAX_SESSIONS_PER_USER} sohbet
          {sessions.length >= MAX_SESSIONS_PER_USER && (
            <span className="text-amber-400 ml-1">(en eskisi silinir)</span>
          )}
        </div>

        <div className="flex-1 overflow-y-auto space-y-1">
          <AnimatePresence>
            {sessions.length === 0 ? (
              <div className="text-center text-xs text-slate-500 py-8">
                Henüz sohbet yok.<br />
                "Yeni Sohbet" ile başla.
              </div>
            ) : (
              sessions.map((s) => {
                const active = s.id === activeSessionId
                return (
                  <motion.button
                    key={s.id}
                    layout
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0, x: -10 }}
                    onClick={() => onSelectSession(s.id)}
                    className={`
                      w-full text-left p-3 rounded-xl transition-all group relative
                      ${active
                        ? 'bg-gradient-to-r from-brand-500/20 to-accent-500/20 border border-accent-500/30'
                        : 'hover:bg-white/5 border border-transparent'
                      }
                    `}
                  >
                    <div className="text-sm text-slate-200 line-clamp-2 leading-snug pr-5">
                      {s.title || 'Yeni Sohbet'}
                    </div>
                    <div className="flex items-center gap-2 mt-1 text-[10px] text-slate-500">
                      <Clock size={9} />
                      {formatDate(s.updatedAt)}
                      {s.messageCount > 0 && <span>· {s.messageCount} mesaj</span>}
                    </div>
                    <button
                      onClick={(e) => handleDelete(e, s.id)}
                      className="absolute top-2 right-2 p-1 text-slate-500 hover:text-rose-400 opacity-0 group-hover:opacity-100 transition"
                      title="Sohbeti sil"
                    >
                      <Trash2 size={12} />
                    </button>
                  </motion.button>
                )
              })
            )}
          </AnimatePresence>
        </div>
      </aside>
    </>
  )
}
