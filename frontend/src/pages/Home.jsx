import React from "react";
import ResultCard from "../components/ResultCard";

function Home() {
  return (
    <div className="container">
      <h1>Welcome to InstaGrade 🎓</h1>
      <p>
        This platform helps instructors grade assignments and check for code plagiarism.
      </p>
      <ResultCard
        title="Code Execution"
        description="Run and evaluate your students’ code automatically."
      />
      <ResultCard
        title="Plagiarism Detection"
        description="Instantly find similarities between student submissions."
      />
    </div>
  );
}

export default Home;
