import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Home from './pages/Home';
import { FAQ, FAQsPage } from './pages/FAQ';
import Chat from './pages/Chat';
import TermSheet from './pages/TermSheet';
import { MarketingLayout } from './layouts/MarketingLayout';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/chat" element={<Chat />} />
        <Route path="/term-sheet" element={<TermSheet />} />
        <Route
          path="/faq"
          element={
            <MarketingLayout>
              <FAQ />
            </MarketingLayout>
          }
        />
        <Route
          path="/faqs"
          element={
            <MarketingLayout>
              <FAQsPage />
            </MarketingLayout>
          }
        />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;

