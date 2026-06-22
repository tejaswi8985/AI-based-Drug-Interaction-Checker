import { useState } from "react";
import { useNavigate } from "react-router-dom";
import bg from '../assets/bg-1.png';
import person from '../assets/person.png';
import '../App.css';

function Signup() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);

  const [formData, setFormData] = useState({
    name: "",
    dob: "",
    gender: "",
    phone: "",
    email: "",
    password: "",
    diseases: "",
    medications: "",
    allergies: "",
    lifestyle: "",
    diet: "",
    height: "",
    weight: "",
    bp: "",
    sugar: "",
    supplements: ""
  });

  const handleChange = (e: any) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  const signUp = async () => {
    const { name, dob, gender, phone, email, password } = formData;

    if (!name || !dob || !gender || !phone || !email || !password) {
      alert("Fill required fields");
      return;
    }

    setLoading(true);

    try {
      const res = await fetch("http://localhost:5001/api/signup", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify(formData)
      });

      const data = await res.json();

      if (res.ok) {
        // Show interaction warning if any were found during registration
        const interactions = data.interactions?.interactions ?? [];
        if (interactions.length > 0) {
          const warnings = interactions
            .map((i: any) => `• ${i.ayurvedic_name} + ${i.allopathic_drug_name}: ${i.interaction_severity?.toUpperCase()} — ${i.recommendation}`)
            .join("\n");
          alert(`Signup successful!\n\n⚠ Drug Interactions Found:\n${warnings}\n\nThis info will be saved in your profile.`);
        } else {
          alert("Signup successful! No drug interactions found.");
        }
        navigate("/");
      } else {
        alert(data.message);
      }

    } catch (err) {
      console.error(err);
      alert("Server error. Make sure all servers are running.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <section
      className='column image w-screen h-screen overflow-y-auto item-center justify-start py-8'
      style={{ backgroundImage: `url(${bg})` }}
    >

      <form className='bg-white w-32 p-9 column g-5 r-1 relative mt-6'>

        {/* PROFILE */}
        <div className="w-100p row justify-center">
          <div
            className='w-6 h-6 circle image border absolute profile'
            style={{ backgroundImage: `url(${person})` }}
          />
        </div>

        {/* HEADER */}
        <div className='column g-3 text-center'>
          <h2>Health Registration</h2>
          <p>Enter your health details</p>
        </div>

        {/* MAIN 2 COLUMN */}
        <div className="row g-5 item-stretch">

          {/* LEFT COLUMN */}
          <div className="column g-4 w-50p h-full justify-between">

            <div className="column g-4">

              <div className="column g-2">
                <h4>Basic Information</h4>

                <input className='w-100p h-2.5 p-2 r-1 border'
                  name="name" placeholder='Full Name' onChange={handleChange} />

                <input className='w-100p h-2.5 p-2 r-1 border'
                  type="date" name="dob" onChange={handleChange} />

                <select className='w-100p h-2.5 p-2 r-1 border'
                  name="gender" onChange={handleChange}>
                  <option value="">Gender</option>
                  <option>Male</option>
                  <option>Female</option>
                  <option>Other</option>
                </select>

                <input className='w-100p h-2.5 p-2 r-1 border'
                  name="phone" placeholder='Phone' onChange={handleChange} />

                <input className='w-100p h-2.5 p-2 r-1 border'
                  name="email" placeholder='Email' onChange={handleChange} />

                <input className='w-100p h-2.5 p-2 r-1 border'
                  type="password"
                  name="password"
                  placeholder='Password'
                  onChange={handleChange} />
              </div>

              <div className="column g-2">
                <h4>Medications</h4>
                <input className='w-100p h-2.5 p-2 r-1 border'
                  name="medications"
                  placeholder='e.g. warfarin, aspirin (comma separated)'
                  onChange={handleChange} />
              </div>

              <div className="column g-2">
                <h4>Allergies</h4>
                <input className='w-100p h-2.5 p-2 r-1 border'
                  name="allergies"
                  placeholder='Drug / Food / Dust'
                  onChange={handleChange} />
              </div>

            </div>

            <div className="column g-2">
              <h4>Supplements <span style={{ fontWeight: "normal", fontSize: "12px", color: "#888" }}>(Ayurvedic herbs)</span></h4>
              <input className='w-100p h-2.5 p-2 r-1 border'
                name="supplements"
                placeholder='e.g. amalaki, ashwagandha (comma separated)'
                onChange={handleChange} />
            </div>

          </div>

          {/* RIGHT COLUMN */}
          <div className="column g-4 w-50p h-full justify-between">

            <div className="column g-4">

              <div className="column g-2">
                <h4>Health Profile</h4>
                <input className='w-100p h-2.5 p-2 r-1 border'
                  name="diseases"
                  placeholder='Diabetes, BP, Asthma...'
                  onChange={handleChange} />
              </div>

              <div className="column g-2">
                <h4>Lifestyle</h4>

                <input className='w-100p h-2.5 p-2 r-1 border'
                  name="lifestyle"
                  placeholder='Alcohol / Smoking'
                  onChange={handleChange} />

                <input className='w-100p h-2.5 p-2 r-1 border'
                  name="diet"
                  placeholder='Veg / Non-Veg / Diet'
                  onChange={handleChange} />
              </div>

            </div>

            <div className="column g-2">
              <h4>Vitals</h4>
              <input className='w-100p h-2.5 p-2 r-1 border' type="number" name="height" placeholder='Height (Meter)' onChange={handleChange} />
              <input className='w-100p h-2.5 p-2 r-1 border' type="number" name="weight" placeholder='Weight (Kgs)' onChange={handleChange} />
              <input className='w-100p h-2.5 p-2 r-1 border' type="number" name="bp" placeholder='Blood Pressure (mm)' onChange={handleChange} />
              <input className='w-100p h-2.5 p-2 r-1 border' name="sugar" placeholder='Blood Sugar (mg)' onChange={handleChange} />
            </div>

          </div>

        </div>

        <button
          type="button"
          className="w-100p p-3 r-1 border-none bg-primary text-white pointer"
          onClick={signUp}
          disabled={loading}
          style={{ opacity: loading ? 0.7 : 1 }}
        >
          {loading ? "⏳ Checking drug interactions..." : "SUBMIT"}
        </button>

        {loading && (
          <p style={{ textAlign: "center", color: "#888", fontSize: "13px" }}>
            Analyzing your medications and supplements for interactions. This may take a few seconds...
          </p>
        )}

        <div className='text-center'>
          <p>Already registered?{" "}
            <span
              className="pointer text-primary"
              onClick={() => navigate("/")}>
              <b>Go to Login</b>
            </span>
          </p>
        </div>

      </form>
    </section>
  );
}

export default Signup;