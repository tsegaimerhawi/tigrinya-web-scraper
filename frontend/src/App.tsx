import { useState } from 'react';
import ArticleList from './components/ArticleList';
import RagPanel from './components/RagPanel';
import PipelinePanel from './components/PipelinePanel';
import './App.css';

function App() {
  const [activeTab, setActiveTab] = useState<'articles' | 'ask' | 'pipeline'>('articles');

  return (
    <div className="app">
      <header>
        <h1>📰 Tigrinya News</h1>
        <nav>
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
          <button
            className={activeTab === 'pipeline' ? 'active' : ''}
            onClick={() => setActiveTab('pipeline')}
          >
            Pipeline
          </button>
        </nav>
      </header>
      <main>
        {activeTab === 'articles' && <ArticleList />}
        {activeTab === 'ask' && <RagPanel />}
        {activeTab === 'pipeline' && <PipelinePanel />}
      </main>
    </div>
  );
}

export default App;
