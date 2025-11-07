import React, { useState } from "react";

function CodeExecutor() {
  const [code, setCode] = useState("");
  const [output, setOutput] = useState("");

  const handleRun = () => {
    if (!code.trim()) {
      setOutput("Please enter some code!");
      return;
    }
    setOutput("Running your code...\n\n✅ Output: Hello World!");
  };

  return (
    <div className="page">
      <h2>Code Executor ⚙️</h2>
      <textarea
        value={code}
        onChange={(e) => setCode(e.target.value)}
        placeholder="Write your code here..."
        rows={10}
        cols={60}
      />
      <br />
      <button onClick={handleRun}>Run</button>
      <pre>{output}</pre>
    </div>
  );
}

export default CodeExecutor;
