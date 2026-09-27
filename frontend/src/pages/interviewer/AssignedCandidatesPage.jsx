import { useEffect, useState } from 'react'
import { useAuth } from '../../auth/useAuth.js'
import { getAssignedCandidates, saveInterviewDecision, scheduleInterview } from '../../api/interviewer.js'
import StatusBadge from '../../components/StatusBadge.jsx'

const DECISIONS = ['Accepted', 'Rejected']

export default function AssignedCandidatesPage() {
  const { auth } = useAuth()
  const [candidates, setCandidates] = useState([])
  const [error, setError] = useState('')

  function loadCandidates() {
    return getAssignedCandidates(auth.token)
      .then((rows) => {
        setCandidates(rows)
        setError('')
      })
      .catch((err) => setError(err.message))
  }

  useEffect(() => {
    let isActive = true
    const refreshAssignments = () => {
      if (document.activeElement?.matches('input, select, textarea')) return
      getAssignedCandidates(auth.token)
        .then((rows) => {
          if (isActive) {
            setCandidates(rows)
            setError('')
          }
        })
        .catch((err) => { if (isActive) setError(err.message) })
    }
    refreshAssignments()
    const intervalId = window.setInterval(refreshAssignments, 10000)
    window.addEventListener('focus', refreshAssignments)
    return () => {
      isActive = false
      window.clearInterval(intervalId)
      window.removeEventListener('focus', refreshAssignments)
    }
  }, [auth.token])

  function updateCandidate(applicationId, changes) {
    setCandidates((current) => current.map((candidate) => candidate.application_id === applicationId ? { ...candidate, ...changes } : candidate))
  }

  async function handleSchedule(candidate) {
    if (!candidate.scheduled_at) return
    try {
      setError('')
      await scheduleInterview(auth.token, candidate.application_id, candidate.scheduled_at)
      loadCandidates()
    } catch (err) { setError(err.message) }
  }

  async function handleReview(candidate) {
    if (!candidate.decision) return
    try {
      setError('')
      await saveInterviewDecision(auth.token, candidate.interview_id, candidate.decision, candidate.feedback || '')
      loadCandidates()
    } catch (err) { setError(err.message) }
  }

  return (
    <main className="dashboard-section interviewer-page">
      <header className="role-page-header"><div><p className="eyebrow">Interviewer workspace</p><h2>Interview pipeline</h2><p>Schedule, assess, and make decisions on candidates who cleared the test.</p></div><button className="table-action" type="button" onClick={loadCandidates}>Refresh assignments</button></header>
      {error && <p className="error">{error}</p>}
      {candidates.length === 0 && <p className="empty-state">No candidates are assigned to <strong>{auth.username}</strong>. Ask the admin to assign the candidate to this exact interviewer account.</p>}
      <div className="interview-list">{candidates.map((candidate) => <article className="interview-card" key={candidate.application_id}><div className="interview-card-header"><div><p className="job-type">{candidate.job_title}</p><h3>{candidate.candidate_username}</h3><span>Resume score {candidate.resume_score}/100</span></div><StatusBadge status={candidate.decision || (candidate.scheduled_at ? 'Scheduled' : 'Interview')} /></div><div className="interview-controls"><label>Interview time<input type="datetime-local" value={candidate.scheduled_at || ''} onChange={(event) => updateCandidate(candidate.application_id, { scheduled_at: event.target.value })} /></label><span className="timeline-state">{candidate.scheduled_at ? candidate.candidate_confirmed ? 'Candidate confirmed' : 'Waiting for candidate' : 'Not scheduled'}</span><button className="table-action" type="button" disabled={!candidate.scheduled_at} onClick={() => handleSchedule(candidate)}>{candidate.scheduled_at ? 'Save schedule' : 'Schedule interview'}</button></div><div className="feedback-controls"><label>Review<select value={candidate.decision || ''} onChange={(event) => updateCandidate(candidate.application_id, { decision: event.target.value })}><option value="">Choose outcome</option>{DECISIONS.map((decision) => <option key={decision}>{decision}</option>)}</select></label><label className="feedback-field">Feedback<textarea rows="3" value={candidate.feedback || ''} onChange={(event) => updateCandidate(candidate.application_id, { feedback: event.target.value })} placeholder="Write interview feedback" /></label><button className="submit-test-button" type="button" disabled={!candidate.scheduled_at || !candidate.decision} onClick={() => handleReview(candidate)}>Save review</button></div></article>)}</div>
    </main>
  )
}
