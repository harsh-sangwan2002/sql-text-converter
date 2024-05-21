import React, { useState, useEffect } from 'react';
import axios from 'axios';

const messages = [
  'Fetching data...',
  'Processing your request...',
  'Almost there...',
  'Just a moment...',
  'Loading results...'
];

const getRandomMessage = () => {
  return messages[Math.floor(Math.random() * messages.length)];
};

const QuestionForm = ({ setQueryResult }) => {
  const [question, setQuestion] = useState('');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [progress, setProgress] = useState(0);
  const [message, setMessage] = useState(getRandomMessage());

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setProgress(0);

    const interval = setInterval(() => {
      setProgress((oldProgress) => {
        const newProgress = oldProgress + 2;
        if (newProgress === 100) {
          clearInterval(interval);
        }
        return Math.min(newProgress, 100);
      });
    }, 500);

    try {
      const response = await axios.post('http://localhost:5000/api/query', { question });
      setQueryResult(response.data);
      setResult(response.data.result);
      setQuestion(''); // Clear input after successful submission
    } catch (error) {
      console.error('Error fetching data:', error);
      setError('An error occurred. Please try again.'); // Display error message to the user
    } finally {
      setLoading(false);
      clearInterval(interval);
    }
  };

  useEffect(() => {
    if (loading) {
      const messageInterval = setInterval(() => {
        setMessage(getRandomMessage());
      }, 5000);
      return () => clearInterval(messageInterval);
    }
  }, [loading]);

  return (
    <div className='container'>
      <form className="form" onSubmit={handleSubmit}>
        <h1 className="title">Language Model For Database Access</h1>
        <input
          type="text"
          placeholder="Enter your question"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          className="input-text"
        />
        <button type="submit" className="btn-submit" disabled={loading}>
          {loading ? 'Loading...' : 'Submit'}
        </button>
      </form>
      {error && <div className="error">{error}</div>}
      {loading && (
        <div className="loader-container">
          <div className="progress-bar">
            <div className="progress" style={{ width: `${progress}%` }}></div>
          </div>
          <div className="loader-message">{message}</div>
        </div>
      )}
      {result && (
        <div className="result">
          <h2>Result:</h2>
          <p>Query: {result.query}</p>
          <p>Ans: {result.result}</p>
        </div>
      )}
    </div>
  );
};

export default QuestionForm;
