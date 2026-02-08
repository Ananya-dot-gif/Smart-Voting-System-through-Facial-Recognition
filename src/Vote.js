import React, { useEffect, useState } from "react";
import { useNavigate, useLocation } from "react-router-dom";

function Vote() {
  const [candidates, setCandidates] = useState([]);
  const [selectedCandidate, setSelectedCandidate] = useState("");
  const [loading, setLoading] = useState(false);

  const location = useLocation();
  const navigate = useNavigate();
  const usn = location.state?.usn;
  const voterName = location.state?.name;



  // 🔊 TEXT-TO-SPEECH FUNCTION
  const speak = (text) => {
    const msg = new SpeechSynthesisUtterance(text);
    msg.lang = "en-US";
    window.speechSynthesis.speak(msg);
  };

  // Fetch candidates
  useEffect(() => {
    if (!usn) {
      alert("❌ Unauthorized access! Please login again.");
      navigate("/login");
      return;
    }

    // 🔊 Announce voter name
    speak(`Welcome ${voterName}. Please cast your vote.`);




    fetch("http://localhost:5000/candidates")
      .then((res) => res.json())
      .then((data) => setCandidates(data))
      .catch((err) => console.error("Error fetching:", err));
  }, [usn, navigate]);

  const submitVote = async () => {
    if (!selectedCandidate) {
      alert("⚠️ Please select a subject.");
      return;
    }

    setLoading(true);

    try {
      const res = await fetch("http://localhost:5000/vote", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          usn: usn,
          candidate_id: selectedCandidate,
        }),
      });

      const data = await res.json();

      if (res.ok && data.success) {
        // 🔊 Speak after successful vote
        speak(`Thank you ${voterName}. Your vote has been recorded successfully.`);



        alert("🗳️ Your vote has been recorded!");
        navigate("/results");
      } else {
        alert("❌ " + (data.error || "Unknown error"));
      }
    } catch (err) {
      alert("⚠️ Server error.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      style={{
        width: "100vw",
        minHeight: "100vh",
        textAlign: "center",
        background: "linear-gradient(to right, #74ebd5, #ACB6E5)",
        padding: "20px",
      }}
    >
      <h1>🗳️ Cast Your Vote</h1>
      <h3>
        Logged in as: <b>{usn}</b>
      </h3>

      {/* ONE SINGLE HORIZONTAL ROW */}
      <div
        style={{
          display: "flex",
          flexDirection: "row",
          flexWrap: "nowrap",
          overflowX: "auto",
          gap: "25px",
          marginTop: "30px",
          padding: "10px",
          width: "100%",
        }}
      >
        {candidates.map((c) => (
          <div
            key={c._id}
            style={{
              minWidth: "220px",
              background: selectedCandidate === c._id ? "#ffeaa7" : "#fff",
              border:
                selectedCandidate === c._id
                  ? "3px solid #ff7f50"
                  : "2px solid #0984e3",
              borderRadius: "12px",
              padding: "15px",
              textAlign: "center",
              cursor: "pointer",
              boxShadow: "0 4px 10px rgba(0,0,0,0.1)",
            }}
            onClick={() => setSelectedCandidate(c._id)}
          >
            <img
              src={c.symbol}
              alt={c.name}
              style={{
                width: "100%",
                height: "150px",
                objectFit: "contain",
                marginBottom: "10px",
              }}
            />
            <h3>{c.name}</h3>

            <input
              type="radio"
              name="candidate"
              checked={selectedCandidate === c._id}
              onChange={() => setSelectedCandidate(c._id)}
            />
          </div>
        ))}
      </div>

      <button
        onClick={submitVote}
        disabled={loading}
        style={{
          marginTop: "40px",
          padding: "12px 28px",
          background: loading ? "#777" : "#0984e3",
          color: "white",
          border: "none",
          borderRadius: "10px",
          fontSize: "17px",
          cursor: loading ? "not-allowed" : "pointer",
        }}
      >
        {loading ? "Submitting..." : "Submit Vote"}
      </button>
    </div>
  );
}

export default Vote;
