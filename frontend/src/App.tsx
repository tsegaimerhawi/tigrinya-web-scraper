import { useState } from 'react';
import ScrapePanel from './components/ScrapePanel';
import ArticleList from './components/ArticleList';
import './App.css';

function App() {
  const [activeTab, setActiveTab] = useState<'scrape' | 'articles'>('scrape');

  return (
    <div className="app">
      <header>
        <h1>📰 Tigrinya News Scraper</h1>
        <nav>
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
        </nav>
      </header>
      <main>
        {activeTab === 'scrape' && <ScrapePanel />}
        {activeTab === 'articles' && <ArticleList />}
      </main>
    </div>
  );
}

export default App;
