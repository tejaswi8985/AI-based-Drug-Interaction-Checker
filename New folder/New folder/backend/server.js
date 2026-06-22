const express = require("express");
const mongoose = require("mongoose");
const cors = require("cors");

const app = express();

app.use(cors());
app.use(express.json());

mongoose.connect("mongodb://127.0.0.1:27017/userDB")
    .then(() => console.log("MongoDB Connected"))
    .catch(err => console.log(err));

const userSchema = new mongoose.Schema({
    name: String,
    dob: String,
    gender: String,
    phone: String,
    email: String,
    password: String,

    diseases: String,
    medications: String,
    supplements: String, // 🔥 ADD
    allergies: String,

    lifestyle: String,
    diet: String,

    height: String,
    weight: String,
    bp: String,
    sugar: String,

    interactionResult: Object, // 🔥 ADD

    searchHistory: {
        type: [String],
        default: []
    }

}, { timestamps: true });
const User = mongoose.model("User", userSchema);

// SIGNUP
const axios = require("axios");

app.post("/api/signup", async (req, res) => {
    try {
        const {
            name,
            dob,
            gender,
            phone,
            email,
            password,
            diseases,
            medications,
            supplements, // 🔥 ADD THIS FIELD
            allergies,
            lifestyle,
            diet,
            height,
            weight,
            bp,
            sugar
        } = req.body;

        // ✅ Validation
        if (!name || !dob || !gender || !phone || !email) {
            return res.status(400).json({ message: "Missing required fields" });
        }

        // ✅ Check existing user
        const existingUser = await User.findOne({ email });
        if (existingUser) {
            return res.status(400).json({ message: "User already exists" });
        }

        // =========================
        // 🔥 CALL PYTHON (IMPORTANT)
        // =========================
        let interactionData = {};

        try {
            const drugs = medications ? medications.split(",") : [];
            const supps = supplements ? supplements.split(",") : [];

            const pythonRes = await axios.post(
                "http://localhost:5002/api/registration-interactions",
                {
                    drugs,
                    supplements: supps
                }
            );

            interactionData = pythonRes.data;

        } catch (err) {
            console.error("Python API error:", err.message);
        }

        // =========================
        // ✅ SAVE USER (WITH RESULT)
        // =========================
        const newUser = new User({
            name,
            dob,
            gender,
            phone,
            email,
            password,
            diseases,
            medications,
            supplements, // 🔥 SAVE THIS
            allergies,
            lifestyle,
            diet,
            height,
            weight,
            bp,
            sugar,
            interactionResult: interactionData // 🔥 OPTIONAL STORE
        });

        await newUser.save();

        // =========================
        // ✅ RESPONSE
        // =========================
        res.status(201).json({
            message: "User created successfully",
            user: newUser,
            interactions: interactionData
        });

    } catch (error) {
        console.error("Signup error:", error);
        res.status(500).json({ message: "Server error" });
    }
});
// LOGIN
app.post("/api/login", async (req, res) => {
    try {
        const { email, password } = req.body;

        const user = await User.findOne({ email });

        if (!user) return res.status(400).json({ message: "User not found" });
        if (user.password !== password) return res.status(400).json({ message: "Wrong password" });

        res.json({ message: "Login success", email: user.email });

    } catch (error) {
        console.error("Login error:", error);
        res.status(500).json({ message: "Server error" });
    }
});

// SAVE SEARCH HISTORY
app.post("/api/save-search", async (req, res) => {
    try {
        const { email, query } = req.body;

        if (!email || !query) {
            return res.status(400).json({ message: "Email and query required" });
        }

        const user = await User.findOne({ email });
        if (!user) return res.status(404).json({ message: "User not found" });

        let history = user.searchHistory || [];
        history = history.filter(q => q !== query);  // remove duplicate
        history.unshift(query);                       // add to front
        history = history.slice(0, 3);               // keep last 3

        user.searchHistory = history;
        await user.save();

        console.log("History saved:", user.searchHistory);

        res.json({ history: user.searchHistory });

    } catch (error) {
        console.error("Save search error:", error);
        res.status(500).json({ message: "Server error" });
    }
});

// GET USER PROFILE (without password)
app.get("/api/user/:email", async (req, res) => {
    try {
        const { email } = req.params;

        const user = await User.findOne({ email }).select("-password");

        if (!user) {
            return res.status(404).json({ message: "User not found" });
        }

        res.json(user);

    } catch (error) {
        console.error("Get user error:", error);
        res.status(500).json({ message: "Server error" });
    }
});

// GET HISTORY
app.get("/api/history/:email", async (req, res) => {
    try {
        const { email } = req.params;

        const user = await User.findOne({ email });
        if (!user) return res.status(404).json({ message: "User not found" });

        res.json({ history: user.searchHistory || [] });

    } catch (error) {
        console.error("Get history error:", error);
        res.status(500).json({ message: "Server error" });
    }
});


app.listen(5001, () => {
    console.log("Node.js server running on port 5001");
});