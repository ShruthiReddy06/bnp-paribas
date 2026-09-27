import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../auth/useAuth.js'
import { defaultRouteForRole } from '../utils/roleRoutes.js'

export default function LoginPage() {
  const { login, register } = useAuth()
  const navigate = useNavigate()
  const [mode, setMode] = useState('signin')
  const [isAdminAccess, setIsAdminAccess] = useState(false)
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [role, setRole] = useState('candidate')
  const [error, setError] = useState('')

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')
    try {
      const data = mode === 'signin'
        ? await login(username, password, isAdminAccess ? 'admin' : 'standard')
        : await register(username, password, role)
      navigate(defaultRouteForRole(data.role))
    } catch (err) {
      setError(err.message)
    }
  }

  return (
    <main className="login-shell">
      <section className="login-intro" aria-label="SmartHire overview">
        <div className="brand-mark">S<span>H</span></div>
        <p className="eyebrow">SmartHire / Talent operations</p>
        <h1>Make every interview count.</h1>
        <p className="intro-copy">
          One calm workspace for candidate progress, interviewer decisions, and
          the people moving your team forward.
        </p>
        <div className="intro-detail">
          <span className="detail-dot" />
          <span>Private workspace · Secure access</span>
        </div>
      </section>

      <section className="login-panel">
        <div className="panel-heading">
          <p className="eyebrow">{isAdminAccess ? 'Restricted access' : 'Your talent workspace'}</p>
          <h2>{isAdminAccess ? 'Admin sign in' : mode === 'signin' ? 'Sign in to SmartHire' : 'Create your account'}</h2>
          <p>{isAdminAccess ? 'Enter the unique administrator credentials to continue.' : mode === 'signin' ? 'Use your work account to continue.' : 'Join your hiring workspace in a few seconds.'}</p>
        </div>
        {!isAdminAccess && <div className="auth-switch" role="tablist" aria-label="Account access">
          <button
            className={mode === 'signin' ? 'active' : ''}
            type="button"
            role="tab"
            aria-selected={mode === 'signin'}
            onClick={() => { setMode('signin'); setIsAdminAccess(false); setError('') }}
          >
            Sign in
          </button>
          <button
            className={mode === 'signup' ? 'active' : ''}
            type="button"
            role="tab"
            aria-selected={mode === 'signup'}
            onClick={() => { setMode('signup'); setIsAdminAccess(false); setError('') }}
          >
            Sign up
          </button>
        </div>}
        <form onSubmit={handleSubmit}>
          <div className="field-group">
            <label htmlFor="username">Username</label>
            <input
              id="username"
              autoComplete="username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder={isAdminAccess ? 'Administrator username' : 'e.g. alex.morgan'}
              required
            />
          </div>
          <div className="field-group">
            <label htmlFor="password">Password</label>
            <input
              id="password"
              type="password"
              autoComplete={mode === 'signin' ? 'current-password' : 'new-password'}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Enter your password"
              required
            />
          </div>
          {mode === 'signup' && (
            <div className="field-group">
              <label htmlFor="role">I am joining as</label>
              <select id="role" value={role} onChange={(e) => setRole(e.target.value)}>
                <option value="candidate">Candidate</option>
                <option value="interviewer">Interviewer</option>
              </select>
            </div>
          )}
          <button className="login-button" type="submit">
            {mode === 'signin' ? 'Continue' : 'Create account'} <span aria-hidden="true">-&gt;</span>
          </button>
        </form>
        {error && <p className="error" role="alert">{error}</p>}
        <p className="panel-footer">
          {isAdminAccess ? 'Not an administrator? ' : 'Are you an administrator? '}
          <button className="access-link" type="button" onClick={() => { setIsAdminAccess(!isAdminAccess); setMode('signin'); setError(''); setUsername(''); setPassword('') }}>
            {isAdminAccess ? 'Back to candidate access' : 'Admin access'}
          </button>
        </p>
      </section>
    </main>
  )
}
