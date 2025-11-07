import React, { useState } from "react";

function PlagiarismChecker() {
  const [text1, setText1] = useState("");
  const [text2, setText2] = useState("");
  const [similarity, setSimilarity] = useState(null);

  const handleCheck = () => {
    if (!text1.trim() || !text2.trim()) {
      setSimilarity("Please paste both texts!");
      return;
    }

    // Fake similarity for demo
    const similarityScore = Math.floor(Math.random() * 100);
    setSimilarity(`Similarity Score: ${similarityScore}%`);
  };

  return (
    <div className="page">
      <h2>Plagiarism Checker 🧠</h2>
      <textarea
        placeholder="Paste first code/text here..."
        rows={6}
        cols={50}
        value={text1}
        onChange={(e) => setText1(e.target.value)}
      />
      <br />
      <textarea
        placeholder="Paste second code/text here..."
        rows={6}
        cols={50}
        value={text2}
        onChange={(e) => setText2(e.target.value)}
      />
      <br />
      <button onClick={handleCheck}>Check Similarity</button>
      {similarity && <p className="result">{similarity}</p>}
    </div>
  );
}

export default PlagiarismChecker;
