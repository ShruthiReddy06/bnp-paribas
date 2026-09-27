import { useEffect, useState } from 'react'
import { useAuth } from '../../auth/useAuth.js'
import { applyForJob, getApplications, getCandidateTests, getJobs, getMyApplications, startCandidateTest, submitCandidateTest } from '../../api/jobs.js'
import StatusBadge from '../../components/StatusBadge.jsx'
import { confirmInterview, getCandidateInterviews } from '../../api/interviews.js'

export default function CandidateStatusPage() {
  const { auth } = useAuth()
  const [jobs, setJobs] = useState([])
  const [appliedJobIds, setAppliedJobIds] = useState([])
  const [applications, setApplications] = useState([])
  const [tests, setTests] = useState([])
  const [interviews, setInterviews] = useState([])
  const [activeTest, setActiveTest] = useState(null)
  const [answers, setAnswers] = useState({})
  const [uploadingJobId, setUploadingJobId] = useState(null)
  const [error, setError] = useState('')
  const [testError, setTestError] = useState('')

  useEffect(() => {
    getJobs(auth.token).then(setJobs).catch((err) => setError(err.message))
    getApplications(auth.token).then(setAppliedJobIds).catch((err) => setError(err.message))
    getCandidateTests(auth.token).then(setTests).catch((err) => setTestError(err.message))
  }, [auth.token])

  useEffect(() => {
    let isActive = true
    const refreshInterviews = () => {
      Promise.all([getCandidateInterviews(auth.token), getMyApplications(auth.token)])
        .then(([interviewRows, applicationRows]) => {
          if (isActive) {
            setInterviews(interviewRows)
            setApplications(applicationRows)
          }
        })
        .catch((err) => { if (isActive) setError(err.message) })
    }
    refreshInterviews()
    const intervalId = window.setInterval(refreshInterviews, 15000)
    return () => {
      isActive = false
      window.clearInterval(intervalId)
    }
  }, [auth.token])

  async function handleApply(jobId, event) {
    const resume = event.target.files[0]
    event.target.value = ''
    if (!resume) return
    const allowedTypes = ['application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document']
    if (!allowedTypes.includes(resume.type) || resume.size > 5 * 1024 * 1024) {
      setError('Upload a PDF, DOC, or DOCX resume smaller than 5 MB.')
      return
    }
    setError('')
    setUploadingJobId(jobId)
    try {
      await applyForJob(auth.token, jobId, resume)
      setAppliedJobIds((current) => [...current, jobId])
      setApplications(await getMyApplications(auth.token))
      setInterviews(await getCandidateInterviews(auth.token))
      setTests(await getCandidateTests(auth.token))
    } catch (err) {
      setError(err.message)
    } finally {
      setUploadingJobId(null)
    }
  }

  async function handleConfirmInterview(interviewId) {
    try {
      await confirmInterview(auth.token, interviewId)
      setInterviews(await getCandidateInterviews(auth.token))
    } catch (err) { setError(err.message) }
  }

  async function handleStartTest(testId) {
    setTestError('')
    try {
      setActiveTest(await startCandidateTest(auth.token, testId))
      setAnswers({})
      setTests((current) => current.map((test) => test.id === testId ? { ...test, status: 'Started' } : test))
    } catch (err) {
      setTestError(err.message)
    }
  }

  async function handleSubmitTest() {
    if (!activeTest) return
    setTestError('')
    try {
      await submitCandidateTest(auth.token, activeTest.id, answers)
      setActiveTest(null)
      setTests(await getCandidateTests(auth.token))
      setApplications(await getMyApplications(auth.token))
    } catch (err) {
      setTestError(err.message)
    }
  }

  return (
    <main className="candidate-page">
      <header className="candidate-header">
        <div><p className="eyebrow">Candidate workspace</p><h2>Find your next opportunity.</h2><p>Explore open roles and keep track of every application in one place.</p></div>
        <span className="candidate-status"><span /> Profile active</span>
      </header>
      {error && <p className="error">{error}</p>}
      <section className="candidate-stats">
        <div className="stat-card"><span>Open roles</span><strong>{jobs.length}</strong><small>Available opportunities</small></div>
        <div className="stat-card"><span>Applications</span><strong>{applications.length}</strong><small>Roles you have applied for</small></div>
      </section>
      <section className="dashboard-section">
        <div className="section-heading"><div><p className="eyebrow">Interview timeline</p><h3>Your interviews</h3></div><span className="count-label">{interviews.filter((interview) => interview.scheduled_at).length} scheduled</span></div>
        {interviews.length === 0 && <p className="empty-state">Your interview schedule will appear after you clear the test.</p>}
        <div className="interview-list">{interviews.map((interview) => <article className="interview-card" key={interview.interview_id}><div className="interview-card-header"><div><p className="job-type">{interview.job_title}</p><h3>Interview with {interview.interviewer_username}</h3><span>{interview.scheduled_at ? new Date(interview.scheduled_at).toLocaleString() : 'Time not scheduled yet'}</span></div><StatusBadge status={interview.decision || (interview.candidate_confirmed ? 'Confirmed' : 'Awaiting confirmation')} /></div>{interview.scheduled_at && <div className="candidate-interview-notice" role="status"><strong>Interview scheduled</strong><span>{new Date(interview.scheduled_at).toLocaleString()} with {interview.interviewer_username}</span></div>}{interview.scheduled_at && !interview.candidate_confirmed && !interview.decision && <button className="submit-test-button" type="button" onClick={() => handleConfirmInterview(interview.interview_id)}>Confirm interview time</button>}{interview.feedback && <p className="interview-feedback"><strong>Interviewer feedback:</strong> {interview.feedback}</p>}</article>)}</div>
      </section>
      <section className="dashboard-section">
        <div className="section-heading"><div><p className="eyebrow">Explore opportunities</p><h3>Open job postings</h3></div><span className="count-label">{jobs.length} roles</span></div>
        <div className="job-grid">
          {jobs.map((job) => <article className="job-card" key={job.id}><p className="job-type">{job.type}</p><h3>{job.title}</h3><p>{job.description}</p><div className="job-card-footer"><span>{job.location}</span><label className={`apply-button ${appliedJobIds.includes(job.id) ? 'applied' : ''}`}><input className="resume-input" type="file" accept=".pdf,.doc,.docx" disabled={appliedJobIds.includes(job.id) || uploadingJobId === job.id} onChange={(event) => handleApply(job.id, event)} />{appliedJobIds.includes(job.id) ? 'Applied' : uploadingJobId === job.id ? 'Uploading...' : 'Apply now'}</label></div></article>)}
        </div>
      </section>
      <section className="dashboard-section">
      <div className="section-heading"><div><p className="eyebrow">Your activity</p><h3>My applications</h3></div><span className="count-label">{applications.length} submitted</span></div>
      {applications.length > 0 && <div className="application-list">{applications.map((application) => <article className="application-row" key={application.id}><div><p className="job-type">{application.type}</p><h3>{application.job_title}</h3><span>{application.location} · {application.resume_filename}</span></div><StatusBadge status={application.status} /></article>)}</div>}
      {applications.length === 0 && <p className="empty-state">Your submitted applications will appear here.</p>}
      </section>
      <section className="dashboard-section">
        <div className="section-heading"><div><p className="eyebrow">Shortlisted assessment</p><h3>Your tests</h3></div><span className="count-label">{tests.length} assigned</span></div>
        {testError && <p className="error">Assessment issue: {testError}</p>}
        {tests.length === 0 && <p className="empty-state">Your test will appear here after an administrator assigns it.</p>}
        <div className="test-list">
          {tests.map((test) => <article className="test-card" key={test.id}>
            <div className="test-card-heading"><div><p className="job-type">{test.generation_mode === 'standard' ? 'Standard assessment' : 'AI-generated assessment'}</p><h3>{test.generation_mode === 'standard' ? 'Work scenario assessment' : 'Technical screening test'}</h3><span>{test.question_count} questions</span></div><div className="test-action"><StatusBadge status={test.status} />{test.status === 'Completed' && test.application_status && <StatusBadge status={test.application_status} />}{test.status === 'Ready' && <button className="apply-button" type="button" onClick={() => handleStartTest(test.id)}>Start test</button>}{test.status !== 'Ready' && <small>Already opened</small>}</div></div>
            {activeTest?.id === test.id && <div className="question-list">
              {activeTest.questions.map((question, index) => <div className="question-block" key={question.id || index}><div className="question-meta">Question {index + 1} · {question.difficulty} · {question.marks} marks</div><h4>{question.question}</h4>{question.type === 'MCQ' && <div className="question-options">{Object.entries(question.options || {}).map(([key, option]) => <label key={key}><input type="radio" name={`question-${test.id}-${index}`} value={key} checked={answers[String(question.id)] === key} onChange={() => setAnswers((current) => ({ ...current, [String(question.id)]: key }))} /> <strong>{key}.</strong> {option}</label>)}</div>}{question.type === 'DESCRIPTIVE' && <textarea aria-label={`Answer for question ${index + 1}`} placeholder="Write your answer here..." rows="4" value={answers[String(question.id)] || ''} onChange={(event) => setAnswers((current) => ({ ...current, [String(question.id)]: event.target.value }))} />}</div>)}
              <button className="submit-test-button" type="button" onClick={handleSubmitTest}>Submit test</button>
            </div>}
          </article>)}
        </div>
      </section>
    </main>
  )
}
