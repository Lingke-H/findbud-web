import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import OnboardingPage from './pages/OnboardingPage'
import PreQuestionPage from './pages/PreQuestionPage'
import AIQuestionPage from './pages/AIQuestionPage'
import MatchResultPage from './pages/MatchResultPage'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Navigate to="/onboarding" replace />} />
        <Route path="/onboarding" element={<OnboardingPage />} />
        <Route path="/question" element={<PreQuestionPage />} />
        <Route path="/ai-question" element={<AIQuestionPage />} />
        <Route path="/result" element={<MatchResultPage />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
