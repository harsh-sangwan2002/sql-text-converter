import React, { useState } from 'react';
import axios from 'axios';

const QuestionForm = ({ setQueryResult }) => {
  const [question, setQuestion] = useState('');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const response = await axios.post('http://localhost:5000/api/query', { question });
      setQueryResult(response);
      setResult(response.data.result);
      setQuestion(''); // Clear input after successful submission
    } catch (error) {
      console.error('Error fetching data:', error);
      setError('An error occurred. Please try again.'); // Display error message to the user
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className='container'>
      <form className="form" onSubmit={handleSubmit}>
        <h1>Language Model For Database Access</h1>
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
          <div className="loader"></div>
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
