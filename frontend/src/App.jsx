import { useEffect, useState } from 'react'
import './App.css'

const API = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000/api'
const demo = [
  { program_id: 1, university: 'University of Manchester', program: 'MSc Advanced Computer Science', country: 'United Kingdom', match_percentage: 92, status: 'Strong match', min_ielts: 6.5, min_cgpa: 3, scholarships: [{ name: 'Global Futures Scholarship', amount: 'Up to 10,000' }] },
  { program_id: 2, university: 'University of Dundee', program: 'MSc Computer Science', country: 'United Kingdom', match_percentage: 84, status: 'Possible match', min_ielts: 6, min_cgpa: 2.7, scholarships: [{ name: 'Global Excellence Scholarship', amount: 'Varies' }] },
]

export default function App() {
  const [t, setT] = useState(localStorage.getItem('ai_coach_token'))
  const [tab, setTab] = useState('login')
  const [form, setForm] = useState({})
  const [me, setMe] = useState()
  const [matches, setMatches] = useState([])
  const [aiSummary, setAiSummary] = useState('')
  const [msg, setMsg] = useState('')
  const [demoMode, setDemo] = useState(false)
  const [chat, setChat] = useState([])
  const [chatOpen, setChatOpen] = useState(false)
  const [thinking, setThinking] = useState(false)

  const req = async (p, o = {}) => {
    const r = await fetch(API + p, { ...o, headers: { Authorization: `Bearer ${t}`, 'Content-Type': 'application/json', ...o.headers } })
    const d = await r.json()
    if (!r.ok) throw Error(d.detail || 'Request failed')
    return d
  }

  const load = async () => {
    try {
      const [profile, recommendations] = await Promise.all([req('/profile/me'), req('/universities/recommendations')])
      setMe(profile)
      setMatches(recommendations)
      if (profile.target_country || profile.target_program || profile.cgpa) {
        const summary = await req('/universities/recommendations/ai-summary')
        setAiSummary(summary.summary)
      } else {
        setAiSummary('')
      }
    } catch (e) {
      setMsg(e.message)
    }
  }

  useEffect(() => { if (t) load() }, [t])

  const auth = async e => {
    e.preventDefault()
    try {
      const reg = tab === 'register'
      const o = reg
        ? { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ email: form.email, password: form.password, full_name: form.name }) }
        : { method: 'POST', headers: { 'Content-Type': 'application/x-www-form-urlencoded' }, body: new URLSearchParams({ username: form.email, password: form.password }) }
      const r = await fetch(API + '/auth/' + (reg ? 'register' : 'login'), o)
      const d = await r.json()
      if (!r.ok) {
        const detail = Array.isArray(d.detail) ? d.detail.map(x => x.msg).join(', ') : d.detail
        throw Error(detail || 'Request failed')
      }
      localStorage.setItem('ai_coach_token', d.access_token)
      setT(d.access_token)
    } catch (e) {
      setMsg(e.message)
    }
  }

  if (!t && !demoMode) return <main className="auth"><section><div className="logo">AC</div><p className="eyebrow">AI COACH</p><h1>Plan your future abroad with confidence.</h1><p>Transcript matching, verified university requirements, scholarships, and test preparation in one platform.</p><ul><li>Personalised university matches</li><li>Test and scholarship tracking</li><li>AI-powered study preparation</li></ul></section><form className="authcard" onSubmit={auth}><p className="eyebrow">STUDENT PORTAL</p><h2>{tab === 'login' ? 'Welcome back' : 'Create your account'}</h2><div className="tabs"><button type="button" className={tab === 'login' ? 'on' : ''} onClick={() => setTab('login')}>Log in</button><button type="button" className={tab === 'register' ? 'on' : ''} onClick={() => setTab('register')}>Register</button></div>{tab === 'register' && <input placeholder="Full name" onChange={e => setForm({ ...form, name: e.target.value })} />}<input placeholder="Email" type="email" onChange={e => setForm({ ...form, email: e.target.value })} /><input placeholder="Password" type="password" onChange={e => setForm({ ...form, password: e.target.value })} /><button className="primary">{tab === 'login' ? 'Log in' : 'Create account'} </button><button type="button" className="demo" onClick={() => setDemo(true)}>Explore client demo</button><p className="error">{msg}</p></form></main>

  const student = demoMode ? { full_name: 'Ayesha Khan', cgpa: 3.62, target_country: 'United Kingdom', target_program: 'Computer Science' } : me
  const list = demoMode ? demo : matches
  const hasProfile = Boolean(student?.target_country || student?.target_program || student?.cgpa)
  const scholarshipCount = list.reduce((total, item) => total + (item.scholarships?.length || 0), 0)
  const ieltsTarget = list.find(item => item.min_ielts)?.min_ielts
  const coachText = hasProfile || demoMode
    ? aiSummary || 'Your next recommendations will update from your saved country, field, CGPA and IELTS scores.'
    : 'Add your target country, field, CGPA and IELTS score to generate a study plan.'

  const saveProfile = async e => {
    e.preventDefault()
    try {
      await req('/profile/me', { method: 'PUT', body: JSON.stringify({ target_country: form.country || null, target_program: form.program || null, cgpa: form.cgpa ? Number(form.cgpa) : null }) })
      setMsg('Profile saved.')
      load()
    } catch (e) {
      setMsg(e.message)
    }
  }

  const score = async e => {
    e.preventDefault()
    try {
      const x = ['reading', 'listening', 'writing', 'speaking'].reduce((a, k) => ({ ...a, [k]: Number(form[k]) }), {})
      await req('/ielts/results', { method: 'POST', body: JSON.stringify(x) })
      setMsg('IELTS score saved.')
      load()
    } catch (e) {
      setMsg(e.message)
    }
  }

  const upload = async e => {
    const file = e.target.files?.[0]
    if (!file) return
    e.target.value = ''
    setMsg('Reading transcript with AI...')
    try {
      const body = new FormData()
      body.append('file', file)
      const r = await fetch(API + '/transcripts/upload', { method: 'POST', headers: { Authorization: `Bearer ${t}` }, body })
      const d = await r.json()
      if (!r.ok) throw Error(d.detail)
      if (d.detected_cgpa !== null && d.detected_cgpa !== undefined) {
        setMe(s => ({ ...s, cgpa: d.detected_cgpa }))
        setMsg(`Transcript uploaded. Detected CGPA: ${d.detected_cgpa}`)
      } else {
        setMsg(d.extraction_method === 'scanned_pdf' ? 'Transcript uploaded, but this PDF is scanned image-only. Enter CGPA manually or configure Gemini Vision OCR.' : 'Transcript uploaded, but no final CGPA was found. Please enter it in Academic profile.')
      }
    } catch (e) {
      setMsg(`Transcript upload failed: ${e.message}`)
    }
  }

  const askCoach = async question => {
    setChatOpen(true)
    setChat([...chat, { role: 'You', text: question }])
    setThinking(true)
    try {
      const reply = demoMode ? { content: 'Start with one focused goal today: practise IELTS Writing Task 2 for 30 minutes, then review coherence, vocabulary and grammar.' } : await req('/coach/chat', { method: 'POST', body: JSON.stringify({ message: question }) })
      setChat(c => [...c, { role: 'AI Coach', text: reply.content }])
    } catch (e) {
      setMsg(e.message)
    } finally {
      setThinking(false)
    }
  }

  return <main className="app"><aside><div className="sidebrand"><div className="logo">AC</div><b>AI Coach</b></div><button className="active" onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}>Overview</button><button onClick={() => document.getElementById('academic-profile')?.scrollIntoView({ behavior: 'smooth' })}>My profile</button><button onClick={() => document.getElementById('transcript-upload')?.click()}>Transcript</button><button onClick={() => document.getElementById('university-matches')?.scrollIntoView({ behavior: 'smooth' })}>University matches</button><button onClick={() => document.getElementById('ielts-score')?.scrollIntoView({ behavior: 'smooth' })}>Test preparation</button><button onClick={() => askCoach('Create my study plan')}>AI Coach</button><small>Verified-data platform<br />Requirements can change.</small><input id="transcript-upload" type="file" accept="application/pdf" hidden onChange={upload} /></aside><div className="content"><header><div><p className="eyebrow">STUDENT DASHBOARD</p><h1>Hello, {student?.full_name?.split(' ')[0] || 'Student'}.</h1></div><button className="demo" onClick={() => { if (demoMode) setDemo(false); else { localStorage.removeItem('ai_coach_token'); setT(null) } }}>{demoMode ? 'Exit demo' : 'Log out'}</button></header><section className="readiness"><div><p className="eyebrow">APPLICATION READINESS</p><h2>{hasProfile || demoMode ? "You're building your application." : 'Complete your profile to begin.'}</h2><p>{hasProfile || demoMode ? 'Upload a transcript, confirm your profile and complete test preparation.' : 'No recommendations are generated until you add your academic and target-study details.'}</p><div className="bar"><i style={{ width: hasProfile || demoMode ? '68%' : '12%' }} /></div></div><button className="primary" onClick={() => document.getElementById('academic-profile')?.scrollIntoView({ behavior: 'smooth' })}>Update profile</button></section><div className="metrics"><article><span>CGPA</span><b>{student?.cgpa ?? '-'}<em>/4.0</em></b></article><article><span>IELTS target</span><b>{ieltsTarget || '-'}</b><small>{ieltsTarget ? 'Based on matches' : 'Add target details'}</small></article><article><span>Matches</span><b>{list.length}</b><small>{list.length ? 'Verified criteria' : 'Waiting for profile'}</small></article><article><span>Scholarships</span><b>{scholarshipCount}</b><small>{scholarshipCount ? 'Available options' : 'No matches yet'}</small></article></div><div className="tools" id="academic-profile"><form onSubmit={saveProfile}><h3>Academic profile</h3><input placeholder="Country" defaultValue={student?.target_country || ''} onChange={e => setForm({ ...form, country: e.target.value })} /><input placeholder="Field of study" defaultValue={student?.target_program || ''} onChange={e => setForm({ ...form, program: e.target.value })} /><input placeholder="CGPA / 4.0" type="number" step=".01" defaultValue={student?.cgpa || ''} onChange={e => setForm({ ...form, cgpa: e.target.value })} /><button className="primary">Save profile</button></form><form id="ielts-score" onSubmit={score}><h3>Record IELTS score</h3>{['reading', 'listening', 'writing', 'speaking'].map(k => <input key={k} placeholder={k} type="number" min="0" max="9" step=".5" onChange={e => setForm({ ...form, [k]: e.target.value })} />)}<button className="primary">Save IELTS score</button></form><article><h3>AI Coach</h3><p>{coachText}</p><button className="primary" onClick={() => askCoach('Create my study plan')}>Start practice </button></article></div><div className="title"><div><p className="eyebrow">PERSONALISED OPPORTUNITIES</p><h2>Top university matches</h2></div><button onClick={load}>Refresh</button></div>{msg && <p className="notice">{msg}</p>}<section className="matches" id="university-matches">{list.length ? list.map(x => <article key={x.program_id}><div className="circle">{x.university[0]}</div><div className="mtext"><span>{x.status}</span><h3>{x.university}</h3><p>{x.program}  {x.country}</p><small>IELTS {x.min_ielts}  CGPA {x.min_cgpa}  {x.scholarships?.[0]?.name || 'Scholarship details available'}</small></div><div className="percent"><b>{x.match_percentage}%</b><small>match score</small><button>View details </button></div></article>) : <article className="empty"><div className="circle">+</div><div className="mtext"><h3>No personalised matches yet</h3><p>Save your country, field of study, CGPA and IELTS scores to generate recommendations.</p></div></article>}</section>{chatOpen && <section className="chatbox"><button type="button" className="chat-close" onClick={() => setChatOpen(false)}>Hide</button><div><p className="eyebrow">AI COACH CHAT</p><h2>Ask about IELTS, tests or your study plan</h2></div><div className="messages">{chat.length ? chat.map((m, i) => <p key={i} className={m.role === 'You' ? 'user' : ''}><b>{m.role}:</b> {m.text}</p>) : <p>Ask the AI Coach how to improve your profile or prepare for a required test.</p>}</div>{thinking && <p className="thinking"><i /> AI Coach is thinking...</p>}<form onSubmit={e => { e.preventDefault(); const q = new FormData(e.currentTarget).get('q'); if (q) { askCoach(q); e.currentTarget.reset() } }}><input name="q" placeholder="Example: Make me a 4-week IELTS Writing plan" /><button className="primary" disabled={thinking}>Send</button></form></section>}<button className="chat-launcher" onClick={() => setChatOpen(true)}>AI Coach</button></div></main>
}
