import React, { useState } from 'react';
import QuestionForm from './components/QuestionForm';
import './App.css'; // Add CSS styles here

const App = () => {
  const [queryResult, setQueryResult] = useState(null);

  return (
    <div className="App">
      <QuestionForm setQueryResult={setQueryResult} />
    </div>
  );
};

export default App;
