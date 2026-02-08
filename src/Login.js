// src/pages/Login.js
import React, { useRef, useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";

function Login() {
  const videoRef = useRef(null);
  const navigate = useNavigate();

  const [usn, setUsn] = useState("");
  const [password, setPassword] = useState("");
  const [cameraActive, setCameraActive] = useState(false);
  const [capturedImage, setCapturedImage] = useState("");
  const [captchaUrl, setCaptchaUrl] = useState("");
  const [captchaInput, setCaptchaInput] = useState("");

  // Fetch CAPTCHA
  const fetchCaptcha = () => {
    setCaptchaUrl(`http://localhost:5000/captcha?cb=${Date.now()}`);
  };

  useEffect(() => {
    fetchCaptcha();
  }, []);

  // Start webcam
  const startCamera = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: true });
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        setCameraActive(true);
      }
    } catch (err) {
      console.error("Webcam error:", err);
      alert("⚠️ Could not access the camera.");
    }
  };

  // Capture image from webcam
  const capturePhoto = () => {
    if (!videoRef.current) return null;

    const canvas = document.createElement("canvas");
    canvas.width = videoRef.current.videoWidth || 640;
    canvas.height = videoRef.current.videoHeight || 480;

    const ctx = canvas.getContext("2d");
    ctx.drawImage(videoRef.current, 0, 0, canvas.width, canvas.height);

    const base64 = canvas.toDataURL("image/jpeg");
    setCapturedImage(base64);
    return base64;
  };

  // Handle Login
  const handleLogin = async (e) => {
    e.preventDefault();

    if (!usn || !password || !captchaInput) {
      alert("⚠️ Fill USN, Password & CAPTCHA.");
      return;
    }

    if (!cameraActive) {
      alert("⚠️ Please start the camera first.");
      return;
    }

    const photoBase64 = capturePhoto();
    if (!photoBase64) {
      alert("⚠️ Failed to capture face.");
      return;
    }

    try {
      const res = await fetch("http://localhost:5000/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({
          usn: usn.trim().toUpperCase(),
          password,
          image: photoBase64,
          captcha_input: captchaInput.trim().toUpperCase(),
        }),
      });

      const data = await res.json();

      if (res.ok && data.status === "login success") {
        alert("✅ Login Successful!");
        navigate("/vote", {state: {usn: usn,name: data.name }});




      } else {
        alert("❌ " + (data.error || "Login Failed"));
        fetchCaptcha();
        setCaptchaInput("");
      }
    } catch (err) {
      console.error("Login error:", err);
      alert("⚠️ Server error. Try again.");
    }
  };

  return (
    <div className="flag">
      <div className="band saffron"></div>

      <div className="band white">
        <div className="flag-card">
          <img src="/chakra.png" alt="Ashoka Chakra" className="chakra" />
          <h2>Login</h2>

          <form onSubmit={handleLogin}>
            {/* USN Input */}
            <input
              className="flag-input"
              type="text"
              placeholder="Enter USN"
              value={usn}
              onChange={(e) => setUsn(e.target.value.toUpperCase())}
              required
            />

            {/* Password Input */}
            <input
              className="flag-input"
              type="password"
              placeholder="Enter Password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />

            {/* CAPTCHA */}
            <div style={{ margin: "10px 0", textAlign: "center" }}>
              {captchaUrl && (
                <>
                  <img
                    src={captchaUrl}
                    alt="CAPTCHA"
                    onClick={fetchCaptcha}
                    style={{
                      width: "320px",
                      height: "120px",
                      borderRadius: "8px",
                      cursor: "pointer",
                      border: "2px solid #ddd",
                      objectFit: "contain",
                    }}
                    title="Click to refresh CAPTCHA"
                  />
                  <div style={{ fontSize: "13px", color: "#777" }}>
                    🔄 Click CAPTCHA to refresh
                  </div>
                </>
              )}
            </div>

            <input
              className="flag-input"
              type="text"
              placeholder="Enter CAPTCHA"
              value={captchaInput}
              onChange={(e) => setCaptchaInput(e.target.value.toUpperCase())}
              required
            />

            {/* Webcam */}
            <video
              ref={videoRef}
              autoPlay
              playsInline
              style={{
                width: "100%",
                borderRadius: "8px",
                marginBottom: "12px",
                backgroundColor: "black",
              }}
            />

            <button
              type="button"
              className="flag-btn"
              onClick={startCamera}
              disabled={cameraActive}
            >
              {cameraActive ? "Camera Active" : "Start Camera"}
            </button>

            <button type="submit" className="flag-btn">
              Login
            </button>
          </form>

          {/* Image Preview */}
          {capturedImage && (
            <div style={{ marginTop: "15px", textAlign: "center" }}>
              <h4>Captured Image:</h4>
              <img
                src={capturedImage}
                alt="Captured"
                style={{ width: "200px", borderRadius: "6px", marginTop: "8px" }}
              />
            </div>
          )}
        </div>
      </div>

      <div className="band green"></div>
    </div>
  );
}

export default Login;
