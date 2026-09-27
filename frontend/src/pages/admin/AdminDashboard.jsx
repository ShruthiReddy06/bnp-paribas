import { useEffect, useState } from 'react'
import { useAuth } from '../../auth/useAuth.js'
import { assignCandidateTest, assignInterviewer, deleteJob, deleteUser, getAdminJobs, getApplications, getCandidates, getShortlistThreshold, getUsers, updateShortlistThreshold } from '../../api/admin.js'
import DataTable from '../../components/DataTable.jsx'
import StatusBadge from '../../components/StatusBadge.jsx'
import { createJob } from '../../api/jobs.js'

const columns = [
  { key: 'name', label: 'Name' },
  { key: 'jd', label: 'JD' },
  { key: 'status', label: 'Status', render: (row) => <StatusBadge status={row.status} /> },
  { key: 'score', label: 'Score' }
]

export default function AdminDashboard() {
  const { auth } = useAuth()
  const [candidates, setCandidates] = useState([])
  const [jobs, setJobs] = useState([])
  const [users, setUsers] = useState([])
  const [applications, setApplications] = useState([])
  const [interviewerSelections, setInterviewerSelections] = useState({})
  const [assigningTestIds, setAssigningTestIds] = useState({})
  const [threshold, setThreshold] = useState(70)
  const [job, setJob] = useState({ title: '', description: '', location: '', type: 'Full-time', experience_years: 0, education: '', must_have: '', nice_to_have: '' })
  const [error, setError] = useState('')
  const [assignmentNotice, setAssignmentNotice] = useState('')

  useEffect(() => {
    Promise.all([getCandidates(auth.token), getAdminJobs(auth.token), getUsers(auth.token), getApplications(auth.token), getShortlistThreshold(auth.token)])
      .then(([candidateRows, jobRows, userRows, applicationRows, thresholdData]) => {
        setCandidates(candidateRows)
        setJobs(jobRows)
        setUsers(userRows)
        setApplications(applicationRows)
        setThreshold(thresholdData.threshold)
      })
      .catch((err) => setError(err.message))
  }, [auth.token])

  useEffect(() => {
    let isActive = true
    const refreshResults = () => {
      Promise.all([getApplications(auth.token), getCandidates(auth.token)])
        .then(([applicationRows, candidateRows]) => {
          if (isActive) {
            setApplications(applicationRows)
            setCandidates(candidateRows)
          }
        })
        .catch((err) => { if (isActive) setError(err.message) })
    }
    const intervalId = window.setInterval(refreshResults, 10000)
    window.addEventListener('focus', refreshResults)
    return () => {
      isActive = false
      window.clearInterval(intervalId)
      window.removeEventListener('focus', refreshResults)
    }
  }, [auth.token])

  async function handleCreateJob(event) {
    event.preventDefault()
    try {
      const created = await createJob(auth.token, {
        ...job,
        experience_years: Number(job.experience_years),
        must_have: job.must_have.split(',').map((item) => item.trim()).filter(Boolean),
        nice_to_have: job.nice_to_have.split(',').map((item) => item.trim()).filter(Boolean)
      })
      setJobs((current) => [created, ...current])
      setJob({ title: '', description: '', location: '', type: 'Full-time', experience_years: 0, education: '', must_have: '', nice_to_have: '' })
    } catch (err) {
      setError(err.message)
    }
  }

  async function handleThresholdUpdate(event) {
    event.preventDefault()
    try {
      const result = await updateShortlistThreshold(auth.token, Number(threshold))
      setThreshold(result.threshold)
      setApplications(await getApplications(auth.token))
      setCandidates(await getCandidates(auth.token))
    } catch (err) {
      setError(err.message)
    }
  }

  async function handleAssignInterviewer(application) {
    const interviewerUsername = interviewerSelections[application.id] || application.interviewer_username
    if (!interviewerUsername) {
      setError('Choose an interviewer before assigning this application.')
      return
    }
    try {
      setError('')
      await assignInterviewer(auth.token, application.id, interviewerUsername)
      setApplications(await getApplications(auth.token))
    } catch (err) {
      setError(err.message)
    }
  }

  async function handleAssignTest(application) {
    setAssigningTestIds((current) => ({ ...current, [application.id]: true }))
    setError('')
    setAssignmentNotice('')
    try {
      const assignedTest = await assignCandidateTest(auth.token, application.id)
      setAssignmentNotice(assignedTest.generation_mode === 'standard'
        ? 'A standard assessment was assigned because Groq is not configured.'
        : 'AI-generated assessment assigned.')
      setApplications(await getApplications(auth.token))
    } catch (err) {
      setError(err.message)
    } finally {
      setAssigningTestIds((current) => ({ ...current, [application.id]: false }))
    }
  }

  async function handleDeleteJob(jobToDelete) {
    if (!window.confirm(`Delete ${jobToDelete.title}? Any applications for this role will also be removed.`)) return
    try {
      await deleteJob(auth.token, jobToDelete.id)
      setJobs((current) => current.filter((jobRow) => jobRow.id !== jobToDelete.id))
      setApplications(await getApplications(auth.token))
    } catch (err) {
      setError(err.message)
    }
  }

  async function handleDeleteUser(userToDelete) {
    if (!window.confirm(`Delete ${userToDelete.username}? Their submitted applications will also be removed.`)) return
    try {
      await deleteUser(auth.token, userToDelete.username)
      setUsers((current) => current.filter((user) => user.username !== userToDelete.username))
      setApplications(await getApplications(auth.token))
    } catch (err) {
      setError(err.message)
    }
  }

  return (
    <main className="admin-page">
      <header className="admin-header">
        <div><p className="eyebrow">Workspace control center</p><h2>Admin dashboard</h2><p>Manage roles, people, and hiring activity from one place.</p></div>
        <span className="admin-status"><span /> System active</span>
      </header>
      {error && <p className="error">{error}</p>}
      {assignmentNotice && <p className="success" role="status">{assignmentNotice}</p>}
      <section className="admin-stats">
        <div className="stat-card"><span>Live roles</span><strong>{jobs.length}</strong><small>Available to candidates</small></div>
        <div className="stat-card"><span>Candidates</span><strong>{users.filter((user) => user.role === 'candidate').length}</strong><small>Registered accounts</small></div>
        <div className="stat-card"><span>Interviewers</span><strong>{users.filter((user) => user.role === 'interviewer').length}</strong><small>Available reviewers</small></div>
        <div className="stat-card"><span>Applications</span><strong>{applications.length}</strong><small>Submitted resumes</small></div>
      </section>
      <section className="threshold-panel">
        <div><p className="eyebrow">Screening rule</p><h3>Shortlist threshold</h3><p>Applications scoring at or above this value are shortlisted automatically.</p></div>
        <form className="threshold-form" onSubmit={handleThresholdUpdate}><label htmlFor="threshold">Minimum score</label><input id="threshold" type="number" min="0" max="100" step="0.5" value={threshold} onChange={(e) => setThreshold(e.target.value)} /><span>/ 100</span><button type="submit">Save threshold</button></form>
      </section>
      <section className="dashboard-section">
        <div className="section-heading"><div><p className="eyebrow">Open roles</p><h3>Job postings</h3></div><span className="count-label">{jobs.length} live</span></div>
        <form className="job-form" onSubmit={handleCreateJob}>
          <input aria-label="Job title" placeholder="Job title" value={job.title} onChange={(e) => setJob({ ...job, title: e.target.value })} required />
          <input aria-label="Location" placeholder="Location" value={job.location} onChange={(e) => setJob({ ...job, location: e.target.value })} required />
          <input aria-label="Job type" placeholder="Type" value={job.type} onChange={(e) => setJob({ ...job, type: e.target.value })} required />
          <input aria-label="Description" placeholder="Short description" value={job.description} onChange={(e) => setJob({ ...job, description: e.target.value })} required />
          <input aria-label="Required experience" type="number" min="0" step="0.5" placeholder="Years experience" value={job.experience_years} onChange={(e) => setJob({ ...job, experience_years: e.target.value })} />
          <input aria-label="Education" placeholder="Education" value={job.education} onChange={(e) => setJob({ ...job, education: e.target.value })} />
          <input aria-label="Required skills" className="wide-job-input" placeholder="Required skills, comma separated" value={job.must_have} onChange={(e) => setJob({ ...job, must_have: e.target.value })} />
          <input aria-label="Nice to have skills" className="wide-job-input" placeholder="Nice-to-have skills, comma separated" value={job.nice_to_have} onChange={(e) => setJob({ ...job, nice_to_have: e.target.value })} />
          <button type="submit">Post role</button>
        </form>
        <div className="table-wrap"><DataTable columns={[{ key: 'title', label: 'Role' }, { key: 'location', label: 'Location' }, { key: 'type', label: 'Type' }, { key: 'experience_years', label: 'Experience' }, { key: 'must_have', label: 'Required skills', render: (row) => row.must_have.join(', ') || 'None' }, { key: 'actions', label: '', render: (row) => <button className="table-action danger" type="button" onClick={() => handleDeleteJob(row)}>Delete</button> }]} rows={jobs} /></div>
      </section>
      <section className="dashboard-section">
        <div className="section-heading"><div><p className="eyebrow">Pipeline</p><h3>Candidates</h3></div></div>
      <div className="table-wrap"><DataTable columns={columns} rows={candidates} /></div>
      </section>
      <section className="dashboard-section split-section">
        <div>
          <div className="section-heading"><div><p className="eyebrow">Workspace directory</p><h3>Users</h3></div></div>
          <div className="table-wrap"><DataTable columns={[{ key: 'username', label: 'Username' }, { key: 'role', label: 'Role' }, { key: 'actions', label: '', render: (row) => row.role === 'admin' ? null : <button className="table-action danger" type="button" onClick={() => handleDeleteUser(row)}>Delete</button> }]} rows={users} /></div>
        </div>
        <div>
          <div className="section-heading"><div><p className="eyebrow">Review queue</p><h3>Applications</h3></div></div>
          <div className="table-wrap"><DataTable columns={[{ key: 'username', label: 'Candidate' }, { key: 'job_title', label: 'Role' }, { key: 'score', label: 'Resume score', render: (row) => row.score == null ? 'Pending' : `${row.score}/100` }, { key: 'test_status', label: 'Test performance', render: (row) => row.test_status === 'Completed' ? `${row.test_score}/100` : row.test_status || (row.status === 'Shortlisted' ? <button className="table-action" type="button" disabled={assigningTestIds[row.id]} onClick={() => handleAssignTest(row)}>{assigningTestIds[row.id] ? 'Generating...' : 'Assign test'}</button> : 'Not assigned') }, { key: 'interviewer_username', label: 'Interviewer', render: (row) => row.status !== 'Interview' ? row.interviewer_username || 'Not assigned' : row.scheduled_at ? row.interviewer_username : <div className="interviewer-assignment"><select aria-label={`Interviewer for ${row.username}`} value={interviewerSelections[row.id] ?? row.interviewer_username ?? ''} onChange={(event) => setInterviewerSelections((current) => ({ ...current, [row.id]: event.target.value }))}><option value="">Choose interviewer</option>{users.filter((user) => user.role === 'interviewer').map((user) => <option key={user.username} value={user.username}>{user.username}</option>)}</select><button className="table-action" type="button" disabled={!interviewerSelections[row.id] && !row.interviewer_username} onClick={() => handleAssignInterviewer(row)}>{row.interviewer_username ? 'Save assignment' : 'Assign'}</button></div> }, { key: 'scheduled_at', label: 'Interview time', render: (row) => row.scheduled_at ? new Date(row.scheduled_at).toLocaleString() : 'Not scheduled' }, { key: 'interview_decision', label: 'Interview decision', render: (row) => row.interview_decision ? <StatusBadge status={row.interview_decision} /> : 'Pending' }, { key: 'interview_feedback', label: 'Feedback', render: (row) => row.interview_feedback || 'Pending' }, { key: 'status', label: 'Status', render: (row) => <StatusBadge status={row.status} /> }, { key: 'resume_filename', label: 'Resume' }]} rows={applications} /></div>
        </div>
      </section>
    </main>
  )
}
