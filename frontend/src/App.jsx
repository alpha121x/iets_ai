import { useEffect, useState } from 'react'
import './App.css'

const API = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000/api'

function App() {
  const [token, setToken] = useState(localStorage.getItem('ai_coach_token'))
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [fullName, setFullName] = useState('')
  const [mode, setMode] = useState('login')
  const [profile, setProfile] = useState(null)
  const [matches, setMatches] = useState([])
  const [error, setError] = useState('')

  const request = async (path, options = {}) => {
    const response = await fetch(`${API}${path}`, { ...options, headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json', ...options.headers } })
    if (!response.ok) throw new Error((await response.json()).detail || 'Request failed')
    return response.json()
  }
  const load = async () => {
    try { const [me, results] = await Promise.all([request('/profile/me'), request('/universities/recommendations')]); setProfile(me); setMatches(results); setError('') } catch (e) { setError(e.message) }
  }
  useEffect(() => { if (token) load() }, [token])
  const login = async (event) => {
    event.preventDefault(); setError('')
    try { const register = mode === 'register'; const r = await fetch(`${API}/auth/${register ? 'register' : 'login'}`, register ? { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({email,password,full_name:fullName}) } : { method:'POST', headers:{'Content-Type':'application/x-www-form-urlencoded'}, body:new URLSearchParams({username:email,password}) }); const data = await r.json(); if (!r.ok) throw new Error(data.detail); localStorage.setItem('ai_coach_token', data.access_token); setToken(data.access_token) } catch (e) { setError(e.message) }
  }
  if (!token) return <main className="login"><p className="kicker">AI COACH</p><h1>Your international study pathway</h1><p>Upload your transcript, find verified opportunities, and prepare for the required tests.</p><div className="tabs"><button className={mode==='login'?'active':''} onClick={()=>setMode('login')}>Log in</button><button className={mode==='register'?'active':''} onClick={()=>setMode('register')}>Create account</button></div><form onSubmit={login}>{mode==='register'&&<input placeholder="Full name" onChange={e=>setFullName(e.target.value)} required/>}<input placeholder="Email" type="email" onChange={e=>setEmail(e.target.value)} required/><input placeholder="Password (minimum 8 characters)" type="password" minLength="8" maxLength="72" onChange={e=>setPassword(e.target.value)} required/><button>{mode==='register'?'Create account':'Log in'}</button></form><p className="error">{error}</p></main>
  return <main>
    <header><div><b>AI Coach</b><span>Transcript · Opportunities · Test Prep</span></div><button className="ghost" onClick={()=>{localStorage.removeItem('ai_coach_token');setToken(null)}}>Log out</button></header>
    <section className="hero"><p className="kicker">STUDENT OPPORTUNITY DASHBOARD</p><h1>Welcome, {profile?.full_name || 'Student'}</h1><p>Recommendations use your transcript, IELTS results and academic profile. Always verify official requirements before applying.</p></section>
    <section className="actions"><article><h2>1. Transcript</h2><p>Upload and confirm CGPA, degree and subjects.</p><a href="http://127.0.0.1:8000/docs" target="_blank">Upload transcript API →</a></article><article><h2>2. Test preparation</h2><p>Prepare for IELTS and programme-specific tests with the AI coach.</p><a href="http://127.0.0.1:8000/docs" target="_blank">Open coach APIs →</a></article><article><h2>3. Verified sources</h2><p>Every opportunity includes its official source and verification date.</p></article></section>
    <section><div className="section-title"><div><p className="kicker">MATCHED PROGRAMMES</p><h2>Universities, tests & scholarships</h2></div><button onClick={load}>Refresh</button></div>{error && <p className="error">{error}</p>}<div className="cards">{matches.map(match=><article className="card" key={match.program_id}><div className="match"><span>{match.status}</span><b>{match.match_percentage}% match</b></div><h3>{match.university}</h3><p>{match.program} · {match.country}</p><dl><dt>IELTS</dt><dd>{match.min_ielts ?? 'Check source'}</dd><dt>CGPA</dt><dd>{match.min_cgpa ?? 'Check source'}</dd><dt>Tests</dt><dd>{match.tests?.map(t=>`${t.name}: ${t.minimum_score}`).join(', ') || 'Check official source'}</dd><dt>Scholarships</dt><dd>{match.scholarships?.map(s=>s.name).join(', ') || 'Check university website'}</dd></dl><p className="reason">{match.reasons?.join(' · ') || 'Your profile meets the stored requirements.'}</p><a href={match.source_url || match.website} target="_blank">Official source →</a><small>Last verified: {match.last_verified_at ? new Date(match.last_verified_at).toLocaleDateString() : 'Needs verification'}</small></article>)}</div>{!matches.length && <p>No matches yet. Complete your target country, field, CGPA and IELTS score in the profile.</p>}</section>
  </main>
}
export default App
