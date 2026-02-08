import { useState } from 'react';
import ScrapePanel from './components/ScrapePanel';
import ArticleList from './components/ArticleList';
import RagPanel from './components/RagPanel';
import PipelinePanel from './components/PipelinePanel';
import './App.css';

function App() {
  const [activeTab, setActiveTab] = useState<'pipeline' | 'scrape' | 'articles' | 'ask'>('pipeline');

  return (
    <div className="app">
      <header>
        <h1>📰 Tigrinya News Scraper</h1>
        <nav>
          <button
            className={activeTab === 'pipeline' ? 'active' : ''}
            onClick={() => setActiveTab('pipeline')}
          >
            Pipeline
          </button>
          <button
            className={activeTab === 'scrape' ? 'active' : ''}
            onClick={() => setActiveTab('scrape')}
          >
            Scrape
          </button>
          <button
            className={activeTab === 'articles' ? 'active' : ''}
            onClick={() => setActiveTab('articles')}
          >
            Articles
          </button>
          <button
            className={activeTab === 'ask' ? 'active' : ''}
            onClick={() => setActiveTab('ask')}
          >
            Ask (RAG)
          </button>
        </nav>
      </header>
      <main>
        {activeTab === 'pipeline' && <PipelinePanel />}
        {activeTab === 'scrape' && <ScrapePanel />}
        {activeTab === 'articles' && <ArticleList />}
        {activeTab === 'ask' && <RagPanel />}
      </main>
    </div>
  );
}

export default App;
