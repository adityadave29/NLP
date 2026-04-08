import { useState } from 'react'
import './App.css'

function App() {
  const [jdFile, setJdFile] = useState(null)
  const [resumeFiles, setResumeFiles] = useState([])
  const [loading, setLoading] = useState(false)
  const [results, setResults] = useState([])
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  
  // Dynamic weightage configuration
  const [weightage, setWeightage] = useState({
    skillMatching: 30,
    semanticSimilarity: 20,
    experience: 20,
    education: 10,
    projects: 5,
    certifications: 5,
    domainMatch: 5,
    locationPreference: 5,
    technicalSkillsCount: 5
  })

  const handleJdUpload = (e) => {
    const file = e.target.files[0]
    if (file && (file.type === 'application/pdf' || file.name.endsWith('.docx'))) {
      setJdFile(file)
      setError('')
    } else {
      setError('Please upload a valid PDF or DOCX file for JD')
    }
  }

  const handleResumeUpload = (e) => {
    const files = Array.from(e.target.files)
    const validFiles = files.filter(file => 
      file.type === 'application/pdf' || file.name.endsWith('.docx')
    )
    
    if (validFiles.length > 0) {
      setResumeFiles(validFiles)
      setError('')
    } else {
      setError('Please upload valid PDF or DOCX files for resumes')
    }
  }

  const handleWeightageChange = (component, value) => {
    const newValue = Math.max(0, Math.min(100, parseInt(value) || 0))
    setWeightage(prev => ({
      ...prev,
      [component]: newValue
    }))
  }

  const validateWeightage = () => {
    const total = weightage.skillMatching + weightage.semanticSimilarity + weightage.experience + weightage.education + weightage.projects + weightage.certifications + weightage.domainMatch + weightage.locationPreference + weightage.technicalSkillsCount
    if (total !== 100) {
      setError(`Weightage must sum to 100%. Current total: ${total}%`)
      return false
    }
    setError('')
    return true
  }

  const handleRunAnalysis = async () => {
    if (!jdFile) {
      setError('Please upload a Job Description file')
      return
    }
    
    if (resumeFiles.length === 0) {
      setError('Please upload resume files')
      return
    }

    if (!validateWeightage()) {
      return
    }

    setLoading(true)
    setError('')
    setSuccess('')
    setResults([])

    try {
      // Upload JD
      const jdFormData = new FormData()
      jdFormData.append('file', jdFile)
      
      const jdResponse = await fetch('http://localhost:5001/upload_jd', {
        method: 'POST',
        body: jdFormData
      })

      if (!jdResponse.ok) {
        throw new Error('Failed to upload JD')
      }

      // Upload Resumes
      const resumeFormData = new FormData()
      resumeFiles.forEach(file => {
        resumeFormData.append('files', file)
      })
      
      const resumeResponse = await fetch('http://localhost:5001/upload_resumes', {
        method: 'POST',
        body: resumeFormData
      })

      if (!resumeResponse.ok) {
        throw new Error('Failed to upload resumes')
      }

      // Analyze resumes with custom weightage
      const analyzeResponse = await fetch('http://localhost:5001/analyze_resumes', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          weightage: {
            skillMatching: weightage.skillMatching,
            semanticSimilarity: weightage.semanticSimilarity,
            experience: weightage.experience,
            education: weightage.education,
            projects: weightage.projects,
            certifications: weightage.certifications,
            domainMatch: weightage.domainMatch,
            locationPreference: weightage.locationPreference,
            technicalSkillsCount: weightage.technicalSkillsCount
          }
        })
      })

      if (!analyzeResponse.ok) {
        throw new Error('Failed to analyze resumes')
      }

      const data = await analyzeResponse.json()
      
      // Recalculate final scores with custom weightage
      const recalculatedResults = data.results.map(result => {
        const skillWeight = weightage.skillMatching / 100
        const semanticWeight = weightage.semanticSimilarity / 100
        const experienceWeight = weightage.experience / 100
        
        const newFinalScore = (skillWeight * result.skill_matching_score + 
                            semanticWeight * result.semantic_similarity + 
                            experienceWeight * result.experience_score)
        
        return {
          ...result,
          final_score: round(newFinalScore, 3)
        }
      })

      setResults(recalculatedResults)
      setSuccess(`Successfully analyzed ${data.total_resumes} resumes with custom weightage`)

    } catch (err) {
      setError(err.message || 'An error occurred during analysis')
    } finally {
      setLoading(false)
    }
  }

  const getScoreClass = (score) => {
    if (score >= 0.7) return 'score-high'
    if (score >= 0.5) return 'score-medium'
    return 'score-low'
  }

  const getRankClass = (rank) => {
    if (rank === 1) return 'rank-badge rank-1'
    if (rank === 2) return 'rank-badge rank-2'
    if (rank === 3) return 'rank-badge rank-3'
    return 'rank-badge'
  }

  const totalWeightage = weightage.skillMatching + weightage.semanticSimilarity + weightage.experience + weightage.education + weightage.projects + weightage.certifications + weightage.domainMatch + weightage.locationPreference + weightage.technicalSkillsCount

  return (
    <div className="app">
      <header className="header">
        <h1>AI-Based Resume Shortlisting</h1>
        <p>Advanced AI-powered candidate ranking system for academic recruitment</p>
      </header>

      <main className="main">
        {error && <div className="error-message">⚠️ {error}</div>}
        {success && <div className="success-message">✅ {success}</div>}

        {/* Weightage Configuration */}
        <div className="upload-box" style={{marginBottom: '2rem'}}>
          <h3>⚖️ Scoring Weightage Configuration</h3>
          <div className="weightage-config">
            <div className="weightage-item">
              <label htmlFor="skill-matching">Skill Matching (%)</label>
              <input
                type="number"
                id="skill-matching"
                min="0"
                max="100"
                value={weightage.skillMatching}
                onChange={(e) => handleWeightageChange('skillMatching', e.target.value)}
                className="weightage-input"
              />
            </div>
            <div className="weightage-item">
              <label htmlFor="semantic-similarity">Semantic Similarity (%)</label>
              <input
                type="number"
                id="semantic-similarity"
                min="0"
                max="100"
                value={weightage.semanticSimilarity}
                onChange={(e) => handleWeightageChange('semanticSimilarity', e.target.value)}
                className="weightage-input"
              />
            </div>
            <div className="weightage-item">
              <label htmlFor="experience">Experience (%)</label>
              <input
                type="number"
                id="experience"
                min="0"
                max="100"
                value={weightage.experience}
                onChange={(e) => handleWeightageChange('experience', e.target.value)}
                className="weightage-input"
              />
            </div>
            <div className="weightage-item">
              <label htmlFor="education">Education (%)</label>
              <input
                type="number"
                id="education"
                min="0"
                max="100"
                value={weightage.education}
                onChange={(e) => handleWeightageChange('education', e.target.value)}
                className="weightage-input"
              />
            </div>
            <div className="weightage-item">
              <label htmlFor="projects">Projects (%)</label>
              <input
                type="number"
                id="projects"
                min="0"
                max="100"
                value={weightage.projects}
                onChange={(e) => handleWeightageChange('projects', e.target.value)}
                className="weightage-input"
              />
            </div>
            <div className="weightage-item">
              <label htmlFor="certifications">Certifications (%)</label>
              <input
                type="number"
                id="certifications"
                min="0"
                max="100"
                value={weightage.certifications}
                onChange={(e) => handleWeightageChange('certifications', e.target.value)}
                className="weightage-input"
              />
            </div>
            <div className="weightage-item">
              <label htmlFor="domainMatch">Domain Match (%)</label>
              <input
                type="number"
                id="domainMatch"
                min="0"
                max="100"
                value={weightage.domainMatch}
                onChange={(e) => handleWeightageChange('domainMatch', e.target.value)}
                className="weightage-input"
              />
            </div>
            <div className="weightage-item">
              <label htmlFor="locationPreference">Location Preference (%)</label>
              <input
                type="number"
                id="locationPreference"
                min="0"
                max="100"
                value={weightage.locationPreference}
                onChange={(e) => handleWeightageChange('locationPreference', e.target.value)}
                className="weightage-input"
              />
            </div>
            <div className="weightage-item">
              <label htmlFor="technicalSkillsCount">Technical Skills Count (%)</label>
              <input
                type="number"
                id="technicalSkillsCount"
                min="0"
                max="100"
                value={weightage.technicalSkillsCount}
                onChange={(e) => handleWeightageChange('technicalSkillsCount', e.target.value)}
                className="weightage-input"
              />
            </div>
          </div>
          <div className={`weightage-total ${totalWeightage === 100 ? 'valid' : 'invalid'}`}>
            Total Weightage: {totalWeightage}% {totalWeightage === 100 ? '✅' : '❌ Must equal 100%'}
          </div>
        </div>

        <div className="upload-section">
          <div className="upload-box">
            <h3>Job Description</h3>
            <div className="file-input-wrapper">
              <input
                type="file"
                accept=".pdf,.docx"
                onChange={handleJdUpload}
                className="file-input"
                id="jd-upload"
              />
              <label htmlFor="jd-upload" className="file-input-label">
                {jdFile ? `✓ ${jdFile.name}` : '📄 Choose JD file (PDF/DOCX)'}
              </label>
            </div>
            {jdFile && (
              <div className="selected-files">
                <p>📋 Document Ready</p>
                <ul>
                  <li>File: {jdFile.name}</li>
                  <li>Size: {(jdFile.size / 1024).toFixed(1)} KB</li>
                </ul>
              </div>
            )}
          </div>

          <div className="upload-box">
            <h3>Resume Collection</h3>
            <div className="file-input-wrapper">
              <input
                type="file"
                accept=".pdf,.docx"
                multiple
                onChange={handleResumeUpload}
                className="file-input"
                id="resumes-upload"
              />
              <label htmlFor="resumes-upload" className="file-input-label">
                {resumeFiles.length > 0 
                  ? `✓ ${resumeFiles.length} files selected` 
                  : '📁 Choose resume files (PDF/DOCX)'}
              </label>
            </div>
            {resumeFiles.length > 0 && (
              <div className="selected-files">
                <p>📊 Upload Summary</p>
                <ul>
                  <li>Total Files: {resumeFiles.length}</li>
                  <li>Total Size: {(resumeFiles.reduce((acc, file) => acc + file.size, 0) / 1024).toFixed(1)} KB</li>
                  <li>Status: Ready for analysis</li>
                </ul>
              </div>
            )}
          </div>
        </div>

        <div className="run-section">
          <button
            onClick={handleRunAnalysis}
            disabled={loading}
            className="run-button"
          >
            {loading ? '🔄 Processing...' : '🚀 Run Analysis'}
          </button>
        </div>

        {results.length > 0 && (
          <div className="results-section">
            <h2>📊 Academic Ranking Results</h2>
            <div className="weightage-summary">
              <p>Applied Weightage: Skill Matching {weightage.skillMatching}% | Semantic Similarity {weightage.semanticSimilarity}% | Experience {weightage.experience}% | Education {weightage.education}% | Projects {weightage.projects}% | Certifications {weightage.certifications}% | Domain Match {weightage.domainMatch}% | Location {weightage.locationPreference}% | Technical Skills {weightage.technicalSkillsCount}%</p>
            </div>
            <div className="table-container">
              <table className="results-table">
                <thead>
                  <tr>
                    <th>Rank</th>
                    <th>Candidate</th>
                    <th>Final Score</th>
                    <th>Skill Match</th>
                    <th>Semantic Similarity</th>
                    <th>Experience</th>
                    <th>Years</th>
                    <th>Domain</th>
                    <th>Projects</th>
                    <th>Certifications</th>
                    <th>Domain Match</th>
                    <th>Education</th>
                    <th>Location</th>
                    <th>Tech Skills</th>
                  </tr>
                </thead>
                <tbody>
                  {results.map((result, index) => (
                    <tr key={index}>
                      <td>
                        <span className={getRankClass(index + 1)}>
                          #{index + 1}
                        </span>
                      </td>
                      <td>
                        <strong>{result.filename.replace('.pdf', '').replace('.docx', '')}</strong>
                      </td>
                      <td className={getScoreClass(result.final_score)}>
                        {(result.final_score * 100).toFixed(1)}%
                      </td>
                      <td className={getScoreClass(result.skill_matching_score)}>
                        {(result.skill_matching_score * 100).toFixed(1)}%
                      </td>
                      <td className={getScoreClass(result.semantic_similarity)}>
                        {(result.semantic_similarity * 100).toFixed(1)}%
                      </td>
                      <td className={getScoreClass(result.experience_score)}>
                        {(result.experience_score * 100).toFixed(1)}%
                      </td>
                      <td>{result.experience_years} years</td>
                      <td>{result.domain.join(', ')}</td>
                      <td className={getScoreClass(result.project_score || 0)}>
                        {(result.project_score || 0 * 100).toFixed(1)}%
                      </td>
                      <td className={getScoreClass(result.certification_score || 0)}>
                        {(result.certification_score || 0 * 100).toFixed(1)}%
                      </td>
                      <td className={getScoreClass(result.domain_match_score || 0)}>
                        {(result.domain_match_score || 0 * 100).toFixed(1)}%
                      </td>
                      <td className={getScoreClass(result.education_score || 0)}>
                        {(result.education_score || 0 * 100).toFixed(1)}%
                      </td>
                      <td className={getScoreClass(result.location_score || 0)}>
                        {(result.location_score || 0 * 100).toFixed(1)}%
                      </td>
                      <td className={getScoreClass(result.tech_skills_score || 0)}>
                        {(result.tech_skills_score || 0 * 100).toFixed(1)}%
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </main>
    </div>
  )
}

export default App
