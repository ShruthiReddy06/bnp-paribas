import { useEffect, useState } from 'react'
import { useAuth } from '../../auth/useAuth.js'
import { getAssignedCandidates, saveInterviewDecision, scheduleInterview } from '../../api/interviewer.js'

const DECISIONS = ['Accepted', 'Rejected', 'On-Hold']

export default function AssignedCandidatesPage() {
  const { auth } = useAuth()
  const [candidates, setCandidates] = useState([])
  const [error, setError] = useState('')

  function loadCandidates() {
    getAssignedCandidates(auth.token).then(setCandidates).catch((err) => setError(err.message))
  }

  useEffect(() => { loadCandidates() }, [auth.token])

  async function handleSchedule(candidate, value) {
    if (!value) return
    try {
      await scheduleInterview(auth.token, candidate.application_id, value)
      loadCandidates()
    } catch (err) { setError(err.message) }
  }

  async function handleDecision(candidate, event) {
    try { await saveInterviewDecision(auth.token, candidate.interview_id, event.target.value, candidate.feedback || ''); loadCandidates() } catch (err) { setError(err.message) }
  }

  async function handleFeedback(candidate) {
    try { await saveInterviewDecision(auth.token, candidate.interview_id, candidate.decision || 'On-Hold', candidate.feedback || ''); loadCandidates() } catch (err) { setError(err.message) }
  }

  return (
    <main className="dashboard-section interviewer-page">
      <header className="role-page-header"><div><p className="eyebrow">Interviewer workspace</p><h2>Interview pipeline</h2><p>Schedule, assess, and make decisions on candidates who cleared the test.</p></div></header>
      {error && <p className="error">{error}</p>}
      {candidates.length === 0 && <p className="empty-state">Candidates who pass the assessment will appear here.</p>}
      <div className="interview-list">{candidates.map((candidate) => <article className="interview-card" key={candidate.application_id}><div className="interview-card-header"><div><p className="job-type">{candidate.job_title}</p><h3>{candidate.candidate_username}</h3><span>Resume score {candidate.resume_score}/100</span></div><StatusBadge status={candidate.decision || 'Interview'} /></div><div className="interview-controls"><label>Interview time<input type="datetime-local" value={candidate.scheduled_at || ''} onChange={(event) => handleSchedule(candidate, event.target.value)} /></label><span className="timeline-state">{candidate.scheduled_at ? candidate.candidate_confirmed ? 'Candidate confirmed' : 'Waiting for candidate' : 'Not scheduled'}</span></div>{candidate.interview_id && <div className="feedback-controls"><label>Decision<select value={candidate.decision || ''} onChange={(event) => handleDecision({ ...candidate, decision: event.target.value }, event)}><option value="">Choose decision</option>{DECISIONS.map((decision) => <option key={decision}>{decision}</option>)}</select></label><label className="feedback-field">Feedback<textarea rows="3" value={candidate.feedback || ''} onChange={(event) => setCandidates((current) => current.map((row) => row.application_id === candidate.application_id ? { ...row, feedback: event.target.value } : row))} placeholder="Write interview feedback" /></label><button className="submit-test-button" type="button" onClick={() => handleFeedback(candidate)}>Save feedback</button></div>}</article>)}</div>
    </main>
  )
}
