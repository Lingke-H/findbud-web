import { BrowserRouter, Routes, Route } from 'react-router-dom'

// 页面组件占位（xzf 逐步填充）
function Home() {
  return <div style={{ padding: 40, fontFamily: 'sans-serif' }}>
    <h1>FindBud — 找搭子</h1>
    <p>前端框架已就绪，请在 src/pages/ 目录下添加页面组件。</p>
  </div>
}

function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* 首页 */}
        <Route path="/" element={<Home />} />
        {/* 后续页面在此添加，例如：
          <Route path="/onboarding" element={<OnboardingPage />} />
          <Route path="/competition" element={<CompetitionSelectPage />} />
          <Route path="/question" element={<FixedQuestionPage />} />
          <Route path="/result" element={<MatchResultPage />} />
        */}
      </Routes>
    </BrowserRouter>
  )
}

export default App
