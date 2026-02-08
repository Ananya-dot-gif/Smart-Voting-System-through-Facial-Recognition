// src/pages/Register.js
import React, { useRef, useState, useEffect } from "react";

function Register() {
  const videoRef = useRef(null);
  const streamRef = useRef(null);

  // Step tracking
  const [currentStep, setCurrentStep] = useState(1);

  // Form fields
  const [usn, setUsn] = useState("");
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [password, setPassword] = useState("");

  // Webcam & image state
  const [cameraStarted, setCameraStarted] = useState(false);
  const [capturedImage, setCapturedImage] = useState(null);

  // Stop camera on exit
  useEffect(() => {
    return () => stopCamera();
  }, []);

  const stopCamera = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
    }
    setCameraStarted(false);
  };

  // Start Webcam
  const startCamera = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: true });
      streamRef.current = stream;
      if (videoRef.current) videoRef.current.srcObject = stream;
      setCameraStarted(true);
    } catch (err) {
      console.error("Camera access error:", err);
      alert("⚠️ Unable to access camera. Check your permissions.");
    }
  };

  // Capture face image (Base64)
  const capturePhoto = () => {
    if (!cameraStarted || !videoRef.current) {
      alert("⚠️ Please start the camera before capturing.");
      return;
    }

    const canvas = document.createElement("canvas");
    canvas.width = videoRef.current.videoWidth || 640;
    canvas.height = videoRef.current.videoHeight || 480;
    canvas.getContext("2d").drawImage(videoRef.current, 0, 0);

    const photo = canvas.toDataURL("image/jpeg", 0.9);
    setCapturedImage(photo);
    return photo;
  };

  // Validation
  const validatePhone = (num) => /^[0-9]{10}$/.test(num);
  const validateEmail = (mail) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(mail);
  const validateUSN = (text) => /^[A-Za-z0-9]+$/.test(text) && text.length >= 5;

  // Proceed to face capture
  const handleNextStep = () => {
    if (!usn || !name || !email || !phone || !password) {
      alert("⚠️ Please fill in all required fields.");
      return;
    }
    if (!validateUSN(usn)) {
      alert("⚠️ Invalid USN format.");
      return;
    }
    if (!validateEmail(email)) {
      alert("⚠️ Invalid email format.");
      return;
    }
    if (!validatePhone(phone)) {
      alert("⚠️ Phone number must be exactly 10 digits.");
      return;
    }

    setCurrentStep(2);
  };

  // Submit registration
  const handleRegister = async (e) => {
    e.preventDefault();

    const photoBase64 = capturePhoto();
    if (!photoBase64) return;

    try {
      const res = await fetch("http://localhost:5000/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ usn, name, email, phone, password, image: photoBase64 }),
      });

      const data = await res.json();

      if (res.ok && data.status === "registered") {
        alert("🎉 Registration successful!");
        stopCamera();

        setUsn("");
        setName("");
        setEmail("");
        setPhone("");
        setPassword("");
        setCapturedImage(null);
        setCurrentStep(1);
      } else {
        alert("❌ " + (data.error || "Registration failed. Try again."));
      }
    } catch (err) {
      console.error("Registration Error:", err);
      alert("⚠️ Server error. Try again later.");
    }
  };

  return (
    <div className="flag">
      <div className="band saffron"></div>

      <div className="band white">
        <div className="flag-card">
          <img src="/chakra.png" alt="Ashoka Chakra" className="chakra" />
          <h2>Register</h2>

          <form onSubmit={handleRegister}>

            {/* ---------------------- STEP 1 ---------------------- */}
            {currentStep === 1 && (
              <>
                <input
                  className="flag-input"
                  type="text"
                  placeholder="Enter USN"
                  value={usn}
                  onChange={(e) => setUsn(e.target.value.toUpperCase())}
                  required
                />

                <input
                  className="flag-input"
                  type="text"
                  placeholder="Enter Full Name"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  required
                />

                <input
                  className="flag-input"
                  type="email"
                  placeholder="Enter Email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                />

                <input
                  className="flag-input"
                  type="tel"
                  placeholder="Enter 10-digit Phone"
                  value={phone}
                  onChange={(e) => setPhone(e.target.value)}
                  maxLength="10"
                  required
                />

                <input
                  className="flag-input"
                  type="password"
                  placeholder="Enter Password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                />

                <button type="button" className="flag-btn" onClick={handleNextStep}>
                  Next
                </button>
              </>
            )}

            {/* ---------------------- STEP 2 ---------------------- */}
            {currentStep === 2 && (
              <>
                <video
                  ref={videoRef}
                  autoPlay
                  playsInline
                  style={{
                    width: "100%",
                    borderRadius: "10px",
                    backgroundColor: "#000",
                    marginBottom: "12px",
                  }}
                />

                {capturedImage && (
                  <img
                    src={capturedImage}
                    alt="Captured"
                    style={{
                      width: "100%",
                      borderRadius: "10px",
                      border: "2px solid #007bff",
                      marginBottom: "12px",
                    }}
                  />
                )}

                <div style={{ display: "flex", gap: "10px", flexWrap: "wrap" }}>
                  <button
                    type="button"
                    className="flag-btn"
                    onClick={startCamera}
                    disabled={cameraStarted}
                  >
                    {cameraStarted ? "Camera Running" : "Start Camera"}
                  </button>

                  <button
                    type="button"
                    className="flag-btn"
                    onClick={capturePhoto}
                    disabled={!cameraStarted}
                  >
                    Capture Face
                  </button>

                  <button
                    type="submit"
                    className="flag-btn"
                    disabled={!capturedImage}
                  >
                    {capturedImage ? "Register" : "Capture Face First"}
                  </button>

                  <button
                    type="button"
                    className="flag-btn"
                    onClick={() => {
                      stopCamera();
                      setCapturedImage(null);
                      setCurrentStep(1);
                    }}
                  >
                    Back
                  </button>
                </div>
              </>
            )}
          </form>
        </div>
      </div>

      <div className="band green"></div>
    </div>
  );
}

export default Register;
